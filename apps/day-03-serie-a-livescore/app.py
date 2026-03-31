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
        :root {
            --bg: #f4f1e8;
            --card: #fffaf1;
            --line: #ded4c2;
            --text: #181613;
            --muted: #766d5e;
            --accent: #d74f2a;
            --accent-dark: #aa3418;
            --green: #177245;
            --amber: #d28b10;
        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(215, 79, 42, 0.12), transparent 22%),
                linear-gradient(180deg, #f8f4ea 0%, var(--bg) 100%);
            color: var(--text);
        }
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            background: linear-gradient(135deg, #181613 0%, #31271f 65%, #523827 100%);
            color: #fff6eb;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 1.4rem 1.5rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 24px 50px rgba(24, 22, 19, 0.18);
        }
        .hero-kicker {
            letter-spacing: 0.18em;
            font-size: 0.74rem;
            text-transform: uppercase;
            opacity: 0.78;
            margin-bottom: 0.4rem;
        }
        .hero-title {
            font-size: 2.3rem;
            line-height: 1;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        .hero-subtitle {
            color: #e7d8c6;
            max-width: 700px;
            font-size: 0.98rem;
        }
        .strip {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 1rem 0 1.4rem;
        }
        .metric-card, .match-card, .news-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem;
        }
        .metric-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            color: var(--muted);
            letter-spacing: 0.08em;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 800;
            margin-top: 0.3rem;
        }
        .metric-note {
            color: var(--muted);
            font-size: 0.85rem;
            margin-top: 0.2rem;
        }
        .section-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin: 0.4rem 0 0.9rem;
        }
        .match-grid {
            display: grid;
            gap: 0.9rem;
        }
        .match-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.85rem;
        }
        .badge {
            display: inline-block;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.08em;
        }
        .badge-live {
            background: rgba(215, 79, 42, 0.14);
            color: var(--accent-dark);
        }
        .badge-ft {
            background: rgba(23, 114, 69, 0.14);
            color: var(--green);
        }
        .badge-upcoming, .badge-ht {
            background: rgba(210, 139, 16, 0.16);
            color: var(--amber);
        }
        .teams-row {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            gap: 0.75rem;
        }
        .team {
            font-size: 1.02rem;
            font-weight: 700;
        }
        .team.away {
            text-align: right;
        }
        .score {
            font-size: 1.9rem;
            font-weight: 900;
            min-width: 92px;
            text-align: center;
        }
        .meta {
            margin-top: 0.8rem;
            color: var(--muted);
            font-size: 0.85rem;
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
        }
        .pill-row {
            display: flex;
            gap: 0.35rem;
            margin-top: 0.7rem;
            flex-wrap: wrap;
        }
        .pill {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 800;
            color: white;
        }
        .pill-w { background: #177245; }
        .pill-d { background: #8d806d; }
        .pill-l { background: #b5382e; }
        .detail-card {
            background: rgba(255,250,241,0.9);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1.1rem;
            margin-bottom: 1rem;
        }
        .detail-score {
            font-size: 2.5rem;
            font-weight: 900;
            text-align: center;
            margin: 0.4rem 0 0.2rem;
        }
        .timeline-event {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.55rem 0;
            border-bottom: 1px solid rgba(222, 212, 194, 0.7);
            font-size: 0.93rem;
        }
        .timeline-event:last-child {
            border-bottom: none;
        }
        .news-card h4 {
            margin: 0 0 0.35rem;
            font-size: 1rem;
        }
        .news-card p {
            margin: 0;
            color: var(--muted);
            font-size: 0.9rem;
        }
        .api-note {
            background: rgba(255, 250, 241, 0.78);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            color: var(--muted);
            margin-bottom: 1rem;
        }
        div[data-testid="stDataFrame"] div[role="table"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--line);
        }
        @media (max-width: 900px) {
            .strip {
                grid-template-columns: 1fr 1fr;
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


def match_card(match: dict[str, Any]) -> str:
    home_score, away_score = match["score"]
    score = f"{home_score} - {away_score}" if match["status"] != "UPCOMING" else match["kickoff"]
    round_label = f"Giornata {match['round']}" if match.get("round") else match["competition"]
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
        <div class="team">{match["home"]}</div>
        <div class="score">{score}</div>
        <div class="team away">{match["away"]}</div>
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

    matches.sort(key=lambda match: ((match["status"] != "LIVE"), (match["status"] != "HT"), match.get("date") or "", match["kickoff"]))

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

    live_count = sum(1 for match in matches if match["status"] == "LIVE")
    completed_count = sum(1 for match in matches if match["status"] == "FT")
    teams = sorted({match["home"] for match in matches} | {match["away"] for match in matches})

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">Live Center</div>
          <div class="hero-title">{data["league_name"]} Matchday Hub</div>
          <div class="hero-subtitle">
            Risultati e calendario reali via TheSportsDB per la stagione {data["season"]}.
            Se imposti <code>THESPORTSDB_API_KEY</code>, l'app usa quella chiave; altrimenti prova con la chiave free pubblica.
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

    scoreboard_col, detail_col = st.columns((1.2, 0.8), gap="large")

    with scoreboard_col:
        st.markdown("<div class='section-title'>Partite del Giorno / Ultimi Aggiornamenti</div>", unsafe_allow_html=True)
        if filtered_matches:
            st.markdown(
                "<div class='match-grid'>" + "".join(match_card(match) for match in filtered_matches) + "</div>",
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
              <div class="detail-score">{selected_match["home"]} {home_score} - {away_score} {selected_match["away"]}</div>
              <div class="metric-note" style="text-align:center;">{selected_match["minute"]} • calcio d'inizio {selected_match["kickoff"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Timeline")
        timeline = detail.get("timeline") or [(minute, f"{team} • {scorer}") for minute, team, scorer in selected_match["events"]]
        if timeline:
            for minute, summary in timeline:
                st.markdown(
                    f"<div class='timeline-event'><span>{minute}</span><span>{summary}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div class='detail-card'>Nessun evento dettagliato disponibile per questa partita.</div>",
                unsafe_allow_html=True,
            )

        st.caption("Statistiche")
        stat_values = detail.get("stats") or selected_match["stats"]
        stats_cols = st.columns(3)
        for idx, (label, values) in enumerate(list(stat_values.items())[:3]):
            stats_cols[idx].metric(label, f"{values[0]} | {values[1]}")

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
