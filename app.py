from flask import Flask, request, jsonify, send_from_directory
import math
import os

app = Flask(__name__, static_folder=".")

# Allow requests from any origin (needed when frontend runs on a
# different port, e.g. VS Code Live Server on :5500)
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/analyze', methods=['OPTIONS'])
@app.route('/questions', methods=['OPTIONS'])
def options_handler():
    return '', 204

# ---------------------------------------------------------------------------
# Question definitions with weighted trait contributions
# ---------------------------------------------------------------------------
# Each answer option maps to a dict of trait deltas:
#   saver, spender, risk_taker, planner  (values can be negative)
QUESTIONS = [
    {
        "id": 1,
        "text": "Payday just hit. First move?",
        "options": [
            {"text": "Instantly split it across savings goals", "weights": {"saver": 4, "spender": 0, "risk_taker": 0, "planner": 3}},
            {"text": "Transfer rent/bills, spend the rest freely", "weights": {"saver": 1, "spender": 3, "risk_taker": 1, "planner": 1}},
            {"text": "Yolo into crypto before I think twice", "weights": {"saver": -1, "spender": 2, "risk_taker": 5, "planner": -1}},
            {"text": "Build a colour-coded budget spreadsheet", "weights": {"saver": 2, "spender": 0, "risk_taker": 0, "planner": 5}},
        ]
    },
    {
        "id": 2,
        "text": "A friend begs you to co-sign a loan for them. You:",
        "options": [
            {"text": "Hard no — my credit is sacred", "weights": {"saver": 3, "spender": 0, "risk_taker": -2, "planner": 3}},
            {"text": "Sure, they're my bestie!", "weights": {"saver": -1, "spender": 2, "risk_taker": 3, "planner": -1}},
            {"text": "Only after reviewing their finances thoroughly", "weights": {"saver": 2, "spender": 0, "risk_taker": 0, "planner": 4}},
            {"text": "What's a co-sign? Just Venmo me later", "weights": {"saver": -2, "spender": 3, "risk_taker": 2, "planner": -2}},
        ]
    },
    {
        "id": 3,
        "text": "You spot a 48-hour flash sale on something you've wanted for months:",
        "options": [
            {"text": "Buy immediately — this discount is fate", "weights": {"saver": -2, "spender": 5, "risk_taker": 1, "planner": -1}},
            {"text": "Check if it fits the monthly budget first", "weights": {"saver": 2, "spender": 1, "risk_taker": 0, "planner": 4}},
            {"text": "Skip it — I'm saving for something bigger", "weights": {"saver": 5, "spender": -2, "risk_taker": 0, "planner": 3}},
            {"text": "Put it on the credit card, figure it out later", "weights": {"saver": -3, "spender": 4, "risk_taker": 3, "planner": -2}},
        ]
    },
    {
        "id": 4,
        "text": "Your emergency fund should cover:",
        "options": [
            {"text": "6–12 months of expenses, minimum", "weights": {"saver": 5, "spender": -1, "risk_taker": -2, "planner": 5}},
            {"text": "1–2 months is plenty, life is short", "weights": {"saver": 1, "spender": 3, "risk_taker": 2, "planner": 0}},
            {"text": "Emergency? That's what credit cards are for", "weights": {"saver": -3, "spender": 4, "risk_taker": 4, "planner": -2}},
            {"text": "I have a detailed tiered emergency plan", "weights": {"saver": 3, "spender": 0, "risk_taker": -1, "planner": 5}},
        ]
    },
    {
        "id": 5,
        "text": "A hot stock tip lands in your group chat. You:",
        "options": [
            {"text": "Research it for weeks before deciding", "weights": {"saver": 2, "spender": 0, "risk_taker": 1, "planner": 5}},
            {"text": "Drop 30% of savings in immediately", "weights": {"saver": -3, "spender": 2, "risk_taker": 5, "planner": -1}},
            {"text": "Ignore it — index funds only", "weights": {"saver": 4, "spender": -1, "risk_taker": -3, "planner": 4}},
            {"text": "Invest a small 'fun money' slice only", "weights": {"saver": 2, "spender": 1, "risk_taker": 2, "planner": 3}},
        ]
    },
    {
        "id": 6,
        "text": "How do you feel about debt?",
        "options": [
            {"text": "Disgusting. Paid everything off ASAP.", "weights": {"saver": 5, "spender": -2, "risk_taker": -2, "planner": 3}},
            {"text": "Leverage is a tool — use it strategically", "weights": {"saver": 1, "spender": 1, "risk_taker": 3, "planner": 4}},
            {"text": "It's just part of life, whatever", "weights": {"saver": -1, "spender": 3, "risk_taker": 2, "planner": -1}},
            {"text": "Terrifying, I avoid it at all costs", "weights": {"saver": 4, "spender": -2, "risk_taker": -3, "planner": 2}},
        ]
    },
    {
        "id": 7,
        "text": "Your spending app shows you went 20% over budget last month. You:",
        "options": [
            {"text": "Immediately cut luxuries for the next 30 days", "weights": {"saver": 3, "spender": -1, "risk_taker": -1, "planner": 4}},
            {"text": "Adjust the budget to match reality ¯\\_(ツ)_/¯", "weights": {"saver": -2, "spender": 4, "risk_taker": 2, "planner": -1}},
            {"text": "Spiral into financial guilt for a week", "weights": {"saver": 1, "spender": 1, "risk_taker": 0, "planner": 1}},
            {"text": "Conduct a full audit and recalibrate plan", "weights": {"saver": 2, "spender": -1, "risk_taker": 0, "planner": 5}},
        ]
    },
    {
        "id": 8,
        "text": "You receive ₹50,000 unexpectedly. It goes to:",
        "options": [
            {"text": "High-yield savings, obviously", "weights": {"saver": 5, "spender": -1, "risk_taker": -1, "planner": 3}},
            {"text": "That vacation I've been delaying", "weights": {"saver": -2, "spender": 5, "risk_taker": 1, "planner": 0}},
            {"text": "Aggressive stock/crypto portfolio", "weights": {"saver": -1, "spender": 1, "risk_taker": 5, "planner": 1}},
            {"text": "Split: 40% invest, 40% save, 20% treat", "weights": {"saver": 3, "spender": 2, "risk_taker": 2, "planner": 5}},
        ]
    },
    {
        "id": 9,
        "text": "Retirement planning – where are you at?",
        "options": [
            {"text": "Maxing out every retirement account since age 22", "weights": {"saver": 5, "spender": -2, "risk_taker": 0, "planner": 5}},
            {"text": "I'll think about it when I'm older", "weights": {"saver": -2, "spender": 3, "risk_taker": 2, "planner": -3}},
            {"text": "My startup is my retirement plan 😎", "weights": {"saver": -1, "spender": 1, "risk_taker": 5, "planner": 1}},
            {"text": "I have a 20-year financial roadmap", "weights": {"saver": 3, "spender": -1, "risk_taker": 1, "planner": 5}},
        ]
    },
    {
        "id": 10,
        "text": "Your vibe when eating out with friends:",
        "options": [
            {"text": "Split exact amounts using an app", "weights": {"saver": 3, "spender": 0, "risk_taker": -1, "planner": 4}},
            {"text": "I'll get this one, you get next", "weights": {"saver": -1, "spender": 3, "risk_taker": 2, "planner": 0}},
            {"text": "I already budgeted ₹800 for dining this week", "weights": {"saver": 4, "spender": 0, "risk_taker": -1, "planner": 5}},
            {"text": "Order everything, we only live once", "weights": {"saver": -3, "spender": 5, "risk_taker": 2, "planner": -2}},
        ]
    },
    {
        "id": 11,
        "text": "Someone offers you a higher-paying but unstable job. You:",
        "options": [
            {"text": "Take it — calculated risk for the reward", "weights": {"saver": 1, "spender": 1, "risk_taker": 4, "planner": 3}},
            {"text": "Stay comfortable, stability > everything", "weights": {"saver": 3, "spender": 0, "risk_taker": -3, "planner": 2}},
            {"text": "Jump in immediately, burn that bridge later", "weights": {"saver": -2, "spender": 2, "risk_taker": 5, "planner": -2}},
            {"text": "Negotiate a trial period with a fallback plan", "weights": {"saver": 2, "spender": 0, "risk_taker": 2, "planner": 5}},
        ]
    },
    {
        "id": 12,
        "text": "Your honest relationship with budgeting apps:",
        "options": [
            {"text": "I built my own custom tracking system in Notion", "weights": {"saver": 3, "spender": -1, "risk_taker": 0, "planner": 5}},
            {"text": "Downloaded 4, used none", "weights": {"saver": -2, "spender": 3, "risk_taker": 1, "planner": -3}},
            {"text": "I use one religiously every single day", "weights": {"saver": 4, "spender": -2, "risk_taker": -1, "planner": 5}},
            {"text": "My bank balance IS my budget tracker", "weights": {"saver": -1, "spender": 4, "risk_taker": 2, "planner": -2}},
        ]
    },
]

# ---------------------------------------------------------------------------
# Personality profiles
# ---------------------------------------------------------------------------
PERSONALITIES = {
    "The Vault Keeper": {
        "dominant": "saver",
        "description": "You treat savings like oxygen — absolutely non-negotiable. Your friends think you're 'careful'. Your bank account thinks you're a legend. You probably have 7 savings buckets named things like 'Rainy Day', 'Rainy Week', and 'Nuclear Winter'.",
        "risk_level": "Low",
        "loan_advice": "You're a lender's dream. Excellent credit hygiene means you qualify for the best rates. Consider leveraging low-interest loans for wealth-building assets rather than hoarding cash earning 3.5% p.a.",
        "emoji": "🔐"
    },
    "The Dopamine Spender": {
        "dominant": "spender",
        "description": "Money was made to be spent, and you're fulfilling its destiny. You live in the present tense, financially speaking. Your Amazon wishlist has its own wishlist. The good news? You know how to enjoy life. The bad news? Your savings are shy.",
        "risk_level": "High",
        "loan_advice": "High spending patterns are a red flag for lenders. Before taking any loan, build 3 months of savings first. Automate savings transfers on payday — what you don't see, you don't spend.",
        "emoji": "💳"
    },
    "The Chaos Gambler": {
        "dominant": "risk_taker",
        "description": "You don't just accept risk — you DM it, take it to dinner, and introduce it to your parents. Volatility is your vibe. You've probably made and lost the same ₹10,000 three times this year. High risk, high reward... also high stress.",
        "risk_level": "Very High",
        "loan_advice": "Loan approval may be tricky with erratic financial behaviour. Lenders want predictability. Channel the risk energy into structured investments. Never use loan money for speculative assets — that's how stories end badly.",
        "emoji": "🎲"
    },
    "The Strategic Architect": {
        "dominant": "planner",
        "description": "You have a 5-year plan, a backup 5-year plan, and a plan for when the plans fail. Spreadsheets are your love language. You've probably already optimised your tax strategy for 2027. Slightly exhausting to your friends. Extremely impressive to your future self.",
        "risk_level": "Low to Medium",
        "loan_advice": "Your planning ability is a major asset for loan applications. You likely already have an excellent debt-to-income ratio. Consider structured loans for appreciating assets like real estate or education — your discipline will handle repayments with ease.",
        "emoji": "📐"
    },
    "The Balanced Operator": {
        "dominant": "balanced",
        "description": "You're the rarest type — someone who actually holds all four financial traits in reasonable tension. You save without being miserly, spend without guilt-spiralling, take calculated risks, and plan without paralysis. Financially, you're what therapists wish their other clients were.",
        "risk_level": "Medium",
        "loan_advice": "Your balanced approach is genuinely impressive. For loans, focus on purpose-driven borrowing — home, education, business. Your natural financial equilibrium means you can manage moderate leverage without stress.",
        "emoji": "⚖️"
    },
}

BEHAVIOR_PATTERNS = {
    "High Default Risk": {
        "condition": "high_spender_high_risk",
        "description": "⚠️ High spending + high risk tolerance = financial fragility. One unexpected expense away from a crisis.",
        "color": "danger"
    },
    "Financially Stable": {
        "condition": "high_saver_planner",
        "description": "✅ Strong saving habits paired with solid planning. You're building a fortress, not a house of cards.",
        "color": "success"
    },
    "Chaotic Neutral": {
        "condition": "mixed",
        "description": "🌀 Mixed signals across your financial personality. Unpredictable but adaptable — organized chaos.",
        "color": "warning"
    },
    "Calculated Achiever": {
        "condition": "risk_planner",
        "description": "🚀 Risk appetite guided by strategic thinking. You're not gambling — you're investing in conviction.",
        "color": "info"
    },
}

# ---------------------------------------------------------------------------
# Analysis logic
# ---------------------------------------------------------------------------

def calculate_scores(answers):
    """answers: list of option indices (0-3) for each question"""
    totals = {"saver": 0, "spender": 0, "risk_taker": 0, "planner": 0}
    for q_idx, ans_idx in enumerate(answers):
        if q_idx >= len(QUESTIONS):
            continue
        weights = QUESTIONS[q_idx]["options"][ans_idx]["weights"]
        for trait, val in weights.items():
            totals[trait] += val
    return totals


def normalize_scores(scores):
    """Convert raw scores to 0-100 percentages."""
    # Clamp negatives to 0 first
    clamped = {k: max(0, v) for k, v in scores.items()}
    total = sum(clamped.values())
    if total == 0:
        return {k: 25.0 for k in clamped}
    return {k: round((v / total) * 100, 1) for k, v in clamped.items()}


def detect_personality(scores, percentages):
    dominant = max(percentages, key=percentages.get)
    
    # Check if it's actually balanced
    values = list(percentages.values())
    max_v, min_v = max(values), min(values)
    spread = max_v - min_v
    
    if spread < 15:  # All traits within 15% of each other
        return "The Balanced Operator"
    
    mapping = {
        "saver": "The Vault Keeper",
        "spender": "The Dopamine Spender",
        "risk_taker": "The Chaos Gambler",
        "planner": "The Strategic Architect",
    }
    return mapping.get(dominant, "The Balanced Operator")


def detect_behavior_pattern(percentages):
    s = percentages["saver"]
    sp = percentages["spender"]
    r = percentages["risk_taker"]
    p = percentages["planner"]

    if sp >= 35 and r >= 30:
        return "High Default Risk"
    if s >= 35 and p >= 30:
        return "Financially Stable"
    if r >= 30 and p >= 30:
        return "Calculated Achiever"
    return "Chaotic Neutral"


def calculate_confidence(percentages):
    """Higher confidence when one trait clearly dominates."""
    values = sorted(percentages.values(), reverse=True)
    dominance_gap = values[0] - values[1]
    # Normalize: gap of 30+ = high confidence (~90%), gap of 5 = low (~50%)
    confidence = 50 + min(dominance_gap * 1.4, 45)
    return round(confidence, 1)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    answers = data.get("answers", [])

    if len(answers) != 12:
        return jsonify({"error": "Expected 12 answers"}), 400

    raw_scores = calculate_scores(answers)
    percentages = normalize_scores(raw_scores)
    personality_name = detect_personality(raw_scores, percentages)
    behavior_pattern = detect_behavior_pattern(percentages)
    confidence = calculate_confidence(percentages)

    profile = PERSONALITIES[personality_name]
    pattern_info = BEHAVIOR_PATTERNS[behavior_pattern]

    response = {
        "personality": personality_name,
        "emoji": profile["emoji"],
        "description": profile["description"],
        "risk_level": profile["risk_level"],
        "loan_advice": profile["loan_advice"],
        "trait_percentages": {
            "Saver": percentages["saver"],
            "Spender": percentages["spender"],
            "Risk Taker": percentages["risk_taker"],
            "Planner": percentages["planner"],
        },
        "behavior_pattern": behavior_pattern,
        "pattern_description": pattern_info["description"],
        "pattern_color": pattern_info["color"],
        "confidence_score": confidence,
        "raw_scores": raw_scores,
    }
    return jsonify(response)


@app.route("/questions", methods=["GET"])
def get_questions():
    safe = [
        {
            "id": q["id"],
            "text": q["text"],
            "options": [{"text": o["text"]} for o in q["options"]]
        }
        for q in QUESTIONS
    ]
    return jsonify(safe)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
