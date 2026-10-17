# NPTEL Quizzer

A fast, interactive, distraction-free practice portal built for NPTEL **Performance and Reward Management** assessment questions and curated exam preparation.

---

## 1. Project Overview

- **NPTEL Weekly Practice:** 130 authentic weekly assessment questions spanning **Week 0 through Week 12** (13 weeks &times; 10 questions each).
- **Important Questions:** Dedicated question bank for focused exam preparation with choices for **individual week modules (Weeks 1–12 dropdown, 10 Qs each)** as well as practice sets across all weeks for **60 Qs** or **Full Bank (120 Qs)**.
- **Additional Practice Questions:** Expanded practice question bank covering all course modules with choices for **50 Qs**, **100 Qs**, or **Full Bank (150 Qs)**.
- **Combined Weekly Mode (Practice All Questions):** Practice session covering all **130 assessment questions** from Weeks 0 through 12 in one continuous session with configurable pre-quiz settings:
  - *Shuffle Questions* (toggleable randomization across Weeks 0–12)
  - *Shuffle Answer Options* (randomized option display with 100% verified key mapping)
- **Light & Dark Theme Toggle:** Compact header theme toggle with persistent user preference across sessions.
- **Total Question Pool:** 400 questions extracted with **100% verified answer keys** and **0 questions requiring manual review**.
- **Tech Stack:** Python Flask backend, HTML5, CSS3 with custom properties, Vanilla JavaScript, and `localStorage` session persistence.

---

## 2. Directory Structure

```text
NPTEL_quizzard/
├── app.py                      # Flask web server and API endpoints
├── extract_data.py             # Reproducible question extraction script
├── README.md                   # Setup and usage guide
├── questions/                  # Source assessment HTML and PDF files
├── data/                       # Extracted structured JSON datasets
│   ├── weekly_questions.json   # 130 weekly questions with verified answers
│   ├── bank_a_questions.json   # 120 Important Questions with verified answers & rationale
│   ├── bank_b_questions.json   # 150 Additional Practice Questions with verified answers
│   └── review_required.json    # Flagged items (empty: 0 issues found)
├── templates/                  # Jinja2 HTML templates
│   ├── index.html              # Homepage with weekly, curated banks, and combined mode
│   └── quiz.html               # Reusable quiz interface and results screen
├── static/
│   ├── css/
│   │   └── style.css           # Accessible styling, light/dark themes & color-coded states
│   └── js/
│       ├── home.js             # Session recovery banner, theme toggle & modal handling
│       └── quiz.js             # Quiz engine, option shuffling, navigator grid & review
└── tests/
    └── test_quizzer.py         # Automated test suite (12 unit & integration tests)
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Required packages: `flask`, `pymupdf` (fitz), `gunicorn`

If needed, install dependencies:
```bash
python -m pip install -r requirements.txt
```

### Launch the Application
Run the server:
```bash
python app.py
```

---

## 4. Question Extraction & Verification Summary

The questions were extracted directly from the primary sources using `extract_data.py`:

| Dataset | Questions Extracted | Verified Answers | Manual Review Required |
| :--- | :---: | :---: | :---: |
| **Weekly Assignments (Weeks 0–12)** | **130** | **130 / 130** (100%) | **0** |
| **Important Questions Bank** | **120** | **120 / 120** (100%) | **0** |
| **Additional Practice Questions Bank** | **150** | **150 / 150** (100%) | **0** |
| **Combined Question Pool** | **400** | **400 / 400** (100%) | **0** |

To re-run the extraction at any time:
```bash
python extract_data.py
```

---

## 5. How to Use NPTEL Quizzer

### Practice Modes
1. **Weekly Assignments:** Click any week card (Week 0 to Week 12) to start a 10-question practice set for that specific week.
2. **Practice All Questions:** Click the prominent featured card in Section 1 to configure and launch a session with all 130 assessment questions (Weeks 0–12) with customizable Question and Option shuffling.
3. **Important Questions:** Practice focused exam questions by **individual week (Week 1 to Week 12 via the dropdown)**, or choose cross-week practice for 60 Qs or all 120 Qs.
4. **Additional Practice Questions:** Practice additional questions with options for 50 Qs, 100 Qs, or all 150 Qs.

### Quiz Features
- **Instant Option Feedback:** Click any option or press keys `A`/`B`/`C`/`D` (or `1`/`2`/`3`/`4`). Correct answers turn green; incorrect answers turn red with the correct answer highlighted.
- **Option Shuffling:** Randomizes the display order of options for each question while keeping answer checking and scoring 100% accurate.
- **Navigator Grid:** Right-hand panel displays question statuses (Green: Correct, Red: Incorrect, Gray: Unanswered, Blue Ring: Current Question).
- **Session Resumption:** Ongoing sessions can be resumed from the homepage if the page is refreshed or accidentally closed.
- **Results & Review:** Provides accuracy breakdown, score calculation, and an interactive question breakdown with filters (*All*, *Wrong Only*, *Unanswered*, *Correct*).

---

## 6. Running Automated Tests

Run the full automated test suite verifying data integrity, API endpoints, randomization, and scoring logic:

```bash
python -m unittest tests/test_quizzer.py
```
