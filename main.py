import sys
from core.api_riot import make_api_request

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
    print(f"Successfully retrieved PUUID: {puuid}")
    
    # 2. Fetch the list of match IDs
    count = 1
    print(f"Fetching up to {count} recent match IDs...")
    match_ids = make_api_request("match_list", puuid=puuid, count=count)
    
    if not match_ids:
        print("No matches found or failed to retrieve matches.")
        sys.exit(1)
        
    print(match_ids)

if __name__ == "__main__":
    main()
