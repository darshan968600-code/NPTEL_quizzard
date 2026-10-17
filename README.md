# NPTEL Quizzer

A fast, interactive, offline-ready local quiz web application built for practicing NPTEL **Performance and Reward Management** assessment questions and previous-year exam questions (PYQs).

---

## 1. Project Overview

- **Mode A (NPTEL Weekly Questions):** 130 authentic weekly assessment questions spanning **Week 0 through Week 12** (13 weeks &times; 10 questions each).
- **Mode B (PYQs & Curated Practice):** 180 previous-year questions with options for **50, 100, 150, or all 180 questions** (randomized subset without repetition, shuffled order).
- **Total Question Bank:** 310 questions extracted with **100% verified answer keys** and **0 questions requiring manual review**.
- **Tech Stack:** Lightweight Python Flask backend, HTML5, CSS3, Vanilla JavaScript, and `localStorage` session persistence.
- **100% Offline & Private:** Runs entirely on `localhost`. Requires no paid APIs, no external cloud dependencies, and no database setup.

---

## 2. Directory Structure

```text
NPTEL_quizzard/
├── app.py                      # Flask local web server and API endpoints
├── extract_data.py             # Reproducible PDF question extraction script
├── README.md                   # Setup and usage guide
├── questions/                  # Source NPTEL PDF files
│   ├── NPTEL Assessment Question Bank - Weeks 0-12.pdf
│   ├── NPTEL Assessment Answer Key - Weeks 0-12.pdf
│   └── NPTEL_PRM_180_MCQ_Combined.pdf
├── data/                       # Extracted structured JSON datasets
│   ├── weekly_questions.json   # 130 weekly questions with verified answers
│   ├── pyq_questions.json      # 180 PYQ questions with verified answers
│   └── review_required.json    # Flagged items (empty: 0 issues found)
├── templates/                  # Jinja2 HTML templates
│   ├── index.html              # Homepage with Mode A and Mode B selection
│   └── quiz.html               # Reusable quiz interface and results screen
├── static/
│   ├── css/
│   │   └── style.css           # Clean, accessible styling & color-coded states
│   └── js/
│       ├── home.js             # Session recovery banner & mode routing
│       └── quiz.js             # Quiz engine, navigation grid, scoring, & review
└── tests/
    └── test_quizzer.py         # Automated test suite (10 unit & integration tests)
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Required packages: `flask`, `pymupdf` (fitz)

If needed, install dependencies:
```bash
python -m pip install flask pymupdf
```

### Launch the Application
Run the local server from the project directory:
```bash
python app.py
```

Open your web browser and navigate to:
```text
http://localhost:5000
```
*(or `http://127.0.0.1:5000`)*

---

## 4. Question Extraction & Verification Summary

The questions were extracted directly from the primary PDF sources using `extract_data.py`:

| Dataset | Source PDF | Questions Extracted | Verified Answers | Manual Review Required |
| :--- | :--- | :---: | :---: | :---: |
| **Weekly Assignments** | `NPTEL Assessment Question Bank - Weeks 0-12.pdf`<br>`NPTEL Assessment Answer Key - Weeks 0-12.pdf` | **130** | **130 / 130** (100%) | **0** |
| **PYQs / Practice MCQs** | `NPTEL_PRM_180_MCQ_Combined.pdf` | **180** | **180 / 180** (100%) | **0** |
| **Total** | | **310** | **310 / 310** (100%) | **0** |

To re-run the extraction at any time:
```bash
python extract_data.py
```

---

## 5. How to Use NPTEL Quizzer

### Starting a Quiz
1. **Homepage:**
   - **Mode A (Weekly):** Click on any week card (Week 0 to Week 12) to start a 10-question quiz for that specific week.
   - **Mode B (PYQs):** Choose a practice size: **50 Qs**, **100 Qs**, **150 Qs**, or **All 180 Qs**. Questions are randomly sampled without replacement and presented in a shuffled order.
2. **Resuming an Ongoing Quiz:**
   - If you accidentally close or refresh the page, the homepage displays an **"Ongoing Quiz"** banner. Click **"Resume Quiz"** to pick up right where you left off.

### Quiz Interface & Answering Rules
- **Selecting an Answer:** Click any option (A, B, C, D) or press keys `A`/`B`/`C`/`D` (or `1`/`2`/`3`/`4`). Your choice is highlighted with a blue border. **The correct answer is not revealed prematurely.**
- **Evaluating Answer & Auto-Advance (~2.5s):**
  - Click **"Next →"** (or press Enter / Space / Right Arrow).
  - The system evaluates your response against the verified answer key:
    - 🟩 **Correct:** Option turns **Green** with a checkmark and positive indicator.
    - 🟥 **Incorrect:** Your wrong choice turns **Red**, the true answer turns **Green**, and a helpful explanation is displayed.
    - The right-hand navigation grid updates in real time.
  - The feedback remains visible for **~2.5 seconds**, and the website **automatically transitions to the next question**!
  - *Fast-Forward option:* If you don't wish to wait 2.5 seconds, clicking **"Next Now →"** advances immediately.
- **Skipping Unanswered Questions:**
  - If you do not select an option, clicking **"Next (Skip) →"** advances immediately to the next question without penalizing or marking the question wrong. It remains neutral gray in the navigator.
- **Re-answering / Retrying:**
  - You can revisit any question using the navigation grid and select a different answer.
  - Clicking **"Next →"** re-evaluates the question, displays the new feedback, and updates your score without duplicate counting.

### Question Navigation Panel (Right Sidebar)
- A compact, scrollable grid displays all question numbers (1 to 10 for weekly, 1 to 180 for PYQ).
- **Color Scheme:**
  - 🟩 **Green:** Answered correctly.
  - 🟥 **Red:** Answered incorrectly.
  - ⬜ **Neutral Gray:** Unanswered.
  - 🟦 **Distinct Outline / Ring:** Currently active question (preserves underlying green/red status).
- Click any box to jump directly to that question.

### Scoring & Results
- When the quiz finishes, the **Results Screen** presents:
  - Final Score (e.g., `8 / 10` or `36 / 50`) and Accuracy Percentage (`80%`, `72%`).
  - Breakdown: Total Questions, Correct, Incorrect, and Unanswered.
  - **"Review Answers"** button: Expands an interactive breakdown of every question with filter buttons (*All*, *Wrong Only*, *Unanswered*, *Correct*).
  - **"Restart Quiz"** button: Clears answers and restarts the current session.
  - **"Return to Home"** button: Goes back to the main portal.

---

## 6. Running Automated Tests

Run the full automated test suite verifying data integrity, API endpoints, randomization, and scoring logic:

```bash
python -m unittest tests/test_quizzer.py
```
