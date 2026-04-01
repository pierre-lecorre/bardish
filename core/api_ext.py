import requests
from functools import lru_cache

@lru_cache(maxsize=1)
def get_latest_version():
    """Get the latest Data Dragon version."""
    return requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

def get_champ_id_map(version=None):
    """Champion ID (int) → Name via Data Dragon API"""
    if not version:
        version = get_latest_version()
    data = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json").json()['data']
    return data

def champ_id_to_name(champ_id, champ_map):
    """ID (str/int) → champion name"""
    for name, data in champ_map.items():
        if data['key'] == str(champ_id):
            return name
    return "Unknown"

def get_profile_icon_url(profile_icon_id, version=None):
    """Get the Data Dragon URL for a profile icon."""
    if not version:
        version = get_latest_version()
    return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/{profile_icon_id}.png"

def get_champion_image_url(champion_name, version=None):
    """Get the Data Dragon URL for a champion's square image.
    Be sure to pass the internal champion name (e.g., 'AurelionSol' instead of 'Aurelion Sol')."""
    if not version:
        version = get_latest_version()
    return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion_name}.png"

def get_rank_icon_url(tier):
    """Get the CDragon URL for a ranked emblem."""
    tier = tier.lower() if tier else "unranked"
    return f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-emblem/emblem-{tier}.png"

def get_mastery_icon_url():
    """Get the CDragon URL for a mastery icon."""
    return "https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/champion-mastery/icon-mastery.svg"