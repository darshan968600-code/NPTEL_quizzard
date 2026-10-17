"""
NPTEL Quizzer - Application Server
"""

import json
import os
import random
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEEKLY_FILE = os.path.join(DATA_DIR, "weekly_questions.json")
BANK_A_FILE = os.path.join(DATA_DIR, "bank_a_questions.json")
BANK_B_FILE = os.path.join(DATA_DIR, "bank_b_questions.json")
REVIEW_FILE = os.path.join(DATA_DIR, "review_required.json")

# Load data into memory
weekly_questions = []
bank_a_questions = []
bank_b_questions = []
review_required = []

if os.path.exists(WEEKLY_FILE):
    with open(WEEKLY_FILE, "r", encoding="utf-8") as f:
        weekly_questions = json.load(f)

if os.path.exists(BANK_A_FILE):
    with open(BANK_A_FILE, "r", encoding="utf-8") as f:
        bank_a_questions = json.load(f)

if os.path.exists(BANK_B_FILE):
    with open(BANK_B_FILE, "r", encoding="utf-8") as f:
        bank_b_questions = json.load(f)

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
    total_weekly = len(weekly_questions)
    total_important = len(bank_a_questions)
    total_additional = len(bank_b_questions)
    total_combined = total_weekly + total_important + total_additional

    return render_template(
        "index.html",
        weeks=sorted_weeks,
        total_weekly=total_weekly,
        total_important=total_important,
        total_additional=total_additional,
        total_combined=total_combined,
        review_count=len(review_required)
    )


@app.route("/quiz")
def quiz():
    mode = request.args.get("mode", "weekly")
    week = request.args.get("week", "0")
    count = request.args.get("count", "50")
    shuffle_q = request.args.get("shuffle_q", "1")
    shuffle_opt = request.args.get("shuffle_opt", "1")
    return render_template(
        "quiz.html",
        mode=mode,
        week=week,
        count=count,
        shuffle_q=shuffle_q,
        shuffle_opt=shuffle_opt
    )


# API Endpoints
@app.route("/api/summary")
def api_summary():
    weeks_available = sorted(list(set(q["week"] for q in weekly_questions)))
    total_combined = len(weekly_questions) + len(bank_a_questions) + len(bank_b_questions)
    return jsonify({
        "status": "success",
        "total_weekly_questions": len(weekly_questions),
        "total_important_questions": len(bank_a_questions),
        "total_additional_questions": len(bank_b_questions),
        "total_combined_questions": total_combined,
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


@app.route("/api/questions/important")
def api_important_questions():
    """Important Questions Bank"""
    try:
        count = int(request.args.get("count", 50))
    except ValueError:
        count = 50

    if count <= 0:
        count = 50
    if count > len(bank_a_questions):
        count = len(bank_a_questions)

    if count == len(bank_a_questions):
        selected = list(bank_a_questions)
        random.shuffle(selected)
    else:
        selected = random.sample(bank_a_questions, count)

    return jsonify({
        "status": "success",
        "mode": "important",
        "mode_title": "Important Questions",
        "requested_count": count,
        "total": len(selected),
        "questions": selected
    })


@app.route("/api/questions/additional")
def api_additional_questions():
    """Additional Practice Questions Bank"""
    try:
        count = int(request.args.get("count", 50))
    except ValueError:
        count = 50

    if count <= 0:
        count = 50
    if count > len(bank_b_questions):
        count = len(bank_b_questions)

    if count == len(bank_b_questions):
        selected = list(bank_b_questions)
        random.shuffle(selected)
    else:
        selected = random.sample(bank_b_questions, count)

    return jsonify({
        "status": "success",
        "mode": "additional",
        "mode_title": "Additional Practice Questions",
        "requested_count": count,
        "total": len(selected),
        "questions": selected
    })


@app.route("/api/questions/all")
def api_all_questions():
    """
    Combined Weekly Practice Mode:
    All 130 authentic assessment questions from Weeks 0-12.
    Respects shuffle_q parameter (1 = randomized order, 0 = predictable source order by week).
    """
    shuffle_q = request.args.get("shuffle_q", "1").lower() in ["1", "true", "yes"]

    # Source order: weekly questions sorted by week and question_number
    combined = list(sorted(weekly_questions, key=lambda x: (x["week"], x["question_number"])))

    if shuffle_q:
        selected = list(combined)
        random.shuffle(selected)
    else:
        selected = list(combined)

    return jsonify({
        "status": "success",
        "mode": "all",
        "mode_title": "Practice All Questions (Weeks 0–12)",
        "total": len(selected),
        "shuffled": shuffle_q,
        "questions": selected
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"NPTEL Quizzer starting on port {port}")
    print(f"Loaded {len(weekly_questions)} weekly, {len(bank_a_questions)} important, and {len(bank_b_questions)} additional practice questions.")
    app.run(host="0.0.0.0", port=port, debug=False)
