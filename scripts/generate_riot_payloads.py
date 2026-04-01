import json
import os
import sys

# Add root repo directory to context so it can run either from root or from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.api_riot import make_api_request

# Using the data from your verified successful request
GAME_NAME = "peusswor"
TAG_LINE = "EUW"
PUUID = "0Vj7SIBGQCAPDuDr_eYeAiUbDvDgCJNG69RQRhjCChICI-NqxqRHNk-43J7uO6c7PVmq4Ak4vuhAOA"
MATCH_ID = "EUW1_7806811562"
CHAMPION_ID = 1  # Annie as dummy test

def run_riot_tests():
    base_dir = os.path.join("payload_examples", "riot")
    
    # Format: (Category, Endpoint Name, Kwargs)
    endpoints_to_test = [
        ("account", "puuid", {"gameName": GAME_NAME, "tagLine": TAG_LINE}),
        ("account", "account", {"puuid": PUUID}),
        
        ("summoner", "summoner", {"puuid": PUUID}),
        
        ("spectator", "active_game", {"puuid": PUUID}),
        
        ("league", "player_data", {"puuid": PUUID}),
        
        ("champion_mastery", "champion_mastery", {"puuid": PUUID}),
        ("champion_mastery", "champion_mastery_by_champ", {"puuid": PUUID, "championId": CHAMPION_ID}),
        
        ("match", "match_list", {"puuid": PUUID, "count": 2}),
        ("match", "match_detail", {"matchId": MATCH_ID}),
        ("match", "match_timeline", {"matchId": MATCH_ID}),
    ]
    
    print(f"Generating organized Riot JSON payloads into '{base_dir}/'...")
    
    for category, endpoint, kwargs in endpoints_to_test:
        print(f"  -> Testing: {category}/{endpoint}")
        try:
            data = make_api_request(endpoint, **kwargs)
            if data:
                # Create category folder specifically
                category_dir = os.path.join(base_dir, category)
                os.makedirs(category_dir, exist_ok=True)
                
                # Save to domain-specific folder
                file_path = os.path.join(category_dir, f"{endpoint}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                print(f"      [SAVED] {file_path}")
            else:
                print(f"      [SKIPPED] No data returned (likely 404 Expected)")
        except Exception as e:
            print(f"      [ERROR] Exception: {e}")
            
    print(f"\n✅ Successfully generated properly organized Riot examples!")

if __name__ == "__main__":
    run_riot_tests()
