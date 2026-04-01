import logging
from typing import List, Optional

from core.api_riot import make_api_request
from core.database import DatabaseManager

logger = logging.getLogger(__name__)

class PlayerHistoryFetcher:
    """
    A utility class to aggregate and manage a player's entire match history,
    leveraging a local SQLite database to prevent redundant API queries.
    """
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize with an optional custom DatabaseManager.
        If None is provided, it instantiates its own to store match documents.
        """
        self.db = db_manager or DatabaseManager()
        
    def sync_match_ids(self, puuid: str, limit: Optional[int] = None) -> List[str]:
        """
        Paginates through Riot's API to collect match IDs for a player.
        If limit is None, fetches ALL match IDs exhaustively.
        If limit is set, stops after collecting that many IDs total.
        Deduplicates against known IDs and saves to DB every 100 for crash safety.
        """
        # Load known match IDs from DB
        cached_data = self.db.get_json(puuid, table_name="matches_list")
        known_ids = cached_data if isinstance(cached_data, list) else []
        known_ids_set = set(known_ids)
        
        new_match_ids = []
        current_start = 0
        
        logger.info(f"Synchronizing match IDs for PUUID: {puuid}. Already know {len(known_ids)} matches.")
        
        while True:
            # If we have a limit, only request what we still need
            req_count = 100
            if limit is not None:
                remaining = limit - (len(new_match_ids) + len(known_ids))
                if remaining <= 0:
                    break
                req_count = min(100, remaining)
            
            match_ids = make_api_request("match_list", puuid=puuid, start=current_start, count=req_count)
            if not match_ids:
                break
            
            for m_id in match_ids:
                if m_id not in known_ids_set:
                    new_match_ids.append(m_id)
                    known_ids_set.add(m_id)
                    
            # INCREMENTAL CACHE: Save progress after every page
            if new_match_ids:
                current_combined = new_match_ids + known_ids
                self.db.store_json(puuid, current_combined, table_name="matches_list")
            
            # Riot returned fewer than requested → end of history
            if len(match_ids) < req_count:
                break
                
            current_start += 100
            
        total = len(new_match_ids) + len(known_ids)
        if new_match_ids:
            logger.info(f"Found {len(new_match_ids)} new match IDs. Total: {total}")
        else:
            logger.info(f"All {total} match IDs already up to date.")
            
        return new_match_ids + known_ids

    def get_match_detail(self, match_id: str) -> Optional[dict]:
        """
        Retrieves a single match details document.
        Checks the local SQLite Database first using DatabaseManager before querying the Riot API.
        """
        # 1. Look up up the JSON dynamically in the SQLite Cache 
        cached_match = self.db.get_json(match_id, table_name="matches")
        if cached_match:
            logger.debug(f"Loaded match {match_id} from DB.")
            return cached_match
            
        # 2. Not in local database, perform the network request
        logger.debug(f"Fetching match {match_id} from Riot API.")
        match_data = make_api_request("match_detail", matchId=match_id)
        
        # 3. Permanently store the fully resolved JSON to the database for future executions
        if match_data and "metadata" in match_data and "info" in match_data:
            self.db.store_json(match_id, match_data, table_name="matches")
            return match_data
            
        return None

    def sync_player_history(self, puuid: str, start: int = 0, limit: Optional[int] = None) -> List[dict]:
        """
        Retrieves a batch of match IDs for a player, then retrieves detailed match info for each,
        utilizing caching to drastically speed up repetitive script executions.
        """
        all_ids = self.sync_match_ids(puuid, limit=limit)
        
        if limit is not None:
            match_ids = all_ids[start:start+limit]
        else:
            match_ids = all_ids[start:]
        
        # Calculate ETA based on Riot API limits (approx ~1.25s per request via DEV key)
        pending_count = sum(1 for match_id in match_ids if not self.db.key_exists(match_id, table_name="matches"))
        cached_count = len(match_ids) - pending_count
        eta_seconds = pending_count * 1.25  
        
        logger.info(f"Syncing {len(match_ids)} matches for PUUID: {puuid}")
        if pending_count > 0:
            if eta_seconds > 60:
                logger.info(f"  -> {cached_count} already cached. Fetching {pending_count} new matches. ETA: ~{eta_seconds/60:.1f} minutes")
            else:
                logger.info(f"  -> {cached_count} already cached. Fetching {pending_count} new matches. ETA: ~{eta_seconds:.0f} seconds")
        else:
            logger.info(f"  -> All {len(match_ids)} matches optimally loaded from local cache!")
            
        full_history = []
        for idx, match_id in enumerate(match_ids):
            match_data = self.get_match_detail(match_id)
            if match_data:
                full_history.append(match_data)
                
            if (idx + 1) % 50 == 0:
                logger.info(f"Progress: Synced {idx + 1}/{len(match_ids)} matches...")
                
        logger.info(f"Finished. Extracted {len(full_history)} total rich match objects.")
        return full_history
