from __future__ import annotations

import json
import os
from collections import Counter
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import streamlit as st

API_BASE_URL = "https://www.thesportsdb.com/api/v1/json"
API_KEY = os.getenv("THESPORTSDB_API_KEY", "123")
SERIE_A_LEAGUE_ID = "4332"

FALLBACK_MATCHES = [
    {
        "id": "fallback-1",
        "kickoff": "20:45",
        "status": "LIVE",
        "minute": "67'",
        "home": "Inter",
        "away": "Milan",
        "score": (2, 1),
        "venue": "San Siro",
        "competition": "Serie A",
        "events": [
            ("12'", "Inter", "Lautaro Martinez"),
            ("28'", "Milan", "Rafael Leao"),
            ("55'", "Inter", "Hakan Calhanoglu"),
        ],
        "stats": {"Possesso": ("58%", "42%"), "Tiri": ("14", "8"), "xG": ("1.9", "0.9")},
        "form": ("W", "D", "W", "W", "L"),
    },
    {
        "id": "fallback-2",
        "kickoff": "18:00",
        "status": "FT",
        "minute": "Finale",
        "home": "Juventus",
        "away": "Roma",
        "score": (1, 1),
        "venue": "Allianz Stadium",
        "competition": "Serie A",
        "events": [
            ("17'", "Juventus", "Dusan Vlahovic"),
            ("74'", "Roma", "Paulo Dybala"),
        ],
        "stats": {"Possesso": ("51%", "49%"), "Tiri": ("11", "10"), "xG": ("1.1", "1.0")},
        "form": ("D", "W", "W", "D", "W"),
    },
    {
        "id": "fallback-3",
        "kickoff": "15:00",
        "status": "UPCOMING",
        "minute": "Pre",
        "home": "Napoli",
        "away": "Atalanta",
        "score": (0, 0),
        "venue": "Stadio Diego Armando Maradona",
        "competition": "Serie A",
        "events": [],
        "stats": {"Possesso": ("-", "-"), "Tiri": ("-", "-"), "xG": ("-", "-")},
        "form": ("W", "L", "W", "W", "D"),
    },
]

FALLBACK_STANDINGS = [
    ("Inter", 29, 67, 20, 7, 2, 61, 18),
    ("Juventus", 29, 62, 18, 8, 3, 48, 22),
    ("Milan", 29, 59, 18, 5, 6, 55, 31),
    ("Bologna", 29, 54, 15, 9, 5, 42, 25),
    ("Roma", 29, 51, 15, 6, 8, 52, 34),
]

FALLBACK_SCORERS = [
    ("Lautaro Martinez", "Inter", 23),
    ("Dusan Vlahovic", "Juventus", 16),
    ("Olivier Giroud", "Milan", 13),
]


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Space+Grotesk:wght@500;700&display=swap');
        :root {
            --bg: #09131b;
            --bg-soft: #0f1d29;
            --card: rgba(15, 29, 41, 0.92);
            --card-strong: #132433;
            --line: rgba(143, 172, 198, 0.16);
            --text: #eff7ff;
            --muted: #8ba2b7;
            --accent: #ff6b35;
            --accent-dark: #ffae8f;
            --green: #23c16b;
            --amber: #ffb020;
            --red: #ff5d73;
            --shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 107, 53, 0.18), transparent 26%),
                radial-gradient(circle at 85% 10%, rgba(35, 193, 107, 0.11), transparent 18%),
                linear-gradient(180deg, #071018 0%, var(--bg) 100%);
            color: var(--text);
            font-family: "Barlow", sans-serif;
        }
        .block-container {
            max-width: 1240px;
            padding-top: 1.2rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d1822 0%, #0a141d 100%);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] * {
            color: var(--text);
        }
        [data-testid="stSidebar"] label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
        }
        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }
        .brand-mark {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--accent) 0%, #ff905f 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            box-shadow: 0 14px 28px rgba(255, 107, 53, 0.25);
        }
        .brand-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
        }
        .brand-subtitle {
            color: var(--muted);
            font-size: 0.88rem;
        }
        .topbar-chip-row {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            justify-content: flex-end;
        }
        .topbar-chip {
            background: rgba(17, 32, 46, 0.88);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.5rem 0.75rem;
            font-size: 0.8rem;
            color: var(--muted);
        }
        .topbar-chip strong {
            color: var(--text);
        }
        .hero {
            background:
                linear-gradient(140deg, rgba(255, 107, 53, 0.95) 0%, rgba(255, 124, 74, 0.88) 35%, rgba(19, 36, 51, 0.97) 100%);
            color: white;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 30px;
            padding: 1.55rem 1.6rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }
        .hero::after {
            content: "";
            position: absolute;
            right: -40px;
            top: -40px;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.18), transparent 65%);
        }
        .hero-kicker {
            letter-spacing: 0.2em;
            font-size: 0.72rem;
            text-transform: uppercase;
            opacity: 0.84;
            margin-bottom: 0.4rem;
        }
        .hero-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2.7rem;
            line-height: 0.95;
            font-weight: 800;
            margin-bottom: 0.65rem;
            max-width: 720px;
            position: relative;
            z-index: 1;
        }
        .hero-subtitle {
            color: rgba(255, 247, 241, 0.9);
            max-width: 690px;
            font-size: 1rem;
            position: relative;
            z-index: 1;
        }
        .hero-meta {
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin-top: 1rem;
            position: relative;
            z-index: 1;
        }
        .hero-meta-card {
            background: rgba(8, 16, 24, 0.24);
            border: 1px solid rgba(255,255,255,0.12);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: 0.75rem 0.9rem;
            min-width: 148px;
        }
        .hero-meta-label {
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.7);
        }
        .hero-meta-value {
            font-size: 1.2rem;
            font-weight: 800;
            margin-top: 0.15rem;
        }
        .strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 0.9rem 0 1.4rem;
        }
        .metric-card, .match-card, .news-card, .surface-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1rem;
            box-shadow: var(--shadow);
        }
        .metric-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            color: var(--muted);
            letter-spacing: 0.1em;
        }
        .metric-value {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2rem;
            font-weight: 800;
            margin-top: 0.3rem;
        }
        .metric-note {
            color: var(--muted);
            font-size: 0.88rem;
            margin-top: 0.2rem;
        }
        .section-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.1rem;
            font-weight: 800;
            margin: 0.2rem 0 0.9rem;
            letter-spacing: -0.02em;
        }
        .subsection-label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.11em;
            font-size: 0.74rem;
            margin: 0.15rem 0 0.55rem;
        }
        .match-grid {
            display: grid;
            gap: 0.9rem;
        }
        .match-card {
            padding: 1.05rem;
            background: linear-gradient(180deg, rgba(18, 35, 49, 0.98), rgba(11, 23, 33, 0.98));
        }
        .match-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .badge {
            display: inline-block;
            padding: 0.32rem 0.6rem;
            border-radius: 999px;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.12em;
        }
        .badge-live {
            background: rgba(255, 107, 53, 0.14);
            color: #ffad8b;
        }
        .badge-ft {
            background: rgba(35, 193, 107, 0.14);
            color: #83f0af;
        }
        .badge-upcoming, .badge-ht {
            background: rgba(255, 176, 32, 0.14);
            color: #ffd370;
        }
        .teams-row {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            gap: 0.55rem;
        }
        .team-block {
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }
        .team-block.away {
            justify-content: flex-end;
            text-align: right;
        }
        .team-badge {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            object-fit: contain;
            padding: 0.35rem;
            flex: 0 0 auto;
        }
        .team-badge-fallback {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            border-radius: 14px;
            background: linear-gradient(135deg, #193243 0%, #274a61 100%);
            color: white;
            font-size: 0.95rem;
            font-weight: 800;
        }
        .team {
            font-size: 1.04rem;
            font-weight: 700;
        }
        .team-meta {
            color: var(--muted);
            font-size: 0.8rem;
            margin-top: 0.1rem;
        }
        .score-stack {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .score {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2.35rem;
            font-weight: 900;
            min-width: 110px;
            text-align: center;
            letter-spacing: -0.04em;
        }
        .score-sub {
            color: var(--muted);
            font-size: 0.76rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        .meta {
            margin-top: 0.95rem;
            color: var(--muted);
            font-size: 0.82rem;
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            border-top: 1px solid rgba(255,255,255,0.06);
            padding-top: 0.8rem;
        }
        .pill-row {
            display: flex;
            gap: 0.35rem;
            margin-top: 0.85rem;
            flex-wrap: wrap;
        }
        .pill {
            min-width: 28px;
            height: 28px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 800;
            color: white;
            padding: 0 0.5rem;
        }
        .pill-w { background: #177245; }
        .pill-d { background: #55677a; }
        .pill-l { background: #b5382e; }
        .detail-card {
            background: linear-gradient(180deg, rgba(19, 36, 51, 0.98), rgba(10, 20, 29, 0.98));
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1.15rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow);
        }
        .detail-vs {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 0.75rem;
            align-items: center;
            margin-top: 0.75rem;
        }
        .detail-team {
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }
        .detail-team.away {
            justify-content: flex-end;
        }
        .detail-team-name {
            font-size: 1rem;
            font-weight: 700;
        }
        .detail-team.away .detail-team-name {
            text-align: right;
        }
        .detail-score {
            font-family: "Space Grotesk", sans-serif;
            font-size: 2.7rem;
            font-weight: 900;
            text-align: center;
            line-height: 1;
        }
        .timeline-event {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.7rem 0.2rem;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            font-size: 0.93rem;
        }
        .timeline-event:last-child {
            border-bottom: none;
        }
        .timeline-minute {
            color: var(--accent-dark);
            font-weight: 700;
            min-width: 52px;
        }
        .timeline-summary {
            color: var(--text);
            text-align: right;
        }
        .stats-grid {
            display: grid;
            gap: 0.65rem;
        }
        .stat-row {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 0.75rem 0.85rem;
        }
        .stat-head {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            font-size: 0.84rem;
            margin-bottom: 0.45rem;
        }
        .stat-label {
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .stat-values {
            color: var(--text);
            font-weight: 700;
        }
        .stat-bar {
            position: relative;
            height: 8px;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            overflow: hidden;
        }
        .stat-home {
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            background: linear-gradient(90deg, var(--accent), #ff955f);
        }
        .stat-away {
            position: absolute;
            right: 0;
            top: 0;
            bottom: 0;
            background: linear-gradient(90deg, #2bc8ff, #6be0ff);
        }
        .news-card h4 {
            margin: 0 0 0.35rem;
            font-size: 1rem;
            font-family: "Space Grotesk", sans-serif;
        }
        .news-card p {
            margin: 0;
            color: var(--muted);
            font-size: 0.9rem;
        }
        .api-note {
            background: rgba(255, 107, 53, 0.1);
            border: 1px solid rgba(255, 107, 53, 0.2);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            color: var(--muted);
            margin-bottom: 1rem;
        }
        div[data-testid="stDataFrame"] div[role="table"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--line);
            background: rgba(15, 29, 41, 0.92);
        }
        @media (max-width: 900px) {
            .topbar {
                flex-direction: column;
                align-items: flex-start;
            }
            .strip {
                grid-template-columns: 1fr 1fr;
            }
            .hero-title {
                font-size: 2.05rem;
            }
            .teams-row, .detail-vs {
                grid-template-columns: 1fr;
            }
            .team-block.away, .detail-team.away {
                justify-content: flex-start;
                text-align: left;
            }
            .timeline-summary {
                text-align: left;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_class(status: str) -> str:
    return {
        "LIVE": "badge-live",
        "FT": "badge-ft",
        "HT": "badge-ht",
        "UPCOMING": "badge-upcoming",
    }.get(status, "badge-upcoming")


def normalize_status(raw: str | None) -> tuple[str, str]:
    mapping = {
        "FT": ("FT", "Finale"),
        "AET": ("FT", "DTS"),
        "FT_PEN": ("FT", "Rigori"),
        "POST": ("UPCOMING", "Posticipata"),
        "NS": ("UPCOMING", "Pre"),
        "HT": ("HT", "Intervallo"),
        "1H": ("LIVE", "1T"),
        "2H": ("LIVE", "2T"),
        "ET": ("LIVE", "ET"),
        "BT": ("LIVE", "Pausa"),
    }
    if raw in mapping:
        return mapping[raw]
    if raw and raw.startswith("P"):
        return "LIVE", raw
    return "UPCOMING", "Pre"


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def season_for_today() -> str:
    now = datetime.now(UTC)
    year = now.year
    if now.month >= 7:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


@st.cache_data(ttl=300, show_spinner=False)
def fetch_json(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params)
    url = f"{API_BASE_URL}/{API_KEY}/{endpoint}?{query}"
    with urlopen(url, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_or_none(endpoint: str, params: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return fetch_json(endpoint, params)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    raw_status = event.get("strStatus")
    status, minute = normalize_status(raw_status)
    home_score = safe_int(event.get("intHomeScore"))
    away_score = safe_int(event.get("intAwayScore"))
    kickoff = event.get("strTimeLocal") or event.get("strTime") or "--:--"
    return {
        "id": event.get("idEvent") or f"event-{event.get('strEvent', 'unknown')}",
        "kickoff": kickoff[:5],
        "status": status,
        "minute": minute,
        "home": event.get("strHomeTeam", "Home"),
        "away": event.get("strAwayTeam", "Away"),
        "score": (home_score, away_score),
        "venue": event.get("strVenue") or "Venue TBD",
        "competition": event.get("strLeague") or "Serie A",
        "events": [],
        "stats": {"Possesso": ("-", "-"), "Tiri": ("-", "-"), "xG": ("-", "-")},
        "form": ("-", "-", "-", "-", "-"),
        "round": event.get("intRound"),
        "date": event.get("dateEvent"),
    }


@st.cache_data(ttl=300, show_spinner=False)
def load_match_detail(event_id: str) -> dict[str, Any]:
    timeline_data = fetch_or_none("lookuptimeline.php", {"id": event_id}) or {}
    stats_data = fetch_or_none("lookupeventstats.php", {"id": event_id}) or {}

    timeline_rows = timeline_data.get("timeline") or timeline_data.get("events") or []
    stats_rows = stats_data.get("statistics") or stats_data.get("eventstats") or []

    timeline = []
    for row in timeline_rows[:12]:
        minute = row.get("intTime") or row.get("strTime") or row.get("strMinute") or "?"
        side = row.get("strHome") or row.get("strTeam") or row.get("strSide") or ""
        label = row.get("strEvent") or row.get("strStat") or row.get("strPlayer") or "Evento"
        detail = row.get("strPlayer") or row.get("strDetail") or row.get("strDescription") or ""
        summary = f"{side} • {label}".strip(" •")
        if detail and detail not in summary:
            summary = f"{summary} • {detail}"
        timeline.append((f"{minute}'" if str(minute).isdigit() else str(minute), summary))

    stats: dict[str, tuple[str, str]] = {}
    for row in stats_rows:
        label = row.get("strStat") or row.get("strType")
        if not label:
            continue
        home_value = row.get("strHome") or row.get("intHome") or row.get("strValueHome") or "-"
        away_value = row.get("strAway") or row.get("intAway") or row.get("strValueAway") or "-"
        stats[str(label)] = (str(home_value), str(away_value))

    return {"timeline": timeline, "stats": stats}


def build_table_from_rows(rows: list[dict[str, Any]] | None) -> list[dict[str, int | str]]:
    if not rows:
        return [
            {
                "#": idx,
                "Squadra": team,
                "PG": played,
                "Pt": pts,
                "V": wins,
                "N": draws,
                "P": losses,
                "GF": goals_for,
                "GS": goals_against,
                "Diff": goals_for - goals_against,
            }
            for idx, (team, played, pts, wins, draws, losses, goals_for, goals_against) in enumerate(
                FALLBACK_STANDINGS, start=1
            )
        ]

    table = []
    for idx, row in enumerate(rows, start=1):
        goals_for = safe_int(row.get("intGoalsFor"))
        goals_against = safe_int(row.get("intGoalsAgainst"))
        table.append(
            {
                "#": idx,
                "Squadra": row.get("strTeam", "Team"),
                "PG": safe_int(row.get("intPlayed")),
                "Pt": safe_int(row.get("intPoints")),
                "V": safe_int(row.get("intWin")),
                "N": safe_int(row.get("intDraw")),
                "P": safe_int(row.get("intLoss")),
                "GF": goals_for,
                "GS": goals_against,
                "Diff": goals_for - goals_against,
            }
        )
    return table


def form_markup(form: tuple[str, ...]) -> str:
    cells = []
    for result in form:
        css = result.lower()
        if css not in {"w", "d", "l"}:
            css = "d"
            result = "-"
        cells.append(f"<span class='pill pill-{css}'>{result}</span>")
    return "<div class='pill-row'>" + "".join(cells) + "</div>"


def team_badge_markup(team: str, team_badges: dict[str, str]) -> str:
    badge_url = team_badges.get(team)
    if badge_url:
        return f'<img class="team-badge" src="{badge_url}" alt="{team} badge" />'
    initials = "".join(part[0] for part in team.split()[:2]).upper()[:2]
    return f'<span class="team-badge-fallback">{initials}</span>'


def parse_ratio(value: str) -> float | None:
    if value in {"-", ""}:
        return None
    cleaned = str(value).replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def stat_rows_markup(stat_values: dict[str, tuple[str, str]]) -> str:
    rows = []
    for label, values in list(stat_values.items())[:4]:
        home_raw, away_raw = values
        home = parse_ratio(home_raw)
        away = parse_ratio(away_raw)
        if home is not None and away is not None and (home + away) > 0:
            home_width = max(12.0, round((home / (home + away)) * 100, 1))
            away_width = max(12.0, round((away / (home + away)) * 100, 1))
        else:
            home_width = away_width = 50.0
        rows.append(
            f"""
            <div class="stat-row">
              <div class="stat-head">
                <span class="stat-label">{label}</span>
                <span class="stat-values">{home_raw} | {away_raw}</span>
              </div>
              <div class="stat-bar">
                <span class="stat-home" style="width:{home_width}%;"></span>
                <span class="stat-away" style="width:{away_width}%;"></span>
              </div>
            </div>
            """
        )
    return "<div class='stats-grid'>" + "".join(rows) + "</div>"


def match_card(match: dict[str, Any], team_badges: dict[str, str]) -> str:
    home_score, away_score = match["score"]
    score = f"{home_score} - {away_score}" if match["status"] != "UPCOMING" else match["kickoff"]
    round_label = f"Giornata {match['round']}" if match.get("round") else match["competition"]
    score_sub = "live" if match["status"] in {"LIVE", "HT"} else ("kickoff" if match["status"] == "UPCOMING" else "finale")
    return f"""
    <div class="match-card">
      <div class="match-top">
        <div>
          <div class="metric-label">{round_label}</div>
          <div class="metric-note">{match["minute"]}</div>
        </div>
        <span class="badge {status_class(match["status"])}">{match["status"]}</span>
      </div>
      <div class="teams-row">
        <div class="team-block">
          {team_badge_markup(match["home"], team_badges)}
          <div>
            <div class="team">{match["home"]}</div>
            <div class="team-meta">Casa</div>
          </div>
        </div>
        <div class="score-stack">
          <div class="score">{score}</div>
          <div class="score-sub">{score_sub}</div>
        </div>
        <div class="team-block away">
          <div>
            <div class="team">{match["away"]}</div>
            <div class="team-meta">Trasferta</div>
          </div>
          {team_badge_markup(match["away"], team_badges)}
        </div>
      </div>
      <div class="meta">
        <span>{match["venue"]}</span>
        <span>{match.get("date") or ""}</span>
      </div>
      {form_markup(match["form"])}
    </div>
    """


@st.cache_data(ttl=300, show_spinner=False)
def load_real_data() -> dict[str, Any]:
    season = season_for_today()
    league_info = fetch_or_none("lookupleague.php", {"id": SERIE_A_LEAGUE_ID})
    if league_info:
        leagues = league_info.get("leagues") or []
        if leagues and leagues[0].get("strCurrentSeason"):
            season = leagues[0]["strCurrentSeason"]

    next_events = fetch_or_none("eventsnextleague.php", {"id": SERIE_A_LEAGUE_ID}) or {}
    past_events = fetch_or_none("eventspastleague.php", {"id": SERIE_A_LEAGUE_ID}) or {}
    table_data = fetch_or_none("lookuptable.php", {"l": SERIE_A_LEAGUE_ID, "s": season}) or {}
    teams_data = fetch_or_none("search_all_teams.php", {"l": "Italian_Serie_A"}) or {}

    team_badges = {
        team.get("strTeam"): team.get("strBadge")
        for team in (teams_data.get("teams") or [])
        if team.get("strTeam")
    }

    matches = []
    for event in (past_events.get("events") or [])[:10]:
        matches.append(normalize_event(event))
    for event in (next_events.get("events") or [])[:10]:
        matches.append(normalize_event(event))

    matches.sort(
        key=lambda match: (
            (match["status"] != "LIVE"),
            (match["status"] != "HT"),
            match.get("date") or "",
            match["kickoff"],
        )
    )

    standings_rows = table_data.get("table")
    standings = build_table_from_rows(standings_rows)

    scorer_candidates = []
    if standings_rows:
        for row in standings_rows[:5]:
            scorer_candidates.append(
                (
                    row.get("strTopScorer") or row.get("strPlayer") or row.get("strTeam", "Team"),
                    row.get("strTeam", "Serie A"),
                    safe_int(row.get("intPoints")),
                )
            )

    if not scorer_candidates:
        scorer_candidates = FALLBACK_SCORERS

    current_round = None
    league_name = "Serie A"
    if league_info and league_info.get("leagues"):
        league = league_info["leagues"][0]
        league_name = league.get("strLeague") or league_name
        current_round = league.get("intCurrentRound")

    return {
        "season": season,
        "league_name": league_name,
        "current_round": current_round,
        "matches": matches or FALLBACK_MATCHES,
        "standings": standings,
        "team_badges": team_badges,
        "scorers": scorer_candidates[:5],
        "api_ok": bool(matches and standings_rows),
    }


def main() -> None:
    st.set_page_config(page_title="Serie A LiveScore", page_icon="⚽", layout="wide")
    inject_css()

    data = load_real_data()
    matches = data["matches"]
    standings = data["standings"]
    team_badges = data["team_badges"]

    live_count = sum(1 for match in matches if match["status"] == "LIVE")
    completed_count = sum(1 for match in matches if match["status"] == "FT")
    teams = sorted({match["home"] for match in matches} | {match["away"] for match in matches})
    next_match = next((match for match in matches if match["status"] == "UPCOMING"), None)
    live_match = next((match for match in matches if match["status"] in {"LIVE", "HT"}), None)

    st.markdown(
        f"""
        <div class="topbar">
          <div class="brand-lockup">
            <div class="brand-mark">A</div>
            <div>
              <div class="brand-title">Serie A Scoreboard</div>
              <div class="brand-subtitle">Interfaccia rifatta per sembrare un vero score center sportivo.</div>
            </div>
          </div>
          <div class="topbar-chip-row">
            <div class="topbar-chip">Season <strong>{data["season"]}</strong></div>
            <div class="topbar-chip">Round <strong>{data["current_round"] or "Current"}</strong></div>
            <div class="topbar-chip">API <strong>{"Live" if data["api_ok"] else "Fallback"}</strong></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">Live Center</div>
          <div class="hero-title">{data["league_name"]} Matchday Hub</div>
          <div class="hero-subtitle">
            Risultati e calendario reali via TheSportsDB per la stagione {data["season"]}.
            Se imposti <code>THESPORTSDB_API_KEY</code>, l'app usa quella chiave; altrimenti prova con la chiave free pubblica.
          </div>
          <div class="hero-meta">
            <div class="hero-meta-card">
              <div class="hero-meta-label">Match live</div>
              <div class="hero-meta-value">{live_count}</div>
            </div>
            <div class="hero-meta-card">
              <div class="hero-meta-label">Top live game</div>
              <div class="hero-meta-value">{f"{live_match['home']} vs {live_match['away']}" if live_match else "Nessuna live"}</div>
            </div>
            <div class="hero-meta-card">
              <div class="hero-meta-label">Next kickoff</div>
              <div class="hero-meta-value">{f"{next_match['home']} - {next_match['away']}" if next_match else "Calendario completo"}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not data["api_ok"]:
        st.markdown(
            """
            <div class="api-note">
              Feed live non disponibile in questo momento. L'interfaccia resta attiva con dati di fallback locali.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.sidebar:
        st.header("Filtri")
        selected_statuses = st.multiselect(
            "Stato partita",
            options=["LIVE", "HT", "FT", "UPCOMING"],
            default=["LIVE", "HT", "FT", "UPCOMING"],
        )
        selected_team = st.selectbox("Squadra", options=["Tutte"] + teams)
        round_label = f"{data['current_round']}ª giornata" if data["current_round"] else "Giornata corrente"
        st.caption(f"Stagione: {data['season']}")
        st.caption(f"Round: {round_label}")

    filtered_matches = [
        match
        for match in matches
        if match["status"] in selected_statuses
        and (selected_team == "Tutte" or selected_team in {match["home"], match["away"]})
    ]

    goals_counter = Counter()
    for match in matches:
        for _, _, scorer in match["events"]:
            goals_counter[scorer] += 1
    top_live_scorer = goals_counter.most_common(1)[0][0] if goals_counter else "Serie A"

    st.markdown(
        f"""
        <div class="strip">
          <div class="metric-card">
            <div class="metric-label">Partite live</div>
            <div class="metric-value">{live_count}</div>
            <div class="metric-note">Estratte dal feed Serie A</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Partite concluse</div>
            <div class="metric-value">{completed_count}</div>
            <div class="metric-note">Ultimi risultati disponibili</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Gol nei match mostrati</div>
            <div class="metric-value">{sum(sum(match["score"]) for match in filtered_matches if match["status"] != "UPCOMING")}</div>
            <div class="metric-note">Conteggio sulla vista filtrata</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Focus</div>
            <div class="metric-value" style="font-size:1.25rem;">{top_live_scorer}</div>
            <div class="metric-note">Nome emerso dal centro partite</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scoreboard_col, detail_col = st.columns((1.22, 0.78), gap="large")

    with scoreboard_col:
        st.markdown("<div class='section-title'>Partite del Giorno / Ultimi Aggiornamenti</div>", unsafe_allow_html=True)
        if filtered_matches:
            st.markdown(
                "<div class='match-grid'>" + "".join(match_card(match, team_badges) for match in filtered_matches) + "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Nessuna partita corrisponde ai filtri selezionati.")

    with detail_col:
        st.markdown("<div class='section-title'>Match Detail</div>", unsafe_allow_html=True)
        selected_match = st.selectbox(
            "Apri partita",
            options=filtered_matches or matches,
            format_func=lambda match: f"{match['home']} vs {match['away']}",
        )
        detail = load_match_detail(str(selected_match["id"])) if not str(selected_match["id"]).startswith("fallback-") else {}
        home_score, away_score = selected_match["score"]
        st.markdown(
            f"""
            <div class="detail-card">
              <div class="metric-label">{selected_match["competition"]} • {selected_match["venue"]}</div>
              <div class="detail-vs">
                <div class="detail-team">
                  {team_badge_markup(selected_match["home"], team_badges)}
                  <div class="detail-team-name">{selected_match["home"]}</div>
                </div>
                <div class="detail-score">{home_score} - {away_score}</div>
                <div class="detail-team away">
                  <div class="detail-team-name">{selected_match["away"]}</div>
                  {team_badge_markup(selected_match["away"], team_badges)}
                </div>
              </div>
              <div class="metric-note" style="text-align:center; margin-top:0.7rem;">{selected_match["minute"]} • calcio d'inizio {selected_match["kickoff"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div class='subsection-label'>Timeline</div>", unsafe_allow_html=True)
        timeline = detail.get("timeline") or [(minute, f"{team} • {scorer}") for minute, team, scorer in selected_match["events"]]
        if timeline:
            timeline_markup = "".join(
                f"<div class='timeline-event'><span class='timeline-minute'>{minute}</span><span class='timeline-summary'>{summary}</span></div>"
                for minute, summary in timeline
            )
            st.markdown(f"<div class='surface-card'>{timeline_markup}</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                "<div class='surface-card'>Nessun evento dettagliato disponibile per questa partita.</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='subsection-label'>Statistiche</div>", unsafe_allow_html=True)
        stat_values = detail.get("stats") or selected_match["stats"]
        st.markdown(stat_rows_markup(stat_values), unsafe_allow_html=True)

    lower_left, lower_mid, lower_right = st.columns((1.15, 0.75, 0.8), gap="large")

    with lower_left:
        st.markdown("<div class='section-title'>Classifica</div>", unsafe_allow_html=True)
        st.dataframe(standings, hide_index=True, use_container_width=True)

    with lower_mid:
        st.markdown("<div class='section-title'>Leaders</div>", unsafe_allow_html=True)
        for idx, (label, team, value) in enumerate(data["scorers"], start=1):
            suffix = "pt" if isinstance(value, int) else value
            st.markdown(
                f"""
                <div class="news-card">
                  <h4>{idx}. {label}</h4>
                  <p>{team} • {suffix}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with lower_right:
        st.markdown("<div class='section-title'>Feed Status</div>", unsafe_allow_html=True)
        notes = [
            ("Provider", "TheSportsDB v1"),
            ("League ID", SERIE_A_LEAGUE_ID),
            ("Season", data["season"]),
            ("API Key", "custom" if API_KEY != "123" else "free public 123"),
        ]
        for headline, body in notes:
            st.markdown(
                f"""
                <div class="news-card">
                  <h4>{headline}</h4>
                  <p>{body}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
