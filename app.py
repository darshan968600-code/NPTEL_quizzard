"""
NPTEL Quizzer - Local Flask Server
Runs on http://localhost:5000
"""

import json
import os
import random
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEEKLY_FILE = os.path.join(DATA_DIR, "weekly_questions.json")
PYQ_FILE = os.path.join(DATA_DIR, "pyq_questions.json")
REVIEW_FILE = os.path.join(DATA_DIR, "review_required.json")

# Load data into memory
weekly_questions = []
pyq_questions = []
review_required = []

if os.path.exists(WEEKLY_FILE):
    with open(WEEKLY_FILE, "r", encoding="utf-8") as f:
        weekly_questions = json.load(f)

if os.path.exists(PYQ_FILE):
    with open(PYQ_FILE, "r", encoding="utf-8") as f:
        pyq_questions = json.load(f)

if os.path.exists(REVIEW_FILE):
    with open(REVIEW_FILE, "r", encoding="utf-8") as f:
        review_required = json.load(f)


@app.route("/")
def home():
    # Build list of available weeks
    weeks_map = {}
    for q in weekly_questions:
        w = q["week"]
        if w not in weeks_map:
            weeks_map[w] = {
                "week": w,
                "label": f"Week {w}",
                "count": 0,
                "first_q": q.get("question", "")[:60] + "..."
            }
        weeks_map[w]["count"] += 1

    sorted_weeks = sorted(weeks_map.values(), key=lambda x: x["week"])
    total_pyqs = len(pyq_questions)
    total_weekly = len(weekly_questions)

    return render_template(
        "index.html",
        weeks=sorted_weeks,
        total_weekly=total_weekly,
        total_pyqs=total_pyqs,
        review_count=len(review_required)
    )


@app.route("/quiz")
def quiz():
    mode = request.args.get("mode", "weekly")
    week = request.args.get("week", "0")
    count = request.args.get("count", "50")
    return render_template("quiz.html", mode=mode, week=week, count=count)


# API Endpoints
@app.route("/api/summary")
def api_summary():
    weeks_available = sorted(list(set(q["week"] for q in weekly_questions)))
    return jsonify({
        "status": "success",
        "total_weekly_questions": len(weekly_questions),
        "total_pyq_questions": len(pyq_questions),
        "weeks_available": weeks_available,
        "questions_requiring_review": len(review_required),
        "all_answers_verified": len(review_required) == 0
    })


@app.route("/api/questions/weekly/<int:week>")
def api_weekly_questions(week):
    qs = [q for q in weekly_questions if q["week"] == week]
    if not qs:
        return jsonify({"status": "error", "message": f"Week {week} not found"}), 404
    # Sort by original question number
    qs_sorted = sorted(qs, key=lambda x: x["question_number"])
    return jsonify({
        "status": "success",
        "mode": "weekly",
        "week": week,
        "week_label": f"Week {week}",
        "total": len(qs_sorted),
        "questions": qs_sorted
    })


@app.route("/api/questions/pyq")
def api_pyq_questions():
    try:
        count = int(request.args.get("count", 50))
    except ValueError:
        count = 50

    if count <= 0:
        count = 50
    if count > len(pyq_questions):
        count = len(pyq_questions)

    # If count equals total bank, shuffle all 180 questions
    if count == len(pyq_questions):
        selected = list(pyq_questions)
        random.shuffle(selected)
    else:
        # Random sample without replacement, then shuffle
        selected = random.sample(pyq_questions, count)

    return jsonify({
        "status": "success",
        "mode": "pyq",
        "requested_count": count,
        "total": len(selected),
        "questions": selected
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(f"NPTEL Quizzer starting on http://localhost:{port}")
    print(f"Loaded {len(weekly_questions)} weekly questions and {len(pyq_questions)} PYQ questions.")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
