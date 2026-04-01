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
        
    def get_all_match_ids(self, puuid: str) -> List[str]:
        """
        Paginates through the Riot API to collect all match IDs for a player.
        """
        all_match_ids = []
        start = 0
        count = 100  # Riot's maximum allowed count per request
        
        logger.info(f"Fetching all match IDs for PUUID: {puuid}")
        
        while True:
            # The make_api_request will handle rate limits locally and from the headers
            match_ids = make_api_request(
                "match_list", 
                puuid=puuid, 
                start=start, 
                count=count
            )
            
            # Break if nothing is returned or we encounter an API issue
            if not match_ids:
                break
                
            all_match_ids.extend(match_ids)
            
            # If the API returned fewer matches than requested, it's the end of their history
            if len(match_ids) < count:
                break
                
            start += count
            
        logger.info(f"Total match IDs retrieved: {len(all_match_ids)}")
        return all_match_ids

    def get_match_detail(self, match_id: str) -> Optional[dict]:
        """
        Retrieves a single match details document.
        Checks the local SQLite Database first using DatabaseManager before querying the Riot API.
        """
        # 1. Look up up the JSON dynamically in the SQLite Cache 
        cached_match = self.db.get_json(match_id)
        if cached_match:
            logger.debug(f"Loaded match {match_id} from DB.")
            return cached_match
            
        # 2. Not in local database, perform the network request
        logger.debug(f"Fetching match {match_id} from Riot API.")
        match_data = make_api_request("match_detail", matchId=match_id)
        
        # 3. Permanently store the fully resolved JSON to the database for future executions
        if match_data and "metadata" in match_data and "info" in match_data:
            self.db.store_json(match_id, match_data)
            return match_data
            
        return None

    def sync_player_history(self, puuid: str) -> List[dict]:
        """
        Retrieves all match IDs for a player, then retrieves detailed match info for each,
        utilizing caching to drastically speed up repetitive script executions.
        """
        match_ids = self.get_all_match_ids(puuid)
        full_history = []
        
        logger.info(f"Syncing {len(match_ids)} detailed matches for PUUID: {puuid}")
        
        for idx, match_id in enumerate(match_ids):
            # The Riot API limit handles automatically if we do hundreds, although it'll block while it waits 
            match_data = self.get_match_detail(match_id)
            if match_data:
                full_history.append(match_data)
                
            if (idx + 1) % 50 == 0:
                logger.info(f"Progress: Synced {idx + 1}/{len(match_ids)} matches...")
                
        logger.info(f"Finished. Extracted {len(full_history)} total rich match objects.")
        return full_history
