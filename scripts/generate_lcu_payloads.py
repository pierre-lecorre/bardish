import json
import os
import sys
import requests
import urllib3

# Add root repo directory to context so it can run either from root or from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.lcu import find_lcu_psutil

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Format: (Category, Name, Endpoint URL)
LCU_ENDPOINTS = [
    ("gameflow", "session", "/lol-gameflow/v1/session"),
    
    ("lobby", "lobby", "/lol-lobby/v2/lobby"),
    
    ("matchmaking", "search", "/lol-matchmaking/v1/search"),
    ("matchmaking", "ready_check", "/lol-matchmaking/v1/ready-check"),
    
    ("champ_select", "session", "/lol-champ-select/v1/session"),
    
    ("end_of_game", "pre_end_of_game", "/lol-pre-end-of-game/v1/currentSequenceEvent"),
    ("end_of_game", "eog_stats_block", "/lol-end-of-game/v1/eog-stats-block")
]

def run_lcu_tests():
    port, auth = find_lcu_psutil()
    if not port:
        print("Could not find LCU running. Make sure League is open locally!")
        return
        
    base_dir = os.path.join("payload_examples", "lcu")
    base_url = f"https://127.0.0.1:{port}"
    
    print(f"Generating organized LCU JSON payloads into '{base_dir}/'...")
    
    for category, name, endpoint in LCU_ENDPOINTS:
        print(f"  -> Testing: {category}/{name}")
        try:
            r = requests.get(f"{base_url}{endpoint}", headers=auth, verify=False, timeout=3)
            if r.status_code == 200 and r.text.strip():
                try:
                    content = r.json()
                except ValueError:
                    content = {"text": r.text}
            else:
                content = {"status": f"Status {r.status_code} - Likely because client phase is inactive for this endpoint."}
        except Exception as e:
            content = {"error": f"Exception: {e}"}
             
        category_dir = os.path.join(base_dir, category)
        os.makedirs(category_dir, exist_ok=True)
             
        file_path = os.path.join(category_dir, f"{name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4, ensure_ascii=False)
        
    print(f"\n✅ Successfully generated properly organized LCU examples!")

if __name__ == "__main__":
    run_lcu_tests()
