---
title: Football Foul Fest
emoji: 🏆
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 5.33.0
python_version: '3.13'
app_file: app.py
pinned: false
short_description: A football tournament where players kick each other to win.
---

# ⚽ Football Foul Fest 🏆

🎥 [Watch the Demo Video](https://www.loom.com/share/c1d989c65ef840ed8f5d090ff3b447df) | [View the Launch Post](https://x.com/yeye70531274663/status/2064279662298067395?s=20)

An inverted football tournament where fouls, cards, and dirty play win matches — not goals. The dirtier you play, the higher your score.

## Scoring & Rules

| Event | Points |
|-------|--------|
| Regular Foul | +1 |
| Yellow Card | +3 |
| Red Card | +5 |
| Penalty Conceded | +2 |
| Violent Conduct | +7 |
| Clean Play | 0 (actual football sequence) |

> [!IMPORTANT]
> **Dirty Conduct Tiebreaker**: If scores are tied at full time (90'), the team with more violence progresses. The tiebreaker hierarchy is:
> 1. Most Violent Conduct events
> 2. Most Red Cards
> 3. Coin flip

## Team Tactics

Assign a specific playstyle to influence how a team behaves and what events they generate:
- **The Chopper**: Maximum fouls, no subtlety. Hack everything that moves.
- **The Diver**: Win penalties through theatrical diving. Every touch is agony.
- **The Intimidator**: Rack up cards deliberately. Fear is the weapon.
- **The Enforcer**: Target key opposition players and make them suffer.
- **The Time Waster**: Slow the game down, waste every second, and provoke the opposition.

## How to Play

1. **Setup** — Select 8 teams from the pool (or create your own with custom ratings)
2. **Start** — Click START FOOTBALL FOUL FEST
3. **Watch** — Matches simulate in real-time with sequential, pacing-controlled live commentary
4. **Advance** — After each match, click Advance to proceed through the tournament bracket
5. **Win** — The dirtiest team is crowned Football Foul Fest Champion

## How It Works

```
[Setup Pool] ──> [Match State (Time Seeded)]
                        │
                        ▼ (10 Ticks/Half Loop)
               [Pick Possession Team]
                        │
                        ▼
             [LLM AI Coach Action Choice] (FOUL, DIVE, PRESS, etc.)
                        │
                        ▼
             [Foul Engine Resolution Cascade] (e.g., Dive -> Yellow -> Red)
                        │
                        ▼
             [LLM Pundit Commentary] (Custom prompt with tone variation)
                        │
                        ▼
             [Sequential Streaming UI] (3s event intervals + 5s halftime)
```

1. **Deterministic Setup**: Matches are initialized with a time-based unique seed for repeatable engine rolls.
2. **Action Prompting**: The possession team calls the Modal LLM endpoint with their score, time, and custom tactic (e.g. *The Chopper*) to select the best dirty play actions.
3. **Engine Resolution**: Actions pass through the physics/probability engine where player attributes (aggression, cynicism, theatrics) roll for success, yellow/red cards, and injuries.
4. **Streaming Commentary**: As cascades resolve, they are pace-controlled and streamed to the UI. Genuinely violent or theatrical plays trigger a second LLM request to generate broadcast-style pundit commentary with funny/poetic/outraged tone variations.
5. **Post-Match Analysis**: At 90', the engine determines tiebreakers if necessary and generates a complete bespoke match recap using the Modal backend.

## Tech Stack

- **Frontend**: Gradio (runs on HF Spaces free CPU tier)
- **AI Backend**: Qwen2.5-14B-Instruct on Modal A100 GPU
- **Model**: ≤32B parameters (hackathon compliant)

