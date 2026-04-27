#!/usr/bin/env python3
"""
Kalshi x ActionBets Arbitrage Scanner
Railway-ready. Set env vars AB_USERNAME and AB_PASSWORD in Railway dashboard.
"""

import os
import json
import time
import threading
import requests
from datetime import datetime
from flask import Flask, jsonify, Response

app = Flask(__name__)

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Config ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

KALSHI_BASE   = "https://api.elections.kalshi.com/trade-api/v2"
AB_BASE       = "https://actionbets.ag/cloud/api"
AB_DOMAIN     = "actionbets.ag"
KALSHI_SERIES = ["KXNBAGAME", "KXMLBGAME", "KXNFLGAME", "KXNHLTOTAL", "KXNBATOTAL", "KXMLBTOTAL"]

# Header variants to try for AB lines (ordered by most likely to work)
AB_HEADER_VARIANTS = [
    # Axios default (most modern SPAs)
    {"Accept": "application/json, text/plain, */*", "X-Requested-With": "XMLHttpRequest"},
    # jQuery AJAX default
    {"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"},
    # Axios without XHR flag
    {"Accept": "application/json, text/plain, */*"},
    # Simple JSON
    {"Accept": "application/json"},
    # Wildcard
    {"Accept": "*/*"},
    # Browser default
    {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"},
    # No Accept header
    {},
]

AB_LINES_PATHS = [
    "/Lines/GetLeagues",
    "/Lines/GetSports",
    "/Lines/GetGames",
    "/Lines/GetAllLines",
    "/Lines/GetStraightLines",
    "/Lines/GetOpenLines",
    "/Lines/GetTodayLines",
    "/Lines/GetLinesByLeague",
    "/Sport/GetLines",
    "/Provider/GetLines",
    "/Customer/GetLines",
]

TEAM_ALIASES = {
    # NBA
    "OKC": ["oklahoma city","thunder","okc"],
    "PHX": ["phoenix","suns"],
    "DET": ["detroit","pistons"],
    "ORL": ["orlando","magic"],
    "MIN": ["minnesota","timberwolves","wolves"],
    "DEN": ["denver","nuggets"],
    "ATL": ["atlanta","hawks"],
    "NYK": ["new york knicks","knicks","nyk"],
    "PHI": ["philadelphia","76ers","sixers"],
    "BOS": ["boston","celtics"],
    "MIA": ["miami heat","heat"],
    "CLE": ["cleveland","cavaliers","cavs"],
    "MIL": ["milwaukee","bucks"],
    "IND": ["indiana","pacers"],
    "CHI": ["chicago bulls","bulls"],
    "TOR": ["toronto raptors","raptors"],
    "BRK": ["brooklyn","nets","bkn"],
    "WAS": ["washington","wizards"],
    "CHA": ["charlotte","hornets"],
    "LAL": ["la lakers","lakers","los angeles lakers"],
    "LAC": ["la clippers","clippers","los angeles clippers"],
    "GSW": ["golden state","warriors"],
    "SAC": ["sacramento","kings"],
    "POR": ["portland","trail blazers","blazers"],
    "SAS": ["san antonio","spurs"],
    "HOU": ["houston rockets","rockets"],
    "MEM": ["memphis","grizzlies"],
    "NOP": ["new orleans","pelicans"],
    "DAL": ["dallas","mavericks","mavs"],
    "UTA": ["utah","jazz"],
    # MLB
    "STL": ["st. louis cardinals","st louis cardinals","cardinals"],
    "PIT": ["pittsburgh","pirates"],
    "CHC": ["chicago cubs","cubs"],
    "CHW": ["chicago white sox","white sox"],
    "SD":  ["san diego","padres"],
    "NYY": ["new york yankees","yankees"],
    "NYM": ["new york mets","mets"],
    "LAD": ["la dodgers","dodgers","los angeles dodgers"],
    "LAA": ["la angels","angels","los angeles angels"],
    "SF":  ["san francisco","giants"],
    "OAK": ["oakland","athletics"],
    "SEA": ["seattle","mariners"],
    "TEX": ["texas rangers","rangers"],
    "MIN": ["minnesota twins","twins"],
    "CLE": ["cleveland guardians","guardians"],
    "KC":  ["kansas city royals","royals"],
    "BAL": ["baltimore","orioles"],
    "TB":  ["tampa bay","rays"],
    "WSH": ["washington nationals","nationals"],
    "PHI": ["philadelphia phillies","phillies"],
    "BOS": ["boston red sox","red sox"],
    "TOR": ["toronto blue jays","blue jays"],
    # NFL
    "BUF": ["buffalo","bills"],
    "NWE": ["new england","patriots"],
    "MIA": ["miami dolphins","dolphins"],
    "NYJ": ["new york jets","jets"],
    "BAL": ["baltimore ravens","ravens"],
    "PIT": ["pittsburgh steelers","steelers"],
    "CLE": ["cleveland browns","browns"],
    "CIN": ["cincinnati","bengals"],
    "HOU": ["houston texans","texans"],
    "IND": ["indianapolis","colts"],
    "TEN": ["tennessee","titans"],
    "JAX": ["jacksonville","jaguars"],
    "KC":  ["kansas city chiefs","chiefs"],
    "LVR": ["las vegas","raiders"],
    "LAC": ["los angeles chargers","chargers"],
    "DEN": ["denver broncos","broncos"],
    "DAL": ["dallas cowboys","cowboys"],
    "NYG": ["new york giants","giants"],
    "PHI": ["philadelphia eagles","eagles"],
    "WAS": ["washington commanders","commanders"],
    "CHI": ["chicago bears","bears"],
    "DET": ["detroit lions","lions"],
    "GB":  ["green bay","packers"],
    "MIN": ["minnesota vikings","vikings"],
    "ATL": ["atlanta falcons","falcons"],
    "CAR": ["carolina","panthers"],
    "NO":  ["new orleans saints","saints"],
    "TB":  ["tampa bay buccaneers","buccaneers"],
    "SF":  ["san francisco 49ers","49ers","niners"],
    "SEA": ["seattle seahawks","seahawks"],
    "LAR": ["los angeles rams","rams"],
    "ARI": ["arizona","cardinals"],
}

# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ State ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

_state = {
    "kalshi_markets":    [],
    "ab_token":          None,
    "ab_session":        None,   # requests.Session() ÃÂ¢ÃÂÃÂ preserves cookies
    "ab_lines":          {},
    "ab_lines_raw":      None,   # raw response stored in memory (not on disk)
    "ab_lines_endpoint": None,
    "ab_header_variant": None,
    "ab_login_raw":      None,
    "arb_opps":          [],
    "last_updated":      None,
    "ab_status":         "Not configured",
    "ab_credentials":    None,
    "ab_customer_id":    "",    # populated on login from accountInfo.customerID
    "ab_office":         "PREMIER",  # populated on login from accountInfo.Office
    "errors":            [],
    "stake":             100.0,
    "probe_results":     {},    # path ÃÂ¢ÃÂÃÂ status code (for /api/debug)
    "sample_resp_headers": {},  # response headers from first 406/401 (debug)
}
_lock = threading.Lock()


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Odds Math ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def american_to_decimal(american):
    american = float(american)
    if american >= 0:
        return (american / 100.0) + 1.0
    return (100.0 / abs(american)) + 1.0

def decimal_to_american_str(decimal):
    if decimal >= 2.0:
        return f"+{int(round((decimal - 1.0) * 100))}"
    return f"{int(round(-100.0 / (decimal - 1.0)))}"

def price_to_american_str(price):
    if price <= 0.005 or price >= 0.995:
        return "N/A"
    return decimal_to_american_str(1.0 / price)

def check_arb(kalshi_price, ab_american, total_stake=100.0):
    if kalshi_price <= 0 or kalshi_price >= 1:
        return None
    try:
        ab_decimal = american_to_decimal(float(ab_american))
    except:
        return None

    p_kalshi      = kalshi_price
    p_ab          = 1.0 / ab_decimal
    total_implied = p_kalshi + p_ab

    if total_implied >= 0.997:
        return None

    kalshi_decimal = 1.0 / kalshi_price
    k_stake  = total_stake * (p_kalshi / total_implied)
    ab_stake = total_stake * (p_ab     / total_implied)
    payout   = k_stake * kalshi_decimal
    profit   = payout - total_stake

    return {
        "total_implied_pct": round(total_implied * 100, 2),
        "profit_pct":        round((profit / total_stake) * 100, 2),
        "kalshi_stake":      round(k_stake, 2),
        "ab_stake":          round(ab_stake, 2),
        "payout":            round(payout, 2),
        "profit":            round(profit, 2),
    }


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ ActionBets Auth ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def ab_login(username, password):
    """Login to ActionBets. Returns (token, session) or (None, None)."""
    session = requests.Session()
    url     = f"{AB_BASE}/System/authenticateCustomer"
    payload = {
        "customerID":    username.upper(),
        "state":         "true",
        "password":      password.upper(),
        "sufix":         "",
        "prefix":        "",
        "multiaccount":  "0",
        "response_type": "code",
        "client_id":     username.upper(),
        "domain":        AB_DOMAIN,
        "redirect_uri":  AB_DOMAIN,
        "token":         "",
        "operation":     "authenticateCustomer",
    }
    try:
        r = session.post(url, data=payload, timeout=20,
                         headers={"Authorization": "Bearer "})
        if r.ok:
            data = r.json()
            with _lock:
                _state["ab_login_raw"] = data
                # Store customer info for later API calls
                acct = data.get("accountInfo", {})
                _state["ab_customer_id"] = acct.get("customerID", username.upper()).strip()
                _state["ab_office"]      = acct.get("Office", "PREMIER").strip()
            if "code" in data:
                print(f"  [AB] Login OK. Cookies: {dict(session.cookies)}")
                return str(data["code"]), session
        print(f"  [AB] Login failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"  [AB] Login error: {e}")
    return None, None




def ab_auth_params(token):
    """Build the standard auth body params required by PPH Insider API."""
    with _lock:
        customer_id = _state.get("ab_customer_id", "")
        office      = _state.get("ab_office", "PREMIER")
    return {
        "customerID":    customer_id,
        "token":         token,
        "office":        office,
        "wagerType":     "S",
        "placeLateFlag": False,
        "RRO":           1,
        "agentSite":     0,
    }


def ab_fetch_leagues(token, session):
    """
    Fetch available sports/leagues from League/Get_SportsLeagues.
    Returns list of league dicts or None on failure.
    """
    url = AB_BASE + "/League/Get_SportsLeagues"
    params = {**ab_auth_params(token), "operation": "Get_SportsLeagues"}
    headers = {
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {token}",
    }
    try:
        r = session.post(url, data=params, headers=headers, timeout=15)
        print(f"  [AB] Get_SportsLeagues -> {r.status_code}")
        if r.ok:
            data = r.json()
            leagues = data.get("Leagues", [])
            print(f"  [AB] Got {len(leagues)} leagues")
            return leagues
        print(f"  [AB] Get_SportsLeagues failed: {r.text[:300]}")
    except Exception as e:
        print(f"  [AB] Get_SportsLeagues error: {e}")
    return None


def ab_fetch_lines_for_sport(token, session, sport_type, sport_sub_type,
                              sport_sub_type2="", period="Game",
                              period_number=0, grouping=""):
    """
    Fetch game lines for a specific sport/league using Lines/Get_LeagueLines2.
    Returns raw response dict or None on failure.
    """
    headers = {
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Authorization": f"Bearer {token}",
    }
    params = {
        **ab_auth_params(token),
        "sportType":       sport_type,
        "sportSubType":    sport_sub_type,
        "sportSubType2":   sport_sub_type2,
        "period":          period,
        "periodNumber":    period_number,
        "grouping":        grouping,
        "propDescription": sport_sub_type2 or period,
        "operation":       "Get_LeagueLines2",
    }
    url = AB_BASE + "/Lines/Get_LeagueLines2"
    try:
        r = session.post(url, data=params, headers=headers, timeout=15)
        print(f"  [AB] Get_LeagueLines2 ({sport_type}/{sport_sub_type}) \u2192 {r.status_code}")
        if r.ok:
            data = r.json()
            lines = data.get("Lines", [])
            print(f"  [AB] Got {len(lines)} games for {sport_sub_type}")
            with _lock:
                _state["ab_lines_endpoint"] = url
            return data
        print(f"  [AB] Get_LeagueLines2 failed: {r.text[:200]}")
    except Exception as e:
        print(f"  [AB] Get_LeagueLines2 error: {e}")
    return None
def ab_probe_lines(token, session):
    """
    Systematically try every path x header combo to find working lines endpoint.
    Returns (raw_data, endpoint_url, winning_headers) or (None, None, None).
    """
    probe_results = {}

    # Capture response headers from first 406/401 for debugging
    sample_resp_headers = {}

    for path in AB_LINES_PATHS:
        url = AB_BASE + path

        # Try each Accept variant with Bearer token ÃÂ¢ÃÂÃÂ with and without agentSite param
        for param_set in [{"agentSite": 0}, {}]:
            for hv in AB_HEADER_VARIANTS:
                headers = {**hv, "Authorization": f"Bearer {token}"}
                param_label = "p" if param_set else "np"
                key = f"Bearer{param_label} {path} {hv.get('Accept','none')[:20]}"
                try:
                    r = session.get(url, params=param_set if param_set else None,
                                    headers=headers, timeout=15)
                    probe_results[key] = r.status_code
                    print(f"  [probe] {r.status_code} Bearer GET {path} params={param_label} accept={hv.get('Accept','none')[:30]}")
                    if not sample_resp_headers and r.status_code in (406, 401):
                        sample_resp_headers = dict(r.headers)
                    if r.ok and len(r.text) > 50:
                        try:
                            data = r.json()
                            print(f"  [probe] SUCCESS: {path}")
                            with _lock:
                                _state["probe_results"] = probe_results
                                _state["sample_resp_headers"] = sample_resp_headers
                            return data, url, headers
                        except:
                            pass
                except Exception as e:
                    probe_results[key] = str(e)

        # Cookie-only (session cookies from login, no Authorization header)
        for hv in AB_HEADER_VARIANTS[:3]:  # just top 3 to keep it fast
            try:
                r = session.get(url, params={"agentSite": 0}, headers=hv, timeout=15)
                key = f"cookie {path}"
                probe_results[key] = r.status_code
                print(f"  [probe] {r.status_code} cookie GET {path} accept={hv.get('Accept','none')[:30]}")
                if r.ok and len(r.text) > 50:
                    try:
                        data = r.json()
                        print(f"  [probe] SUCCESS cookie: {path}")
                        with _lock:
                            _state["probe_results"] = probe_results
                            _state["sample_resp_headers"] = sample_resp_headers
                        return data, url, hv
                    except:
                        pass
            except Exception as e:
                probe_results[f"cookie {path}"] = str(e)

        # POST with Bearer (JSON body)
        for post_hv in [
            {"Accept": "application/json, text/plain, */*", "X-Requested-With": "XMLHttpRequest",
             "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            {"Accept": "application/json, text/plain, */*", "Authorization": f"Bearer {token}"},
            {"Accept": "*/*", "Authorization": f"Bearer {token}"},
        ]:
            try:
                r = session.post(url, json={}, headers=post_hv, timeout=15)
                key = f"POST-bearer {path}"
                probe_results[key] = r.status_code
                print(f"  [probe] {r.status_code} POST-bearer {path}")
                if r.ok and len(r.text) > 50:
                    try:
                        data = r.json()
                        print(f"  [probe] SUCCESS POST-bearer: {path}")
                        with _lock:
                            _state["probe_results"] = probe_results
                            _state["sample_resp_headers"] = sample_resp_headers
                        return data, url, post_hv
                    except:
                        pass
                if not sample_resp_headers and r.status_code in (406, 401):
                    sample_resp_headers = dict(r.headers)
                break  # only try first non-exception
            except:
                pass

        # POST no auth (cookie session)
        try:
            r = session.post(url, json={}, headers={"Accept": "application/json, text/plain, */*",
                                                     "X-Requested-With": "XMLHttpRequest"}, timeout=15)
            probe_results[f"POST-cookie {path}"] = r.status_code
        except:
            pass

    with _lock:
        _state["probe_results"] = probe_results
        _state["sample_resp_headers"] = sample_resp_headers
    return None, None, None

def ab_fetch_lines(token, session, endpoint, headers):
    """Fetch lines from known working endpoint."""
    try:
        r = session.get(endpoint, params={"agentSite": 0}, headers=headers, timeout=15)
        if r.ok and len(r.text) > 50:
            return r.json()
    except Exception as e:
        print(f"  [AB] fetch lines error: {e}")
    return None


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Parse AB Lines ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def parse_ab_lines(raw_data, sport_sub=""):
    """
    Parse ActionBets Get_LeagueLines2 response into {team_key: {ml, team, sport}}.
    Response shape: {"Lines": [{Team1ID, Team2ID, MoneyLine1, MoneyLine2, ...}]}
    """
    lines = {}
    if not raw_data:
        return lines

    with _lock:
        _state["ab_lines_raw"] = raw_data

    sport = sport_sub.upper()
    game_list = raw_data.get("Lines", [])
    for game in game_list:
        if not isinstance(game, dict):
            continue
        t1  = game.get("Team1ID", "")
        t2  = game.get("Team2ID", "")
        ml1 = game.get("MoneyLine1")
        ml2 = game.get("MoneyLine2")

        if t1 and ml1 is not None:
            try:
                lines[t1.strip().lower()] = {"ml": float(ml1), "team": t1.strip(), "sport": sport}
            except (ValueError, TypeError):
                pass

        if t2 and ml2 is not None:
            try:
                lines[t2.strip().lower()] = {"ml": float(ml2), "team": t2.strip(), "sport": sport}
            except (ValueError, TypeError):
                pass

    return lines
def match_team(kalshi_code, ab_lines, required_sport=""):
    aliases = TEAM_ALIASES.get(kalshi_code.upper(), [kalshi_code.lower()])
    for ab_key, ab_data in ab_lines.items():
        if required_sport and ab_data.get("sport", "").upper() != required_sport.upper():
            continue
        for alias in aliases:
            if alias in ab_key or ab_key in alias:
                return ab_data["team"], ab_data["ml"]
    return None, None


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Kalshi Fetch ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def _get(url):
    try:
        r = requests.get(url, timeout=12, headers={"Accept": "application/json"})
        if r.ok:
            return r.json()
    except Exception as e:
        print(f"  [Kalshi] {url}: {e}")
    return None


def fetch_kalshi_markets():
    markets = []
    for series in KALSHI_SERIES:
        data = _get(f"{KALSHI_BASE}/events?limit=50&status=open&series_ticker={series}")
        if not data:
            continue
        for event in data.get("events", []):
            eticker = event["event_ticker"]
            mdata   = _get(f"{KALSHI_BASE}/markets?event_ticker={eticker}&status=open&limit=30")
            if not mdata:
                continue
            for m in mdata.get("markets", []):
                if m.get("market_type") != "binary":
                    continue
                yes_ask = float(m.get("yes_ask_dollars") or 0)
                no_ask  = float(m.get("no_ask_dollars")  or 0)
                if yes_ask <= 0.005 or yes_ask >= 0.995:
                    continue
                if no_ask <= 0:
                    no_ask = round(1.0 - yes_ask, 4)
                ticker    = m.get("ticker", "")
                parts     = ticker.split("-")
                team_code = parts[-1] if len(parts) >= 3 else ""
                markets.append({
                    "ticker":       ticker,
                    "event_ticker": eticker,
                    "event_title":  event.get("title", eticker),
                    "event_sub":    event.get("sub_title", ""),
                    "series":       series,
                    "title":        m.get("title", ""),
                    "team_code":    team_code,
                    "yes_price":    yes_ask,
                    "no_price":     no_ask,
                    "yes_american": price_to_american_str(yes_ask),
                    "no_american":  price_to_american_str(no_ask),
                    "close_time":   m.get("close_time", ""),
                })
    return markets


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Arb Engine ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def parse_opponent_code(event_sub, team_code):
    """Extract opponent team code from event_sub like 'POR at SAS (Apr 28)'."""
    s = event_sub.upper()
    for sep in [" AT ", " VS ", " VS. ", " @ "]:
        if sep in s:
            parts = s.split(sep)
            away = parts[0].strip().split()[0]
            home = parts[1].strip().split()[0]
            if team_code.upper() == away:
                return home
            elif team_code.upper() == home:
                return away
    return ""

# Only game-winner series support team-based arb matching
GAME_SERIES = {"KXNBAGAME", "KXMLBGAME", "KXNFLGAME"}
SERIES_TO_SPORT = {
    "KXNBAGAME": "NBA",
    "KXMLBGAME": "MLB",
    "KXNFLGAME": "NFL",
}

def find_arb_opps(kalshi_markets, ab_lines, stake=100.0):
    opps = []
    for m in kalshi_markets:
        series = m.get("series", "")
        # Skip totals (KXNBATOTAL, KXMLBTOTAL, KXNHLTOTAL) â no moneyline match possible
        if series not in GAME_SERIES:
            continue
        code = m.get("team_code", "")
        if not code:
            continue

        sport = SERIES_TO_SPORT.get(series, "")
        # team_code = the team that Kalshi YES means wins
        ab_team, ab_ml = match_team(code, ab_lines, required_sport=sport)

        # Find opponent for correct YES-side pairing
        opp_code = parse_opponent_code(m.get("event_sub", ""), code)
        ab_opp, ab_ml_opp = (match_team(opp_code, ab_lines, required_sport=sport)
                             if opp_code else (None, None))

        # YES: Kalshi YES (team wins) vs AB on OPPONENT (team loses) â opposite outcomes
        if ab_opp and ab_ml_opp is not None:
            arb = check_arb(m["yes_price"], ab_ml_opp, stake)
            if arb:
                opps.append({
                    "event_title":     m["event_title"],
                    "event_sub":       m["event_sub"],
                    "series":          series,
                    "kalshi_ticker":   m["ticker"],
                    "kalshi_side":     f"YES (Kalshi) â {ab_team} wins",
                    "kalshi_price":    m["yes_price"],
                    "kalshi_american": price_to_american_str(m["yes_price"]),
                    "ab_team":         ab_opp,
                    "ab_ml":           ab_ml_opp,
                    "ab_american":     decimal_to_american_str(american_to_decimal(ab_ml_opp)),
                    "stake":           stake,
                    **arb,
                })

        # NO: Kalshi NO (team loses) vs AB on SAME TEAM (team wins) â opposite outcomes
        if ab_team and ab_ml is not None:
            arb = check_arb(m["no_price"], ab_ml, stake)
            if arb:
                opps.append({
                    "event_title":     m["event_title"],
                    "event_sub":       m["event_sub"],
                    "series":          series,
                    "kalshi_ticker":   m["ticker"],
                    "kalshi_side":     f"NO (Kalshi) â {ab_team} loses",
                    "kalshi_price":    m["no_price"],
                    "kalshi_american": price_to_american_str(m["no_price"]),
                    "ab_team":         ab_team,
                    "ab_ml":           ab_ml,
                    "ab_american":     decimal_to_american_str(american_to_decimal(ab_ml)),
                    "stake":           stake,
                    **arb,
                })

    opps.sort(key=lambda x: x["profit_pct"], reverse=True)
    return opps
def load_credentials():
    # 1. Environment variables (Railway)
    u = os.environ.get("AB_USERNAME", "").strip()
    p = os.environ.get("AB_PASSWORD", "").strip()
    if u and p:
        print(f"  [Creds] Loaded from environment vars: {u}")
        return u, p

    # 2. ab_config.json (local dev)
    for cfg_path in ["ab_config.json", "../ab_config.json",
                     os.path.expanduser("~/Documents/ab_config.json")]:
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            u = cfg.get("username", "").strip()
            p = cfg.get("password", "").strip()
            if u and p and u not in ("YOUR_ACTIONBETS_USERNAME",):
                print(f"  [Creds] Loaded from {cfg_path}: {u}")
                return u, p
        except:
            pass
    return None, None


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Background Refresh ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def full_refresh(stake=100.0):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Refreshing...")

    # Kalshi
    kalshi = fetch_kalshi_markets()
    print(f"  Kalshi: {len(kalshi)} markets")

    # ActionBets
    with _lock:
        token    = _state["ab_token"]
        session  = _state["ab_session"]
        endpoint = _state["ab_lines_endpoint"]
        hdrs     = _state["ab_header_variant"]
        creds    = _state["ab_credentials"]

    ab_lines  = {}
    ab_status = "Not configured"

    username, password = (creds if creds else load_credentials()) or (None, None)

    if username and password:
        if not token or not session:
            print(f"  Logging into ActionBets as {username}...")
            token, session = ab_login(username, password)
            if token:
                ab_status = "Logged in ÃÂ¢ÃÂÃÂ discovering lines endpoint..."
                endpoint  = None
                hdrs      = None
            else:
                ab_status = "Login failed"

        if token and session:
            print("  Fetching AB leagues via League/Get_SportsLeagues...")
            leagues = ab_fetch_leagues(token, session)
            if leagues is None:
                # Re-login and try again
                print("  League fetch failed ÃÂ¢ÃÂÃÂ re-logging in...")
                token, session = ab_login(username, password)
                if token:
                    leagues = ab_fetch_leagues(token, session)

            if leagues:
                # Target sports: NBA, MLB, NFL, NHL
                TARGET_SPORTS = {
                    "BASKETBALL": ["NBA"],
                    "BASEBALL":   ["MLB"],
                    "FOOTBALL":   ["NFL"],
                    "HOCKEY":     ["NHL"],
                }
                all_raw_lines = {}
                for lg in leagues:
                    sport_type  = lg.get("SportType", "").upper()
                    sport_sub   = lg.get("SportSubType", "").upper()
                    period_num  = lg.get("PeriodNumber", 0)
                    active_val  = lg.get("Active", 0)
                    is_active   = (active_val == 1 or str(active_val).upper() == "Y")
                    # Only main game lines (PeriodNumber=0) for target sports
                    if not is_active or period_num != 0:
                        continue
                    for sport, subs in TARGET_SPORTS.items():
                        if sport_type == sport and any(s in sport_sub for s in subs):
                            raw = ab_fetch_lines_for_sport(
                                token, session,
                                lg.get("SportType", ""),
                                lg.get("SportSubType", ""),
                                lg.get("SportSubType2", ""),
                                lg.get("PeriodDescription", "Game"),
                                period_num,
                                lg.get("Grouping", ""),
                            )
                            if raw:
                                parsed = parse_ab_lines(raw, sport_sub=lg.get("SportSubType", ""))
                                all_raw_lines.update(parsed)
                if all_raw_lines:
                    ab_lines  = all_raw_lines
                    ab_status = f"Live ÃÂ¢ÃÂÃÂ {len(ab_lines)} teams"
                    print(f"  AB lines: {len(ab_lines)} teams")
                else:
                    ab_status = "Logged in Ã¢ÂÂ no games found on Lines/Get_LeagueLines2"
            else:
                ab_status = "Logged in Ã¢ÂÂ league fetch failed (check /api/test-leagues)"

    else:
        ab_status = "Set AB_USERNAME + AB_PASSWORD in Railway env vars"

    opps = find_arb_opps(kalshi, ab_lines, stake)
    print(f"  Arb opportunities: {len(opps)}")

    with _lock:
        _state["kalshi_markets"]    = kalshi
        _state["ab_token"]          = token
        _state["ab_session"]        = session
        _state["ab_lines"]          = ab_lines
        _state["ab_lines_endpoint"] = endpoint
        _state["ab_header_variant"] = hdrs
        _state["ab_status"]         = ab_status
        _state["arb_opps"]          = opps
        _state["last_updated"]      = datetime.now().isoformat()
        if username:
            _state["ab_credentials"] = (username, password)

def background_loop():
    while True:
        try:
            with _lock:
                stake = _state.get("stake", 100.0)
            full_refresh(stake)
        except Exception as e:
            print(f"  [BG Error] {e}")
        time.sleep(60)


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Flask Routes ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify({
            "kalshi_count": len(_state["kalshi_markets"]),
            "ab_status":    _state["ab_status"],
            "arb_count":    len(_state["arb_opps"]),
            "last_updated": _state["last_updated"],
            "ab_endpoint":  _state["ab_lines_endpoint"],
        })


@app.route("/api/arb-opps")
def api_arb_opps():
    with _lock:
        return jsonify({
            "opps":         _state["arb_opps"],
            "ab_status":    _state["ab_status"],
            "kalshi_count": len(_state["kalshi_markets"]),
            "last_updated": _state["last_updated"],
        })


@app.route("/api/force-refresh")
def api_force_refresh():
    with _lock:
        stake = _state.get("stake", 100.0)
    full_refresh(stake)
    with _lock:
        return jsonify({
            "ok":       True,
            "arb_count": len(_state["arb_opps"]),
            "ab_status": _state["ab_status"],
        })


@app.route("/api/set-stake/<float:stake>")
def api_set_stake(stake):
    with _lock:
        _state["stake"] = stake
        opps = find_arb_opps(_state["kalshi_markets"], _state["ab_lines"], stake)
        _state["arb_opps"] = opps
    return jsonify({"ok": True, "stake": stake, "arb_count": len(opps)})


@app.route("/api/debug")
def api_debug():
    """Exposes raw AB probe results and login response for debugging."""
    with _lock:
        return jsonify({
            "ab_login_raw":      _state["ab_login_raw"],
            "ab_lines_raw":      _state["ab_lines_raw"],
            "ab_lines_endpoint": _state["ab_lines_endpoint"],
            "ab_header_variant": str(_state["ab_header_variant"]),
            "probe_results":       _state["probe_results"],
            "sample_resp_headers": _state["sample_resp_headers"],
            "ab_status":           _state["ab_status"],
            "ab_teams_parsed":     list(_state["ab_lines"].keys())[:30],
        })


@app.route("/api/probe-live")
def api_probe_live():
    """Make a live POST to an AB endpoint and return the full response for debugging."""
    from flask import request as flask_request
    path  = flask_request.args.get("path", "/Lines/GetStraightLines")
    body  = flask_request.args.get("body", "{}")
    try:
        b = json.loads(body)
    except:
        b = {}
    with _lock:
        token   = _state.get("ab_token")
        session = _state.get("ab_session")
    if not token or not session:
        return jsonify({"error": "Not logged in ÃÂ¢ÃÂÃÂ no token/session"})
    # Always include full auth params (required by PPH Insider API)
    form_data = {**ab_auth_params(token), **b}
    url = AB_BASE + path
    results = {}
    ax_hdrs = {"Accept":"application/json, text/plain, */*","X-Requested-With":"XMLHttpRequest","Authorization":f"Bearer {token}"}
    # POST form-encoded with agentSite=0 (how the browser jQuery does it)
    try:
        r = session.post(url, data=form_data, headers={**ax_hdrs}, timeout=15)
        results["POST-form-agentSite0"] = {"status": r.status_code, "body": r.text[:800], "ct": r.headers.get("Content-Type","")}
    except Exception as e:
        results["POST-form-agentSite0"] = {"error": str(e)}
    # POST JSON with agentSite=0
    try:
        r = session.post(url, json=form_data, headers={**ax_hdrs, "Content-Type":"application/json"}, timeout=15)
        results["POST-json-agentSite0"] = {"status": r.status_code, "body": r.text[:800], "ct": r.headers.get("Content-Type","")}
    except Exception as e:
        results["POST-json-agentSite0"] = {"error": str(e)}
    # POST form empty
    try:
        r = session.post(url, data={}, headers={**ax_hdrs}, timeout=15)
        results["POST-form-empty"] = {"status": r.status_code, "body": r.text[:800], "ct": r.headers.get("Content-Type","")}
    except Exception as e:
        results["POST-form-empty"] = {"error": str(e)}
    # GET
    try:
        r = session.get(url, headers=ax_hdrs, timeout=15)
        results["GET"] = {"status": r.status_code, "body": r.text[:400], "ct": r.headers.get("Content-Type","")}
    except Exception as e:
        results["GET"] = {"error": str(e)}
    return jsonify(results)


@app.route("/api/scan-paths")
def api_scan_paths():
    """Batch probe many AB paths with form-encoded agentSite=0. Returns status+body snippet for each."""
    from flask import request as flask_request
    with _lock:
        token   = _state.get("ab_token")
        session = _state.get("ab_session")
    if not token or not session:
        return jsonify({"error": "Not logged in"})
    ax_hdrs = {"Accept":"application/json, text/plain, */*","X-Requested-With":"XMLHttpRequest","Authorization":f"Bearer {token}"}
    auth = ab_auth_params(token)
    # Paths to probe ÃÂ¢ÃÂÃÂ underscore naming convention discovered from Get_SportsLeagues
    paths_to_try = [
        # League model ÃÂ¢ÃÂÃÂ confirmed working base (Get_SportsLeagues returns 200)
        "/League/Get_SportsLeagues",
        "/League/Get_Lines",
        "/League/Get_StraightLines",
        "/League/Get_GameLines",
        "/League/Get_Games",
        "/League/verifyLeagues",
        # Lines model ÃÂ¢ÃÂÃÂ PascalCase and underscore variants
        "/Lines/Get_Lines",
        "/Lines/Get_StraightLines",
        "/Lines/Get_GameLines",
        "/Lines/Get_SportsLines",
        "/Lines/Get_Games",
        "/Lines/getLines",
        "/Lines/getStraightLines",
        # Board model (returned 500 with empty body ÃÂ¢ÃÂÃÂ try with auth params)
        "/Board/Get_Lines",
        "/Board/Get_Games",
        "/Board/Get_StraightLines",
        "/Board/GetLines",
        "/Board/GetGames",
        # Game model (returned 500 with empty body ÃÂ¢ÃÂÃÂ try with auth params)
        "/Game/Get_Games",
        "/Game/Get_Lines",
        "/Game/GetGames",
        "/Game/GetLines",
        # Schedule model
        "/Schedule/Get_Games",
        "/Schedule/Get_Lines",
        "/Schedule/GetGames",
        # Sports model
        "/Sports/Get_Sports",
        "/Sports/Get_Lines",
        "/Sports/Get_Games",
        # WagerSport model (from wager.js)
        "/WagerSport/checkWagerLineMulti",
        "/WagerSport/Get_Lines",
        # Customer lines
        "/Customer/Get_Lines",
        "/Customer/getLines",
    ]
    results = {}
    for p in paths_to_try:
        url = AB_BASE + p
        func_name = p.split("/")[-1]
        params = {**auth, "operation": func_name}
        try:
            r = session.post(url, data=params, headers=ax_hdrs, timeout=10)
            snippet = r.text[:500].replace("\n"," ")
            results[p] = {"status": r.status_code, "body": snippet, "ct": r.headers.get("Content-Type","")}
        except Exception as e:
            results[p] = {"error": str(e)}
    return jsonify(results)


@app.route("/api/test-leagues")
def api_test_leagues():
    """Call League/Get_SportsLeagues with full auth params and return raw response."""
    with _lock:
        token   = _state.get("ab_token")
        session = _state.get("ab_session")
    if not token or not session:
        return jsonify({"error": "Not logged in"})
    leagues = ab_fetch_leagues(token, session)
    if leagues is None:
        return jsonify({"error": "Get_SportsLeagues returned None"})
    # Filter for sports we care about
    sports = {}
    for lg in leagues:
        st = lg.get("SportType", "")
        if st not in sports:
            sports[st] = []
        sports[st].append({
            "SportSubType":    lg.get("SportSubType"),
            "PeriodNumber":    lg.get("PeriodNumber"),
            "PeriodDescription": lg.get("PeriodDescription"),
            "Active":          lg.get("Active"),
        })
    return jsonify({"total": len(leagues), "by_sport": sports, "raw_first_5": leagues[:5]})


@app.route("/api/test-lines")
def api_test_lines():
    """Try to fetch lines for NBA/MLB using discovered sport params from /api/test-leagues."""
    from flask import request as flask_request
    sport_type    = flask_request.args.get("sport", "BASKETBALL")
    sport_subtype = flask_request.args.get("sub", "NBA")
    period        = flask_request.args.get("period", "Game")
    with _lock:
        token   = _state.get("ab_token")
        session = _state.get("ab_session")
    if not token or not session:
        return jsonify({"error": "Not logged in"})
    raw = ab_fetch_lines_for_sport(token, session, sport_type, sport_subtype, period=period)
    if raw is None:
        return jsonify({"error": "All line endpoints failed"})
    return jsonify({"ok": True, "preview": str(raw)[:2000]})

@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Frontend ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arb Scanner ÃÂ¢ÃÂÃÂ Kalshi x ActionBets</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0a0d12; --surface: #13181f; --card: #1a2030;
    --border: #252d3a; --text: #e2eaf5; --muted: #6b7a96;
    --green: #00c97a; --green-dim: rgba(0,201,122,0.10); --green-border: rgba(0,201,122,0.35);
    --red: #ff4757; --yellow: #ffd700; --blue: #4a9eff;
  }
  body { background: var(--bg); color: var(--text); font-family: "Segoe UI", system-ui, sans-serif; font-size: 14px; min-height: 100vh; }
  header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 0 24px; display: flex; align-items: center; gap: 20px; height: 56px; position: sticky; top: 0; z-index: 50; }
  .logo { font-size: 15px; font-weight: 800; color: var(--green); letter-spacing: -0.5px; }
  .logo span { color: var(--muted); font-weight: 400; font-size: 13px; margin-left: 6px; }
  .header-right { display: flex; align-items: center; gap: 12px; margin-left: auto; }
  .stake-group { display: flex; align-items: center; gap: 8px; background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 5px 12px; }
  .stake-group label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }
  .stake-group input { background: transparent; border: none; color: var(--text); font-size: 14px; font-weight: 700; width: 80px; outline: none; }
  .btn { background: var(--blue); color: #fff; border: none; border-radius: 6px; padding: 7px 16px; font-size: 12px; font-weight: 700; cursor: pointer; }
  .btn:hover { opacity: .85; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  #status-bar { background: var(--surface); border-bottom: 1px solid var(--border); padding: 7px 24px; display: flex; align-items: center; gap: 20px; font-size: 12px; color: var(--muted); }
  .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--muted); }
  .dot.live { background: var(--green); box-shadow: 0 0 6px var(--green); animation: pulse 2s infinite; }
  .dot.warn { background: var(--yellow); }
  .dot.err  { background: var(--red); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
  .si { display: flex; align-items: center; gap: 6px; }
  #lu { margin-left: auto; }
  main { max-width: 960px; margin: 0 auto; padding: 28px 20px; }
  .center-state { text-align: center; padding: 80px 20px; color: var(--muted); }
  .spinner { width: 36px; height: 36px; border: 3px solid var(--border); border-top-color: var(--green); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .center-state h2 { font-size: 22px; margin-bottom: 10px; color: var(--text); }
  .center-state p { max-width: 400px; margin: 0 auto; line-height: 1.7; }
  .warn-box { background: rgba(255,215,0,0.08); border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; font-size: 13px; color: var(--yellow); }
  #arb-hdr { margin-bottom: 18px; }
  #arb-hdr h2 { font-size: 20px; font-weight: 800; color: var(--green); }
  #arb-hdr .sub { font-size: 12px; color: var(--muted); margin-top: 3px; }
  .card { background: var(--card); border: 1px solid var(--green-border); border-radius: 10px; margin-bottom: 14px; overflow: hidden; box-shadow: 0 0 20px var(--green-dim); }
  .card-hdr { background: var(--green-dim); border-bottom: 1px solid var(--green-border); padding: 10px 16px; display: flex; align-items: center; gap: 12px; }
  .rank { font-size: 11px; font-weight: 800; color: var(--green); background: rgba(0,201,122,0.12); border: 1px solid var(--green-border); border-radius: 4px; padding: 2px 7px; }
  .game { font-size: 14px; font-weight: 700; }
  .sub2 { font-size: 12px; color: var(--muted); }
  .pct { margin-left: auto; font-size: 22px; font-weight: 900; color: var(--green); }
  .card-body { padding: 14px 16px; }
  .bets { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
  .bet { background: rgba(255,255,255,0.025); border: 1px solid var(--border); border-radius: 7px; padding: 11px 13px; }
  .bet .where { font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: var(--muted); margin-bottom: 5px; }
  .bet .what  { font-size: 12px; font-weight: 600; color: var(--text); margin-bottom: 3px; }
  .bet .amt   { font-size: 26px; font-weight: 900; color: var(--green); line-height: 1; }
  .bet .odds  { font-size: 12px; color: var(--muted); margin-top: 3px; }
  .bet .covers { font-size: 11px; color: var(--green); background: rgba(0,201,122,0.08); border-radius: 4px; padding: 3px 7px; margin: 5px 0 8px; display: inline-block; font-weight: 600; }
  .summary { background: rgba(0,201,122,0.05); border: 1px solid var(--green-border); border-radius: 6px; padding: 10px 14px; display: flex; gap: 20px; font-size: 13px; }
  .sl { color: var(--muted); font-size: 11px; }
  .sv { font-weight: 700; color: var(--green); font-size: 15px; }
  .sv.big { font-size: 19px; }
  .g { margin-left: auto; font-size: 11px; color: var(--muted); align-self: center; }
  .no-arb { text-align: center; padding: 60px 20px; color: var(--muted); }
  .no-arb .icon { font-size: 44px; margin-bottom: 14px; }
  .no-arb h3 { font-size: 17px; color: var(--text); margin-bottom: 8px; }
  .no-arb p { max-width: 360px; margin: 0 auto; line-height: 1.7; font-size: 13px; }
  .mkt-box { margin-top: 18px; background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; display: inline-block; text-align: left; }
  footer { text-align: center; padding: 24px; color: var(--muted); font-size: 11px; border-top: 1px solid var(--border); margin-top: 40px; }
</style>
</head>
<body>
<header>
  <div class="logo">ARB SCANNER <span>Kalshi ÃÂÃÂ ActionBets</span></div>
  <div class="header-right">
    <div class="stake-group">
      <label>STAKE $</label>
      <input type="number" id="stake-input" value="100" min="1" max="100000" step="10">
    </div>
    <button class="btn" onclick="forceRefresh()" id="rbtn">Refresh Now</button>
  </div>
</header>

<div id="status-bar">
  <div class="si"><div class="dot" id="kdot"></div><span id="kstat">Loading...</span></div>
  <div class="si"><div class="dot" id="adot"></div><span id="astat">ActionBets: checking...</span></div>
  <div id="lu"></div>
</div>

<main>
  <div id="loading" class="center-state">
    <div class="spinner"></div>
    <h2>Scanning for arbitrage...</h2>
    <p>Fetching live Kalshi markets and connecting to ActionBets. First load takes ~20 seconds.</p>
  </div>
  <div id="content" style="display:none"></div>
</main>

<footer>Auto-refreshes every 60 seconds &mdash; Only guaranteed profit opportunities shown &mdash; 100% mathematical certainty</footer>

<script>
let pollTimer, stakeDebounce;
const ICONS = {KXNBAGAME:'NBA',KXMLBGAME:'MLB',KXNFLGAME:'NFL',KXNHLTOTAL:'NHL',KXNBATOTAL:'NBA Total',KXMLBTOTAL:'MLB Total'};

window.addEventListener('DOMContentLoaded', () => {
  poll(); startPoll();
  document.getElementById('stake-input').addEventListener('input', e => {
    clearTimeout(stakeDebounce);
    stakeDebounce = setTimeout(() => {
      fetch('/api/set-stake/' + (parseFloat(e.target.value)||100)).then(() => poll());
    }, 600);
  });
});
function startPoll() { clearInterval(pollTimer); pollTimer = setInterval(poll, 10000); }
async function poll() {
  try { const r = await fetch('/api/arb-opps'); render(await r.json()); } catch(e) {}
}
async function forceRefresh() {
  const btn = document.getElementById('rbtn');
  btn.disabled = true; btn.textContent = 'Refreshing...';
  try { await fetch('/api/force-refresh'); await poll(); }
  finally { btn.disabled = false; btn.textContent = 'Refresh Now'; startPoll(); }
}

function getCovers(o) {
  var isYes = /\bYES\b/i.test(o.kalshi_side);
  var abTeamName = o.ab_team.replace(/\s*@\s*[+\-]?\d+.*$/, '').trim();
  var abCity = abTeamName.split(' ')[0].toLowerCase();
  var titleClean = o.event_title.replace(/^Game\s+\d+[:\s]+/i, '');
  var atParts = titleClean.split(/\s+at\s+/i);
  var team1 = (atParts[0] || '').trim(), team2 = (atParts[1] || '').trim();
  var opponent = team1.toLowerCase().startsWith(abCity) ? team2 : team1;
  if (isYes) {
    var m = o.kalshi_side.match(/[\u2014\-]\s*(.+?)\s+wins\b/i);
    return { kalshi: (m ? m[1] : team1) + ' wins', ab: abTeamName + ' wins' };
  }
  return { kalshi: (opponent || '?') + ' wins', ab: abTeamName + ' wins' };
}
function render(data) {
  document.getElementById('loading').style.display = 'none';
  document.getElementById('content').style.display = 'block';

  const ab = data.ab_status||'';
  document.getElementById('kstat').textContent = (data.kalshi_count||0) + ' Kalshi markets';
  document.getElementById('kdot').className = 'dot ' + (data.kalshi_count > 0 ? 'live' : 'err');
  document.getElementById('astat').textContent = 'ActionBets: ' + ab;
  document.getElementById('adot').className = 'dot ' +
    (ab.includes('Live') ? 'live' : ab.match(/fail|error/i) ? 'err' : 'warn');
  if (data.last_updated) {
    document.getElementById('lu').textContent = 'Updated ' + new Date(data.last_updated).toLocaleTimeString();
  }

  const opps = data.opps||[], stake = document.getElementById('stake-input').value;
  let html = '';
  if (ab.match(/config|not configured/i))
    html += '<div class="warn-box">ActionBets not connected. Set AB_USERNAME and AB_PASSWORD environment variables.</div>';
  else if (ab.match(/fail/i))
    html += '<div class="warn-box">ActionBets login failed. Check your credentials.</div>';
  else if (ab.match(/endpoint not found/i))
    html += '<div class="warn-box">ActionBets logged in but lines endpoint not found yet. Check <a href="/api/debug" style="color:var(--yellow)">/api/debug</a> for probe results.</div>';

  if (!opps.length) {
    html += '<div class="no-arb"><div class="icon">ÃÂ°ÃÂÃÂÃÂ</div><h3>No arb opportunities right now</h3><p>Odds are too close across both books. Checks every 60 seconds ÃÂ¢ÃÂÃÂ gaps appear when games are about to start or odds shift.</p>';
    html += '<div class="mkt-box"><div style="font-size:11px;color:var(--muted);margin-bottom:5px">WATCHING</div><div style="font-weight:700">' + (data.kalshi_count||0) + ' Kalshi markets</div><div style="color:var(--muted);font-size:12px">NBA ÃÂÃÂ· MLB ÃÂÃÂ· NFL ÃÂÃÂ· Totals</div></div></div>';
  } else {
    html += '<div id="arb-hdr"><h2>ÃÂ°ÃÂÃÂÃÂ¢ ' + opps.length + ' Guaranteed Profit' + (opps.length>1?'s':'') + ' Found</h2><div class="sub">Sorted highest first ÃÂÃÂ· $' + stake + ' total stake</div></div>';
    opps.forEach((o,i) => {
      html += '<div class="card"><div class="card-hdr">';
      html += '<span class="rank">#'+(i+1)+' '+(ICONS[o.series]||'')+'</span>';
      html += '<div><div class="game">'+o.event_title+'</div><div class="sub2">'+o.event_sub+'</div></div>';
      html += '<div class="pct">+'+o.profit_pct+'%</div></div>';
      html += '<div class="card-body"><div class="bets">';
      const covers = getCovers(o);
      html += '<div class="bet"><div class="where">KALSHI</div><div class="what">'+o.kalshi_side+'</div>';
      html += '<div class="covers">✓ Pays if: <strong>'+covers.kalshi+'</strong></div>';
      html += '<div class="amt">$'+o.kalshi_stake+'</div><div class="odds">@ '+o.kalshi_american+' ('+Math.round(o.kalshi_price*100)+'% implied)</div></div>';
      html += '<div class="bet"><div class="where">ACTIONBETS</div><div class="what">'+o.ab_team+'</div>';
      html += '<div class="covers">✓ Pays if: <strong>'+covers.ab+'</strong></div>';
      html += '<div class="amt">$'+o.ab_stake+'</div><div class="odds">@ '+o.ab_american+'</div></div></div>';
      html += '<div class="summary"><div><div class="sl">Total staked</div><div class="sv">$'+o.stake+'</div></div>';
      html += '<div><div class="sl">Payout (either outcome)</div><div class="sv">$'+o.payout+'</div></div>';
      html += '<div><div class="sl">Guaranteed profit</div><div class="sv big">+$'+o.profit+'</div></div>';
      html += '<div class="g">Win no matter what ÃÂ¢ÃÂÃÂ</div></div></div></div>';
    });
  }
  document.getElementById('content').innerHTML = html;
}
</script>
</body>
</html>
"""


# ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ Entry Point ÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¢ÃÂÃÂ

def start_background():
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()


# Start background thread when gunicorn imports this module
start_background()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print("\n" + "="*60)
    print("  Kalshi x ActionBets Arbitrage Scanner")
    print("="*60)
    u, p = load_credentials()
    if u:
        print(f"  Credentials: {u} (loaded)")
        with _lock:
            _state["ab_credentials"] = (u, p)
    else:
        print("  Credentials: NOT FOUND ÃÂ¢ÃÂÃÂ set AB_USERNAME / AB_PASSWORD")
    print(f"  Port: {port}")
    print("="*60 + "\n")
    app.run(debug=False, port=port, use_reloader=False)
