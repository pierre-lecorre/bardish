import requests
import time
import threading
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_RIOT")
server_region = os.getenv("SERVER_REGION")
server_name = os.getenv("SERVER_NAME")

headers = {"X-Riot-Token": api_key}

# Format: "endpoint_name": {"url": "...", "limits": [(max_requests, seconds), ...]}
ENDPOINTS = {
    "puuid": {
        "url": f"https://{server_region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{{gameName}}/{{tagLine}}",
        "limits": [(1000, 60)] # account-v1
    },
    "account": {
        "url": f"https://{server_region}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{{puuid}}",
        "limits": [(1000, 60)] # account-v1
    },
    "summoner": {
        "url": f"https://{server_name}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{{puuid}}",
        "limits": [(1600, 60)] # summoner-v4
    },
    "active_game": {
        "url": f"https://{server_name}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{{puuid}}",
        "limits": [(20000, 10), (1200000, 600)] # spectator-v5
    },
    "player_data": {
        "url": f"https://{server_name}.api.riotgames.com/lol/league/v4/entries/by-puuid/{{puuid}}",
        "limits": [(20000, 10), (1200000, 600)] # league-v4
    },
    "champion_mastery": {
        "url": f"https://{server_name}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{{puuid}}",
        "limits": [(20000, 10), (1200000, 600)] # champion-mastery-v4
    },
    "champion_mastery_by_champ": {
        "url": f"https://{server_name}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{{puuid}}/by-champion/{{championId}}",
        "limits": [(20000, 10), (1200000, 600)] # champion-mastery-v4
    },
    "match_list": {
        "url": f"https://{server_region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{{puuid}}/ids?start={{start}}&count={{count}}",
        "limits": [(2000, 10)] # match-v5
    },
    "match_detail": {
        "url": f"https://{server_region}.api.riotgames.com/lol/match/v5/matches/{{matchId}}",
        "limits": [(2000, 10)] # match-v5
    },
    "match_timeline": {
        "url": f"https://{server_region}.api.riotgames.com/lol/match/v5/matches/{{matchId}}/timeline",
        "limits": [(2000, 10)] # match-v5
    },
}

# The Standard App Rate Limits for Development Keys (added tiny margins for latency safety)
APP_LIMITS = [(19, 1.2), (98, 122)]

class RateLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.history = {}
        self.app_history = {limit: [] for limit in APP_LIMITS}
        self.global_penalty_until = 0.0

    def apply_penalty(self, penalty_seconds):
        with self.lock:
            penalty_time = time.time() + penalty_seconds
            if penalty_time > self.global_penalty_until:
                self.global_penalty_until = penalty_time

    def _wait_for_limit(self, history_list, max_req, period):
        now = time.time()
        # Filter out requests that are older than the period
        valid_history = [t for t in history_list if now - t < period]
        
        if len(valid_history) >= max_req:
            # Sleep until the oldest request in the window expires
            sleep_time = period - (now - valid_history[0])
            if sleep_time > 0:
                #print(f"Rate Limiter: Delaying for {sleep_time:.2f}s to respect {max_req} req / {period}s limit.")
                time.sleep(sleep_time)
                now = time.time()
                # Recalculate after waking up
                valid_history = [t for t in history_list if now - t < period]
                
        valid_history.append(now)
        return valid_history

    def acquire(self, endpoint_name, endpoint_limits):
        with self.lock:
            # 0. Check global penalty
            now = time.time()
            if now < self.global_penalty_until:
                sleep_time = self.global_penalty_until - now
                #print(f"Rate Limiter: Global penalty active. Delaying for {sleep_time:.2f}s.")
                time.sleep(sleep_time)

            # 1. Enforce Application Rate Limits (across all endpoints)
            for limit in APP_LIMITS:
                max_req, period = limit
                self.app_history[limit] = self._wait_for_limit(self.app_history[limit], max_req, period)
            
            # 2. Enforce specific Method Rate Limits (for this specific endpoint)
            if endpoint_name not in self.history:
                self.history[endpoint_name] = {limit: [] for limit in endpoint_limits}
                
            for limit in endpoint_limits:
                max_req, period = limit
                self.history[endpoint_name][limit] = self._wait_for_limit(self.history[endpoint_name][limit], max_req, period)

limiter = RateLimiter()

def make_api_request(endpoint_name, max_retries=3, **kwargs):
    if endpoint_name not in ENDPOINTS:
        raise ValueError(f"Endpoint '{endpoint_name}' not found.")
        
    endpoint_info = ENDPOINTS[endpoint_name]
    url = str(endpoint_info["url"]).format(**kwargs)
    
    for attempt in range(max_retries):
        # Prevent the user from hitting the rate limit
        limiter.acquire(endpoint_name, endpoint_info["limits"])
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2))
            print(f"Rate limited (429) by server for {url}. Retrying in {retry_after}s (Attempt {attempt+1}/{max_retries})...")
            limiter.apply_penalty(retry_after)
            time.sleep(retry_after)
        elif response.status_code == 404 and endpoint_name in ['active_game', 'champion_mastery_by_champ']:
            # 404 is expected if they are not in a game, or have no mastery on a champ
            return None
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
            
    return None
