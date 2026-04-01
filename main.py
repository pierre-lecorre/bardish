import sys
import logging

# Set up basic logging so we can see what the fetcher is doing
logging.basicConfig(level=logging.INFO, format='%(message)s')

from core.api_riot import make_api_request
from core.player import PlayerHistoryFetcher

def main():
    game_name = "peusswor"
    tag_line = "EUW"
    
    print(f"Looking up player: {game_name}#{tag_line}...")
    
    # 1. Fetch PUUID from gameName and tagLine
    account_data = make_api_request("puuid", gameName=game_name, tagLine=tag_line)
    
    if not account_data or 'puuid' not in account_data:
        print("Failed to find player account.")
        sys.exit(1)
        
    puuid = account_data['puuid']
    print(f"Successfully retrieved PUUID: {puuid}\n")
    
    # 2. Instantiate our fetcher class which uses the DatabaseManager automatically
    fetcher = PlayerHistoryFetcher()
    
    # 3. Use sync_player_history to exhaustively paginate their ENTIRE history.
    # It will use ETA predictions and cache everything dynamically into 'app_data.db'.
    full_match_history = fetcher.sync_player_history(puuid)
    
    print("\n--- DONE ---")
    print(f"Stored {len(full_match_history)} comprehensive match objects into the local SQLite database!")
    
if __name__ == "__main__":
    main()
