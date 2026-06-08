"""
app.py — Football Foul Fest: Gradio Blocks frontend.

The main application tying together foul_engine, tactics, and tournament
into a streaming match simulation UI with Setup and Live Match tabs.
"""

import time
import random
import copy
import re
import gradio as gr

# Load .env file for local development (on HF Spaces, secrets are set as env vars directly)
from dotenv import load_dotenv
load_dotenv()

from foul_engine import (
    get_default_teams, create_custom_team, create_match,
    pick_active_player, resolve_action, apply_event,
    is_major_event, get_top_fouler, format_clock,
    EventType, MatchEvent, Team,
)
from tactics import (
    get_actions, get_minor_commentary, get_major_commentary,
    get_post_match_report, TACTIC_MODIFIERS,
)
from tournament import (
    create_tournament, get_current_matchup, record_result,
    is_finished, format_bracket_display, format_history,
    get_round_label, MatchResult, Tournament,
)


# ---------------------------------------------------------------------------
# CSS Theme
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

/* ===== DESIGN SYSTEM: Aggressive Broadcast ===== */
:root {
    --surface: #131313;
    --surface-container: #1c1b1b;
    --surface-container-high: #2a2a2a;
    --on-surface: #e5e2e1;
    --on-surface-variant: #e6bdb8;
    --primary: #dc2626;
    --primary-dim: #991b1b;
    --on-primary: #fff;
    --secondary: #facc15;
    --divider: #262626;
    --text-body: #d1d5db;
    --text-muted: #6b7280;
}

* { font-family: 'Inter', sans-serif !important; }

.gradio-container {
    background: var(--surface) !important;
    color: var(--on-surface) !important;
    max-width: 1280px !important;
}

/* ===== TOP HEADER ===== */
.top-header {
    background: #0a0a0a;
    border-bottom: 4px solid var(--primary);
    padding: 20px 24px;
    text-align: center;
}
.top-header h1 {
    color: var(--primary);
    font-size: 40px;
    font-weight: 900;
    margin: 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.top-header .subtitle {
    color: var(--text-muted);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 6px;
}

/* ===== TABS ===== */
.tabs > .tab-nav > button {
    color: var(--text-body) !important;
    background: var(--surface-container) !important;
    border: 1px solid var(--divider) !important;
    border-radius: 4px 4px 0 0 !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    font-size: 13px !important;
}
.tabs > .tab-nav > button.selected {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
    color: var(--on-primary) !important;
}

/* ===== TEAM SELECTOR CARD GRID ===== */
.team-selector .wrap {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 12px !important;
}
@media (max-width: 768px) {
    .team-selector .wrap {
        grid-template-columns: repeat(2, 1fr) !important;
    }
}
.team-selector label {
    background: #171717 !important;
    border: 1px solid var(--divider) !important;
    border-radius: 4px !important;
    padding: 16px 8px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    min-height: 110px !important;
}
.team-selector label:hover {
    border-color: var(--primary-dim) !important;
    background: var(--surface-container-high) !important;
}
.team-selector input[type="checkbox"] {
    display: none !important; /* Hide original checkboxes */
}
.team-selector label:has(input:checked) {
    border-color: var(--primary) !important;
    background: #220808 !important; /* Dark red background */
    box-shadow: inset 0 0 0 1px var(--primary) !important;
}
.team-selector label span {
    white-space: pre-line !important;
    display: block !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    color: var(--text-body) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin: 0 !important;
}
.team-selector label:has(input:checked) span {
    color: #fff !important;
}
/* Style the flag (first line) */
.team-selector label span::first-line {
    font-size: 32px !important;
    line-height: 1.5 !important;
}
.selection-counter {
    text-align: center;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 12px 0;
}

/* ===== BUTTONS ===== */
.start-btn button {
    background: var(--primary) !important;
    color: var(--on-primary) !important;
    font-size: 18px !important;
    font-weight: 900 !important;
    padding: 16px 48px !important;
    border: none !important;
    border-radius: 4px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
}
.start-btn button:hover { background: var(--primary-dim) !important; }

.create-btn button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dim) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 14px 28px !important;
    transition: transform 0.15s ease, filter 0.15s ease !important;
    width: 100% !important;
}
.create-btn button:hover {
    filter: brightness(1.15) !important;
    transform: translateY(-1px) !important;
}
.create-btn button:active {
    transform: translateY(1px) !important;
}

.advance-btn button {
    background: transparent !important;
    color: var(--secondary) !important;
    border: 2px solid var(--secondary) !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
    padding: 16px !important;
}
.advance-btn button:hover { background: rgba(250, 204, 21, 0.1) !important; }

/* ===== PANELS ===== */
.dark-panel {
    background: #171717 !important;
    border: 1px solid var(--divider) !important;
    border-radius: 8px !important;
    padding: 24px !important;
}

/* ===== SECTION BADGE HEADERS ===== */
.section-header-container {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--divider);
}
.section-badge {
    background: var(--secondary);
    color: #000;
    font-weight: 900;
    font-size: 13px;
    padding: 2px 8px;
    border-radius: 2px;
}
.section-title {
    color: var(--on-surface);
    font-weight: 900;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ===== COMMENTARY FEED ===== */
.commentary-feed {
    max-height: 450px;
    overflow-y: auto;
    scroll-behavior: smooth;
    background: #0a0a0a;
    border: 1px solid var(--divider);
    border-radius: 4px;
    padding: 16px;
}
.commentary-feed::-webkit-scrollbar { width: 4px; }
.commentary-feed::-webkit-scrollbar-track { background: #0a0a0a; }
.commentary-feed::-webkit-scrollbar-thumb { background: var(--primary-dim); border-radius: 2px; }

/* ===== INCIDENT CARDS ===== */
.incident-card {
    background: #171717;
    border: 1px solid var(--divider);
    border-radius: 4px;
    margin-bottom: 12px;
    display: flex;
    overflow: hidden;
}
.incident-minute {
    background: #1c1b1b;
    color: var(--secondary);
    font-weight: 900;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 60px;
    flex-shrink: 0;
    border-right: 1px solid var(--divider);
}
.incident-content {
    padding: 12px 16px;
    flex-grow: 1;
}
.incident-title {
    font-weight: 800;
    font-size: 12px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.incident-desc {
    font-style: italic;
    font-size: 14px;
    color: var(--text-body);
    line-height: 1.5;
}

/* ===== STATS TABLE ===== */
.stats-table { width: 100%; border-collapse: collapse; }
.stats-table th {
    color: var(--secondary);
    padding: 12px 8px;
    border-bottom: 1px solid var(--divider);
    text-align: center;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 11px;
}
.stats-table td {
    padding: 12px 8px;
    text-align: center;
    border-bottom: 1px solid var(--divider);
    color: var(--text-body);
    font-size: 13px;
}
.stats-table td:first-child {
    text-align: left;
    color: var(--text-muted);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 11px;
}

/* ===== SCOREBOARD ===== */
.scoreboard {
    background: #0a0a0a;
    border: 1px solid var(--divider);
    border-radius: 4px;
    padding: 24px;
    text-align: center;
}
.score-big {
    font-size: 40px;
    font-weight: 900;
    color: var(--secondary);
    letter-spacing: -0.02em;
}
.team-name-display {
    font-size: 16px;
    font-weight: 800;
    color: var(--on-surface);
    text-transform: uppercase;
    letter-spacing: 0.025em;
}
.live-badge {
    background: var(--primary);
    color: white;
    padding: 2px 8px;
    border-radius: 0;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    animation: pulse-live 1.5s infinite;
}
@keyframes pulse-live {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ===== BRACKET ===== */
.bracket-layout {
    display: flex;
    gap: 24px;
    justify-content: space-between;
    overflow-x: auto;
    padding: 16px 0;
}
.bracket-column {
    flex: 1;
    min-width: 250px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.bracket-column-header {
    font-size: 12px;
    font-weight: 800;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 2px solid var(--divider);
    padding-bottom: 8px;
    text-align: center;
}
.bracket-matchups {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    flex-grow: 1;
    gap: 16px;
}
.bracket-match {
    background: #171717;
    border: 1px solid var(--divider);
    border-radius: 4px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    position: relative;
}
.bracket-match.live {
    border-color: var(--primary);
    box-shadow: 0 0 10px rgba(220, 38, 38, 0.2);
}
.bracket-match.live::after {
    content: "LIVE";
    position: absolute;
    top: -8px;
    right: 8px;
    background: var(--primary);
    color: white;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 6px;
    letter-spacing: 0.05em;
    border-radius: 2px;
}
.bracket-team {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    color: var(--text-body);
}
.bracket-team.winner {
    font-weight: 700;
    color: var(--on-surface);
}
.bracket-team.winner span {
    color: var(--on-surface);
}
.bracket-team.loser {
    color: var(--text-muted);
    text-decoration: line-through;
}
.bracket-team.loser span {
    color: var(--text-muted);
}
.bracket-team .score {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    color: var(--secondary);
}
.bracket-team.loser .score {
    color: var(--text-muted);
}

/* ===== HISTORY ===== */
.history-log {
    background: #0a0a0a;
    border: 1px solid var(--divider);
    border-radius: 4px;
    padding: 12px 16px;
    font-size: 13px;
    line-height: 1.8;
}

/* ===== CHAMPION ===== */
.champion-banner {
    background: #0a0a0a;
    border: 2px solid var(--secondary);
    border-radius: 4px;
    padding: 32px;
    text-align: center;
    animation: champion-glow 2s infinite;
}
@keyframes champion-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(250, 204, 21, 0.2); }
    50% { box-shadow: 0 0 40px rgba(250, 204, 21, 0.4); }
}

/* ===== POST-MATCH REPORT ===== */
.post-report {
    background: #171717;
    border-left: 4px solid var(--primary);
    border-radius: 0;
    padding: 16px 20px;
    font-style: italic;
    color: var(--text-body);
    line-height: 1.6;
}

/* ===== FOOTER BRANDING ===== */
.footer-branding {
    margin-top: 40px;
    padding: 24px;
    border-top: 1px solid var(--divider);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ===== INPUTS & DROPDOWNS ===== */
.dark-panel input, .dark-panel textarea, .dark-panel select {
    background: #0e0e0e !important;
    border: 1px solid #2d2d2d !important;
    border-radius: 6px !important;
    color: var(--on-surface) !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
}
.dark-panel input:focus, .dark-panel textarea:focus, .dark-panel select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2) !important;
}
.dark-panel .dropdown-container {
    background: #0e0e0e !important;
    border: 1px solid #2d2d2d !important;
    border-radius: 6px !important;
}
.dark-panel .dropdown-container:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2) !important;
}

/* ===== ALERT BOXES ===== */
.alert-box {
    padding: 12px 18px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: block;
    margin-top: 12px;
    width: 100%;
    text-align: center;
    box-sizing: border-box;
}
.alert-box.error {
    background: rgba(220, 38, 38, 0.1) !important;
    border: 1px solid var(--primary) !important;
    color: #ff8b8b !important;
}
.alert-box.success {
    background: rgba(34, 197, 94, 0.1) !important;
    border: 1px solid #22c55e !important;
    color: #a7f3d0 !important;
}
"""




# ---------------------------------------------------------------------------
# HTML builder functions
# ---------------------------------------------------------------------------

def build_scoreboard_html(home_name, home_emoji, away_name, away_emoji,
                          h_score, a_score, minute, top_home, top_away,
                          is_live=True, round_label=""):
    """Build the live scoreboard HTML."""
    clock = format_clock(minute)
    live_html = '<span class="live-badge">🔴 LIVE</span>' if is_live else '<span style="color:#6b7280;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">FULL TIME</span>'
    round_html = f'<div style="color:#6b7280;font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px;">{round_label}</div>' if round_label else ''

    return f"""
    <div class="scoreboard">
        {round_html}
        <div style="display:flex;justify-content:center;align-items:center;gap:40px;">
            <div style="text-align:center;">
                <div style="font-size:2.5em;">{home_emoji}</div>
                <div class="team-name-display">{home_name}</div>
                <div style="color:#6b7280;font-size:12px;margin-top:4px;font-weight:700;">⭐ {top_home or '—'}</div>
            </div>
            <div>
                <div class="score-big">{h_score} — {a_score}</div>
                <div style="color:#6b7280;margin-top:8px;font-size:12px;font-weight:700;letter-spacing:0.05em;">⏱ {clock}  {live_html}</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:2.5em;">{away_emoji}</div>
                <div class="team-name-display">{away_name}</div>
                <div style="color:#6b7280;font-size:12px;margin-top:4px;font-weight:700;">⭐ {top_away or '—'}</div>
            </div>
        </div>
    </div>
    """


def build_commentary_html(commentary_log):
    """Build the commentary feed HTML from a list of logs."""
    if not commentary_log:
        return '<div class="commentary-feed" style="color:#6b7280;text-align:center;padding:24px;">Waiting for kickoff...</div>'

    cards_html = []
    for item in commentary_log:
        if isinstance(item, dict):
            minute = item.get("minute", 0)
            etype = item.get("event_type", EventType.REGULAR_FOUL)
            team_name = item.get("team_name", "")
            team_emoji = item.get("team_emoji", "")
            player = item.get("player", "")
            text = item.get("text", "")
        else:
            # Fallback for tuple (text, etype)
            text, etype = item
            minute = 0
            # Try to parse minute from text using regex
            match = re.match(r"^(\d+)'\s*(.*)$", text)
            if match:
                minute = int(match.group(1))
                text = match.group(2)
            team_name = ""
            team_emoji = ""
            player = ""

        # Parse out the minute prefix if it's still in the text
        clean_text = text
        match = re.match(r"^(\d+)'\s*(.*)$", text)
        if match:
            minute_parsed, clean_text = match.groups()
            minute = int(minute_parsed)

        # Set title, border, and title color based on EventType
        border_color = "#262626"
        title_color = "var(--text-body)"
        title = "INCIDENT"

        if etype == EventType.YELLOW_CARD:
            border_color = "#facc15"
            title_color = "#facc15"
            title = "YELLOW CARD 🟨"
        elif etype == EventType.DIVE_FAILED:
            border_color = "#facc15"
            title_color = "#facc15"
            title = "SIMULATION 🟨"
        elif etype == EventType.RED_CARD:
            border_color = "#dc2626"
            title_color = "#dc2626"
            title = "RED CARD 🟥"
        elif etype == EventType.VIOLENT_CONDUCT:
            border_color = "#991b1b"
            title_color = "#ff2020"
            title = "VIOLENT CONDUCT 🔴"
        elif etype in (EventType.DIVE_SUCCESS, EventType.PENALTY_CONCEDED):
            border_color = "#ffe083"
            title_color = "#ffe083"
            title = "PENALTY WON 🎭"
        elif etype == EventType.REGULAR_FOUL:
            border_color = "#5c403c"
            title_color = "var(--text-body)"
            title = "FOUL"
        elif etype == EventType.KICK_OFF:
            border_color = "#444"
            title_color = "var(--text-muted)"
            title = "KICK OFF ⏱️"
        elif etype == EventType.HALF_TIME:
            border_color = "#444"
            title_color = "var(--text-muted)"
            title = "HALF TIME ⏱️"
        elif etype == EventType.FULL_TIME:
            border_color = "var(--secondary)"
            title_color = "var(--secondary)"
            title = "FULL TIME 🏆"

        # Append team and player details to title if present
        if player:
            team_str = f" ({team_emoji} {team_name})" if team_name else ""
            title = f"{title} — {player}{team_str}"

        cards_html.append(f"""
        <div class="incident-card" style="border-left: 4px solid {border_color};">
            <div class="incident-minute">{minute}'</div>
            <div class="incident-content">
                <div class="incident-title" style="color:{title_color};">{title}</div>
                <div class="incident-desc">{clean_text}</div>
            </div>
        </div>
        """)

    content = "\n".join(cards_html)
    return f"""
    <div class="commentary-feed" id="commentary-feed">
        {content}
    </div>
    """



def build_stats_html(home_name, home_emoji, away_name, away_emoji, h_stats, a_stats):
    """Build the match statistics table HTML."""
    rows = [
        ("Foul Points", h_stats.foul_points, a_stats.foul_points),
        ("Regular Fouls", h_stats.regular_fouls, a_stats.regular_fouls),
        ("Yellow Cards 🟨", h_stats.yellow_cards, a_stats.yellow_cards),
        ("Red Cards 🟥", h_stats.red_cards, a_stats.red_cards),
        ("Penalties", h_stats.penalties_conceded, a_stats.penalties_conceded),
        ("Violent Conduct", h_stats.violent_conduct, a_stats.violent_conduct),
        ("Dives", h_stats.dives, a_stats.dives),
    ]

    rows_html = ""
    for label, h_val, a_val in rows:
        h_style = "color:#ff2020;font-weight:700;" if h_val > a_val else ""
        a_style = "color:#ff2020;font-weight:700;" if a_val > h_val else ""
        rows_html += f"""
        <tr>
            <td>{label}</td>
            <td style="{h_style}">{h_val}</td>
            <td style="{a_style}">{a_val}</td>
        </tr>"""

    return f"""
    <table class="stats-table">
        <thead>
            <tr>
                <th></th>
                <th>{home_emoji} {home_name}</th>
                <th>{away_name} {away_emoji}</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """


def get_winner_info(results, idx):
    """Get the winner's emoji and name from a round result list at idx."""
    if idx < len(results):
        r = results[idx]
        emoji = r.home_emoji if r.winner == r.home else r.away_emoji
        return emoji, r.winner
    return None


def build_bracket_html(t):
    """Build the bracket display from the tournament state."""
    if t is None:
        return '<div class="bracket-container" style="color:#888;text-align:center;padding:24px;">Tournament not started. Select 8 teams on the Setup tab to begin!</div>'

    # Quarter Finals column
    qf_html = ""
    for i in range(4):
        home, away = t.qf_matchups[i]
        res = t.qf_results[i] if i < len(t.qf_results) else None
        is_live = (t.current_round == "QF" and t.current_match_idx == i)
        
        home_class, away_class = "", ""
        home_score, away_score = "—", "—"
        match_class = "bracket-match"
        if is_live:
            match_class += " live"
        
        if res:
            home_score, away_score = res.home_score, res.away_score
            if res.winner == home.name:
                home_class, away_class = "winner", "loser"
            else:
                home_class, away_class = "loser", "winner"
                
        qf_html += f"""
        <div class="{match_class}">
            <div class="bracket-team {home_class}">
                <span>{home.emoji} {home.name}</span>
                <span class="score">{home_score}</span>
            </div>
            <div class="bracket-team {away_class}">
                <span>{away.emoji} {away.name}</span>
                <span class="score">{away_score}</span>
            </div>
        </div>
        """

    # Semi Finals column
    sf_html = ""
    for i in range(2):
        res = t.sf_results[i] if i < len(t.sf_results) else None
        is_live = (t.current_round == "SF" and t.current_match_idx == i)
        
        match_class = "bracket-match"
        if is_live:
            match_class += " live"
            
        # Determine team info
        if i < len(t.sf_matchups):
            home, away = t.sf_matchups[i]
            home_name, home_emoji = home.name, home.emoji
            away_name, away_emoji = away.name, away.emoji
        else:
            # Project from QF
            qf_w1 = get_winner_info(t.qf_results, i*2)
            qf_w2 = get_winner_info(t.qf_results, i*2 + 1)
            home_emoji, home_name = qf_w1 if qf_w1 else ("⏳", f"Winner QF{i*2+1}")
            away_emoji, away_name = qf_w2 if qf_w2 else ("⏳", f"Winner QF{i*2+2}")
            
        home_class, away_class = "", ""
        home_score, away_score = "—", "—"
        if res:
            home_score, away_score = res.home_score, res.away_score
            if res.winner == home_name:
                home_class, away_class = "winner", "loser"
            else:
                home_class, away_class = "loser", "winner"
                
        sf_html += f"""
        <div class="{match_class}">
            <div class="bracket-team {home_class}">
                <span>{home_emoji} {home_name}</span>
                <span class="score">{home_score}</span>
            </div>
            <div class="bracket-team {away_class}">
                <span>{away_emoji} {away_name}</span>
                <span class="score">{away_score}</span>
            </div>
        </div>
        """

    # Final column
    final_html = ""
    res = t.final_result
    is_live = (t.current_round == "Final")
    match_class = "bracket-match"
    if is_live:
        match_class += " live"
        
    if t.final_matchup:
        home, away = t.final_matchup[0]
        home_name, home_emoji = home.name, home.emoji
        away_name, away_emoji = away.name, away.emoji
    else:
        sf_w1 = get_winner_info(t.sf_results, 0)
        sf_w2 = get_winner_info(t.sf_results, 1)
        home_emoji, home_name = sf_w1 if sf_w1 else ("⏳", "Winner SF1")
        away_emoji, away_name = sf_w2 if sf_w2 else ("⏳", "Winner SF2")
        
    home_class, away_class = "", ""
    home_score, away_score = "—", "—"
    if res:
        home_score, away_score = res.home_score, res.away_score
        if res.winner == home_name:
            home_class, away_class = "winner", "loser"
        else:
            home_class, away_class = "loser", "winner"
            
    final_html += f"""
    <div class="{match_class}">
        <div class="bracket-team {home_class}">
            <span>{home_emoji} {home_name}</span>
            <span class="score">{home_score}</span>
        </div>
        <div class="bracket-team {away_class}">
            <span>{away_emoji} {away_name}</span>
            <span class="score">{away_score}</span>
        </div>
    </div>
    """

    return f"""
    <div class="bracket-layout">
        <div class="bracket-column">
            <div class="bracket-column-header">Quarter Finals</div>
            <div class="bracket-matchups">{qf_html}</div>
        </div>
        <div class="bracket-column">
            <div class="bracket-column-header">Semi Finals</div>
            <div class="bracket-matchups">{sf_html}</div>
        </div>
        <div class="bracket-column">
            <div class="bracket-column-header">Final</div>
            <div class="bracket-matchups">{final_html}</div>
        </div>
    </div>
    """


def build_history_html(t):
    """Build the tournament history log."""
    if t is None:
        return '<div class="history-log" style="color:#888;">No matches played yet.</div>'
    entries = format_history(t)
    if not entries:
        return '<div class="history-log" style="color:#888;">No matches played yet.</div>'
    lines = "<br>".join(entries)
    return f'<div class="history-log">{lines}</div>'


def build_report_html(report_text):
    """Build the post-match report HTML."""
    if not report_text:
        return ""
    return f'<div class="post-report">{report_text}</div>'


def build_champion_html(t):
    """Build the champion celebration banner."""
    if t is None or not t.champion:
        return ""
    return f"""
    <div class="champion-banner">
        <div style="font-size:3em;">🏆</div>
        <div style="font-size:32px;font-weight:900;color:#facc15;margin:12px 0;text-transform:uppercase;letter-spacing:0.025em;">
            FOOTBALL FOUL FEST CHAMPION
        </div>
        <div style="font-size:2.5em;">{t.champion_emoji} {t.champion}</div>
        <div style="color:#6b7280;margin-top:8px;font-style:italic;font-size:14px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;">
            The dirtiest team in the world
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Possession logic
# ---------------------------------------------------------------------------

def pick_possession(state):
    """Pick which team has possession this tick. Slight bias toward trailing team."""
    rng = state.rng
    if state.home_score > state.away_score:
        return state.away if rng.random() < 0.55 else state.home
    elif state.away_score > state.home_score:
        return state.home if rng.random() < 0.55 else state.away
    else:
        return state.home if rng.random() < 0.5 else state.away


# ---------------------------------------------------------------------------
# Tiebreaker (no extra time)
# ---------------------------------------------------------------------------

def determine_winner(state):
    """Determine the winner when scores are tied.
    Tiebreaker order: violent conduct count → red cards → coin flip."""
    if state.home_score != state.away_score:
        return state.home if state.home_score > state.away_score else state.away

    # Tied — use tiebreakers
    if state.home_stats.violent_conduct != state.away_stats.violent_conduct:
        return state.home if state.home_stats.violent_conduct > state.away_stats.violent_conduct else state.away
    if state.home_stats.red_cards != state.away_stats.red_cards:
        return state.home if state.home_stats.red_cards > state.away_stats.red_cards else state.away
    # Coin flip
    return state.home if state.rng.random() < 0.5 else state.away


# ---------------------------------------------------------------------------
# Game loop generator
# ---------------------------------------------------------------------------

def run_match(tournament_state_val):
    """Generator: simulates one full match, yielding UI updates each tick.

    Each yield produces a tuple of:
      (scoreboard_html, commentary_html, stats_html, report_html,
       advance_btn_update, bracket_html, history_html, champion_html)
    """
    t = tournament_state_val
    if t is None or is_finished(t):
        yield (
            "", "", "", "",
            gr.update(visible=False), build_bracket_html(t),
            build_history_html(t), build_champion_html(t),
        )
        return

    matchup = get_current_matchup(t)
    if matchup is None:
        yield (
            "", "", "", "",
            gr.update(visible=False), build_bracket_html(t),
            build_history_html(t), build_champion_html(t),
        )
        return

    # Deep-copy teams so card state doesn't pollute the tournament bracket
    home_orig, away_orig = matchup
    home = copy.deepcopy(home_orig)
    away = copy.deepcopy(away_orig)

    round_label = get_round_label(t)
    state = create_match(home, away)
    commentary_log = []  # list of dicts

    # Helper to yield current UI state
    def ui_snapshot(is_live=True, report="", show_advance=False):
        top_h = get_top_fouler(home.name, state.events)
        top_a = get_top_fouler(away.name, state.events)
        return (
            build_scoreboard_html(
                home.name, home.emoji, away.name, away.emoji,
                state.home_score, state.away_score, state.minute,
                top_h, top_a, is_live=is_live, round_label=round_label
            ),
            build_commentary_html(commentary_log),
            build_stats_html(home.name, home.emoji, away.name, away.emoji,
                             state.home_stats, state.away_stats),
            build_report_html(report),
            gr.update(visible=show_advance),
            build_bracket_html(t),
            build_history_html(t),
            "",  # champion html (not yet)
        )

    # --- Kick Off ---
    state.half = "first"
    state.minute = 0
    ko_text = get_minor_commentary(0, EventType.KICK_OFF, home.name, "", state.rng)
    commentary_log.append({
        "minute": 0,
        "event_type": EventType.KICK_OFF,
        "team_name": home.name,
        "team_emoji": home.emoji,
        "player": "",
        "text": ko_text
    })
    yield ui_snapshot()
    time.sleep(1)

    # --- First Half: 15 ticks × 3 sec = 45 seconds, maps to minutes 0-45 ---
    foul_count = 0  # Track minor fouls to only show every other one
    for tick in range(15):
        state.minute = int(tick * 45 / 15)
        team = pick_possession(state)

        # One action per tick — keeps commentary readable
        actions = get_actions(
            team.name, state.minute,
            state.home_score, state.away_score,
            team.tactic, state.rng
        )
        action = actions[0]  # Use the first action only

        player = pick_active_player(team, state.rng)
        if player is not None:
            events = resolve_action(state, team, action, player)
            for event in events:
                apply_event(state, event)
                # Only show commentary for major events or every-other minor foul
                if is_major_event(event.event_type):
                    line = get_major_commentary(
                        state.minute, event.event_type,
                        event.team, event.player, state.rng
                    )
                    commentary_log.append({
                        "minute": state.minute,
                        "event_type": event.event_type,
                        "team_name": event.team,
                        "team_emoji": home.emoji if event.team == home.name else away.emoji,
                        "player": event.player,
                        "text": line
                    })
                else:
                    foul_count += 1
                    if foul_count % 2 == 1:  # Show odd-numbered minor fouls
                        line = get_minor_commentary(
                            state.minute, event.event_type,
                            event.team, event.player, state.rng
                        )
                        commentary_log.append({
                            "minute": state.minute,
                            "event_type": event.event_type,
                            "team_name": event.team,
                            "team_emoji": home.emoji if event.team == home.name else away.emoji,
                            "player": event.player,
                            "text": line
                        })

        yield ui_snapshot()
        time.sleep(3)

    # --- Half Time ---
    state.half = "halftime"
    state.minute = 45
    ht_text = get_minor_commentary(45, EventType.HALF_TIME, "", "", state.rng)
    commentary_log.append({
        "minute": 45,
        "event_type": EventType.HALF_TIME,
        "team_name": "",
        "team_emoji": "",
        "player": "",
        "text": ht_text
    })
    yield ui_snapshot()
    time.sleep(5)

    # --- Second Half: 15 ticks × 3 sec = 45 seconds, maps to minutes 45-90 ---
    state.half = "second"
    for tick in range(15):
        state.minute = 45 + int(tick * 45 / 15)
        team = pick_possession(state)

        actions = get_actions(
            team.name, state.minute,
            state.home_score, state.away_score,
            team.tactic, state.rng
        )
        action = actions[0]

        player = pick_active_player(team, state.rng)
        if player is not None:
            events = resolve_action(state, team, action, player)
            for event in events:
                apply_event(state, event)
                if is_major_event(event.event_type):
                    line = get_major_commentary(
                        state.minute, event.event_type,
                        event.team, event.player, state.rng
                    )
                    commentary_log.append({
                        "minute": state.minute,
                        "event_type": event.event_type,
                        "team_name": event.team,
                        "team_emoji": home.emoji if event.team == home.name else away.emoji,
                        "player": event.player,
                        "text": line
                    })
                else:
                    foul_count += 1
                    if foul_count % 2 == 1:
                        line = get_minor_commentary(
                            state.minute, event.event_type,
                            event.team, event.player, state.rng
                        )
                        commentary_log.append({
                            "minute": state.minute,
                            "event_type": event.event_type,
                            "team_name": event.team,
                            "team_emoji": home.emoji if event.team == home.name else away.emoji,
                            "player": event.player,
                            "text": line
                        })

        yield ui_snapshot()
        time.sleep(3)

    # --- Full Time ---
    state.half = "finished"
    state.minute = 90
    ft_text = get_minor_commentary(90, EventType.FULL_TIME, "", "", state.rng)
    commentary_log.append({
        "minute": 90,
        "event_type": EventType.FULL_TIME,
        "team_name": "",
        "team_emoji": "",
        "player": "",
        "text": ft_text
    })

    # Determine winner (tiebreaker if tied)
    winner = determine_winner(state)
    loser = away if winner.name == home.name else home

    # Record result in tournament
    result = MatchResult(
        home=home.name, away=away.name,
        home_emoji=home.emoji, away_emoji=away.emoji,
        home_score=state.home_score, away_score=state.away_score,
        winner=winner.name,
    )
    record_result(t, result)

    # Tiebreaker commentary
    if state.home_score == state.away_score:
        tb_text = (
            f"90' TIED AT {state.home_score}-{state.away_score}! "
            f"{winner.name} wins on the Dirty Conduct tiebreaker! "
            f"The team with more violence progresses!"
        )
        commentary_log.append({
            "minute": 90,
            "event_type": EventType.FULL_TIME,
            "team_name": winner.name,
            "team_emoji": winner.emoji,
            "player": "",
            "text": tb_text
        })

    # Post-match report
    top_fouler = get_top_fouler(winner.name, state.events) or winner.name
    report = get_post_match_report(
        home.name, away.name,
        state.home_score, state.away_score,
        winner.name, top_fouler, state.rng
    )

    # Final yield with report and advance button
    top_h = get_top_fouler(home.name, state.events)
    top_a = get_top_fouler(away.name, state.events)

    yield (
        build_scoreboard_html(
            home.name, home.emoji, away.name, away.emoji,
            state.home_score, state.away_score, 90,
            top_h, top_a, is_live=False, round_label=round_label
        ),
        build_commentary_html(commentary_log),
        build_stats_html(home.name, home.emoji, away.name, away.emoji,
                         state.home_stats, state.away_stats),
        build_report_html(report),
        gr.update(visible=True),
        build_bracket_html(t),
        build_history_html(t),
        build_champion_html(t),
    )


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def on_create_team(name, p1, p2, p3, tactic, all_teams_val):
    """Create a custom team and add it to the selectable pool."""
    teams = list(all_teams_val) if all_teams_val else get_default_teams()

    if not name or not name.strip():
        return teams, gr.update(), '<div class="alert-box error">❌ Team name is required.</div>'
    if not all([p1, p2, p3]):
        return teams, gr.update(), '<div class="alert-box error">❌ All 3 player names are required.</div>'

    # Check for duplicate name
    if any(t.name.lower() == name.strip().lower() for t in teams):
        return teams, gr.update(), f'<div class="alert-box error">❌ Team \'{name.strip()}\' already exists.</div>'

    custom = create_custom_team(
        name=name.strip(),
        emoji="🏴",
        player_names=[p1.strip(), p2.strip(), p3.strip()],
        tactic=tactic,
    )
    teams.append(custom)

    # Update checkbox choices with newline format for grid cards
    choices = [f"{t.emoji}\n{t.name}" for t in teams]
    return teams, gr.update(choices=choices), f'<div class="alert-box success">✅ {custom.emoji} {custom.name} added!</div>'


def on_start_tournament(selected_labels, all_teams_val):
    """Validate selection and create the tournament."""
    teams = list(all_teams_val) if all_teams_val else get_default_teams()

    if not selected_labels or len(selected_labels) != 8:
        count = len(selected_labels) if selected_labels else 0
        return (
            None,
            gr.update(selected=0),  # Stay on Setup tab
            "", "", "", "", "",
            gr.update(visible=False),
            f"❌ Select exactly 8 teams. You selected {count}.",
        )

    # Map labels (which now contain a newline) back to Team objects
    label_to_team = {f"{t.emoji}\n{t.name}": t for t in teams}
    selected_teams = []
    for label in selected_labels:
        team = label_to_team.get(label)
        if team:
            # Deep copy so each tournament gets fresh player state
            selected_teams.append(copy.deepcopy(team))

    if len(selected_teams) != 8:
        return (
            None,
            gr.update(selected=0),
            "", "", "", "", "",
            gr.update(visible=False),
            "❌ Could not find all selected teams. Try again.",
        )

    # Shuffle for random bracket seeding
    random.shuffle(selected_teams)
    t = create_tournament(selected_teams)

    return (
        t,
        gr.update(selected=1),  # Switch to Live Match tab
        build_bracket_html(t),
        build_history_html(t),
        "",  # scoreboard (will be filled by run_match)
        "",  # commentary
        "",  # stats
        gr.update(visible=False), # Target post_match_row
        "✅ Tournament started! Switching to Live Match...",
    )


def on_advance(tournament_state_val):
    """Triggered by the Advance button — resets UI for next match or shows champion."""
    t = tournament_state_val
    if t is None:
        return (t, "", "", "", "", "", gr.update(visible=False), "")

    if is_finished(t):
        return (
            t,
            build_bracket_html(t), build_history_html(t),
            "", "", "",
            gr.update(visible=False),
            build_champion_html(t),
        )

    # Clear UI for next match
    return (
        t,
        build_bracket_html(t), build_history_html(t),
        "", "", "",
        gr.update(visible=False), # Target post_match_row
        "",
    )


# ---------------------------------------------------------------------------
# Gradio Blocks layout
# ---------------------------------------------------------------------------

def create_app():
    default_teams = get_default_teams()
    default_choices = [f"{t.emoji}\n{t.name}" for t in default_teams]

    head_js = """
    <script>
      (function() {
        const observer = new MutationObserver((mutations) => {
          const feed = document.getElementById('commentary-feed');
          if (feed) {
            window.requestAnimationFrame(() => {
              feed.scrollTop = feed.scrollHeight;
            });
          }
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });
      })();
    </script>
    """
    with gr.Blocks(title="Football Foul Fest", css=CUSTOM_CSS, head=head_js) as demo:

        # --- State ---
        tournament_state = gr.State(None)
        all_teams_state = gr.State(default_teams)

        # --- Header ---
        gr.HTML("""
        <div class="top-header">
            <h1>⚽ FOOTBALL FOUL FEST 🏆</h1>
            <div class="subtitle">The dirtiest tournament in football. Cards are points. Fouls are glory.</div>
        </div>
        """)

        with gr.Tabs() as tabs:

            # ============================================================
            # TAB 1: SETUP
            # ============================================================
            with gr.Tab("⚙️ Setup", id=0):
                with gr.Column(elem_classes=["dark-panel"]):

                    gr.HTML("""
                    <div class="section-header-container">
                        <span class="section-badge">01</span>
                        <span class="section-title">Select 8 Participating Teams</span>
                    </div>
                    """)

                    team_selector = gr.CheckboxGroup(
                        choices=default_choices,
                        label="",
                        elem_classes=["team-selector"],
                        interactive=True,
                    )

                    selection_counter = gr.HTML(
                        '<div class="selection-counter" style="color:#888;font-style:italic;">'
                        'Select exactly 8 teams. The dirtiest nation wins. (0/8 selected)</div>'
                    )

                    gr.HTML('<hr style="border-color:#333;margin:16px 0;">')

                    gr.HTML("""
                    <div class="section-header-container">
                        <span class="section-badge">02</span>
                        <span class="section-title">Custom Team Creator</span>
                    </div>
                    """)

                    with gr.Row():
                        team_name_input = gr.Textbox(
                            label="Team Name",
                            placeholder="e.g. The Barbarians",
                            scale=3
                        )
                        tactic_dropdown = gr.Dropdown(
                            choices=list(TACTIC_MODIFIERS.keys()),
                            value="The Chopper",
                            label="Tactic",
                            scale=2
                        )

                    gr.HTML("""
                    <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; margin: 16px 0 8px 0; border-bottom: 1px dashed #262626; padding-bottom: 4px;">
                        Squad Players (3 required)
                    </div>
                    """)

                    with gr.Row():
                        p1_input = gr.Textbox(label="Player 1", placeholder="e.g. Bone Crusher")
                        p2_input = gr.Textbox(label="Player 2", placeholder="e.g. The Ankle Breaker")
                        p3_input = gr.Textbox(label="Player 3", placeholder="e.g. Iron Lung")

                    with gr.Row():
                        create_btn = gr.Button("⚡ Create & Add Team", elem_classes=["create-btn"])

                    status_msg = gr.HTML("")
                    gr.HTML('<div style="height:20px;"></div>')

                    start_btn = gr.Button(
                        "🏆 START FOOTBALL FOUL FEST",
                        elem_classes=["start-btn"],
                    )
                    start_status = gr.HTML("")

            # ============================================================
            # TAB 2: LIVE MATCH
            # ============================================================
            with gr.Tab("⚽ Live Match", id=1):

                gr.HTML("""
                <div class="section-header-container">
                    <span class="section-badge">03</span>
                    <span class="section-title">Foul Fest Bracket</span>
                </div>
                """)
                bracket_html = gr.HTML(build_bracket_html(None))

                gr.HTML("""
                <div class="section-header-container" style="margin-top:16px;">
                    <span class="section-badge">04</span>
                    <span class="section-title">Tournament History</span>
                </div>
                """)
                history_html = gr.HTML(build_history_html(None))

                gr.HTML('<div style="height:12px;"></div>')
                scoreboard_html = gr.HTML("")

                gr.HTML('<div style="height:12px;"></div>')
                with gr.Row():
                    with gr.Column(scale=3):
                        gr.HTML("""
                        <div class="section-header-container">
                            <span class="section-badge">05</span>
                            <span class="section-title">Live Commentary</span>
                        </div>
                        """)
                        commentary_html = gr.HTML("")
                    with gr.Column(scale=2):
                        gr.HTML("""
                        <div class="section-header-container">
                            <span class="section-badge">06</span>
                            <span class="section-title">Match Statistics</span>
                        </div>
                        """)
                        stats_html = gr.HTML("")

                # Post-match side-by-side elements
                with gr.Row(visible=False) as post_match_row:
                    with gr.Column(scale=3):
                        report_html = gr.HTML("")
                    with gr.Column(scale=1, min_width=180):
                        advance_btn = gr.Button(
                            "⚡ Advance →",
                            elem_classes=["advance-btn"],
                        )

                champion_html = gr.HTML("")

        # Footer Branding Bar
        gr.HTML("""
        <div class="footer-branding">
            <span>FOOTBALL FOUL FEST &copy; 2026</span>
            <span>CARDS ARE POINTS • FOULS ARE GLORY</span>
        </div>
        """)

        # ============================================================
        # EVENT WIRING
        # ============================================================

        # Limit team selection to 8 and show counter
        def on_selection_change(selected):
            count = len(selected) if selected else 0
            if count <= 8:
                if count == 8:
                    color = "#00cc00"
                    msg = "✅ 8/8 selected — Ready to start!"
                else:
                    color = "#FFD700" if count > 0 else "#888"
                    msg = f"{count}/8 selected. Pick {8 - count} more."
                return selected, f'<div class="selection-counter" style="color:{color};">{msg}</div>'
            else:
                # More than 8 — trim back to first 8
                trimmed = selected[:8]
                return trimmed, '<div class="selection-counter" style="color:#ff2020;">⚠️ Maximum 8 teams! Extra selections removed.</div>'

        team_selector.change(
            fn=on_selection_change,
            inputs=[team_selector],
            outputs=[team_selector, selection_counter],
        )

        # Create custom team
        create_btn.click(
            fn=on_create_team,
            inputs=[team_name_input, p1_input, p2_input, p3_input,
                    tactic_dropdown, all_teams_state],
            outputs=[all_teams_state, team_selector, status_msg],
        )

        # Start tournament
        start_btn.click(
            fn=on_start_tournament,
            inputs=[team_selector, all_teams_state],
            outputs=[tournament_state, tabs, bracket_html, history_html,
                     scoreboard_html, commentary_html, stats_html,
                     post_match_row, start_status],
        ).then(
            fn=run_match,
            inputs=[tournament_state],
            outputs=[scoreboard_html, commentary_html, stats_html,
                     report_html, post_match_row, bracket_html,
                     history_html, champion_html],
        )

        # Advance to next match
        advance_btn.click(
            fn=on_advance,
            inputs=[tournament_state],
            outputs=[tournament_state, bracket_html, history_html,
                     scoreboard_html, commentary_html, stats_html,
                     post_match_row, champion_html],
        ).then(
            fn=run_match,
            inputs=[tournament_state],
            outputs=[scoreboard_html, commentary_html, stats_html,
                     report_html, post_match_row, bracket_html,
                     history_html, champion_html],
        )

    return demo


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo = create_app()
    demo.queue()
    demo.launch()
