---
title: Football Foul Fest
emoji: 🏆
colorFrom: red
colorTo: black
sdk: gradio
sdk_version: 5.33.0
python_version: '3.13'
app_file: app.py
pinned: false
short_description: A football tournament where players kick each other to win.
---

# ⚽ Football Foul Fest 🏆

An inverted football tournament where fouls, cards, and dirty play win matches — not goals. The dirtier you play, the higher your score.

## Scoring

| Event | Points |
|-------|--------|
| Regular Foul | +1 |
| Yellow Card | +3 |
| Red Card | +5 |
| Penalty Conceded | +2 |
| Violent Conduct | +7 |

## How to Play

1. **Setup** — Select 8 teams from the pool (or create your own)
2. **Start** — Click START FOOTBALL FOUL FEST
3. **Watch** — Matches simulate in real-time with live commentary
4. **Advance** — After each match, click Advance to proceed through the bracket
5. **Win** — The dirtiest team is crowned Football Foul Fest Champion

## Tech Stack

- **Frontend**: Gradio (runs on HF Spaces free CPU tier)
- **AI Backend**: Qwen2.5-7B-Instruct on Modal A10G GPU
- **Model**: ≤32B parameters (hackathon compliant)

