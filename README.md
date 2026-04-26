# MindYourMoney 💸 – AI Financial Personality Analyzer

A Gen Z-style AI-powered financial personality quiz. 12 spicy questions → one brutally honest profile.

## Project Structure

```
MindYourMoney/
├── app.py           ← Flask backend (scoring engine + API)
├── index.html       ← Frontend entry point
├── style.css        ← Dark neon UI styles
├── script.js        ← Quiz engine + API calls + animations
└── requirements.txt
```

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## How it Works

### Backend (`app.py`)
- **`GET /questions`** — Returns 12 quiz questions (without score weights exposed to client)
- **`POST /analyze`** — Accepts `{ "answers": [0,2,1,...] }` (12 option indices), returns full personality profile

### Scoring Engine
Each answer maps to **weighted trait deltas** across 4 dimensions:
| Trait | Description |
|-------|-------------|
| 🔐 Saver | Tendency to save and protect wealth |
| 💳 Spender | Tendency to spend freely |
| 🎲 Risk Taker | Tolerance for financial risk |
| 📐 Planner | Preference for structured planning |

### Personality Types
| Type | Dominant Trait |
|------|---------------|
| The Vault Keeper | Saver |
| The Dopamine Spender | Spender |
| The Chaos Gambler | Risk Taker |
| The Strategic Architect | Planner |
| The Balanced Operator | Balanced (all traits within 15%) |

### Behavior Patterns
- **High Default Risk** — High spender + high risk tolerance
- **Financially Stable** — High saver + strong planner
- **Calculated Achiever** — Risk taker + strong planner
- **Chaotic Neutral** — Mixed signals

### Confidence Score
Calculated from the dominance gap between the top two traits. Higher gap = higher model confidence in the classification.

---

## Frontend Features
- Particle background animation
- Glassmorphism card UI (dark + neon)
- Animated question transitions (slide in/out)
- Progress bar + dot trail
- AI analyzing loading sequence with animated orb
- Confidence score ring animation
- Animated trait percentage bars
- Fully mobile responsive
