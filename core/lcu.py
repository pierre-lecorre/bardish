import psutil
import re
import base64
import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def find_lcu_psutil():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == 'LeagueClientUx.exe':
            cmdline = ' '.join(proc.info['cmdline'] or [])

            port_match = re.search(r'--app-port=(\d+)', cmdline)
            token_match = re.search(r'--remoting-auth-token=([^\s]+)', cmdline)

            if port_match and token_match:
                port = int(port_match.group(1))
                token = token_match.group(1)

                # ✅ LCU always uses "riot" as the username
                credentials = base64.b64encode(f"riot:{token}".encode()).decode()
                auth = {"Authorization": f"Basic {credentials}"}

                print(f"✅ LCU found: port={port}")
                return port, auth

    print("❌ LeagueClientUx.exe not running")
    return None, None


def get_lobby_data():
    port, auth = find_lcu_psutil()
    if not port:
        return None

    base_url = f"https://127.0.0.1:{port}"

    try:
        resp = requests.get(f"{base_url}/lol-gameflow/v1/session", headers=auth, verify=False, timeout=5)
        print(f"🔁 Status: {resp.status_code}")

        if resp.status_code == 404:
            print("ℹ️ Client idle (no session)")
            return {'port': port, 'phase': 'None'}

        resp.raise_for_status()
        gameflow = resp.json()
        phase = gameflow.get('phase', 'None')
        print(f"📍 Phase: {phase}")

        def dump(url):
            r = requests.get(f"{base_url}{url}", headers=auth, verify=False)
            if r.status_code == 200 and r.text.strip():
                print(json.dumps(r.json(), indent=2))
                return r.json()
            print(f"⚠️ Empty or error response for {url}: {r.status_code}")
            return None

        if phase == 'Lobby':
            data = dump('/lol-lobby/v2/lobby')
            return {'port': port, 'phase': phase, 'lobby': data}

        elif phase == 'Matchmaking':
            data = dump('/lol-matchmaking/v1/search')
            return {'port': port, 'phase': phase, 'matchmaking': data}

        elif phase == 'ReadyCheck':
            data = dump('/lol-matchmaking/v1/ready-check')
            return {'port': port, 'phase': phase, 'ready_check': data}

        elif phase == 'ChampSelect':
            data = dump('/lol-champ-select/v1/session')
            return {'port': port, 'phase': phase, 'session': data}

        elif phase == 'GameStart':
            print("🚀 Game is launching...")
            print(json.dumps(gameflow, indent=2))
            return {'port': port, 'phase': phase, 'gameflow': gameflow}

        elif phase == 'InProgress':
            data = dump('/lol-gameflow/v1/session')
            return {'port': port, 'phase': phase, 'gameflow': data}

        elif phase == 'WaitingForStats':
            print("⏳ Waiting for end-of-game stats...")
            return {'port': port, 'phase': phase}

        elif phase == 'PreEndOfGame':
            data = dump('/lol-pre-end-of-game/v1/currentSequenceEvent')
            return {'port': port, 'phase': phase, 'pre_eog': data}

        elif phase == 'EndOfGame':
            data = dump('/lol-end-of-game/v1/eog-stats-block')
            return {'port': port, 'phase': phase, 'eog': data}

        elif phase == 'Reconnect':
            print("🔄 Reconnect screen — game already in progress")
            return {'port': port, 'phase': phase}

        elif phase == 'None':
            print("🏠 On home screen")
            return {'port': port, 'phase': phase}

        else:
            print(f"❓ Unknown phase: {phase} — dumping full gameflow")
            print(json.dumps(gameflow, indent=2))
            return {'port': port, 'phase': phase, 'gameflow': gameflow}

    except Exception as e:
        print(f"❌ Error: {e}")
        return None
