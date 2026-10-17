"""
Extraction script for NPTEL Quizzer.
Extracts questions from:
1. questions/NPTEL Assessment Question Bank - Weeks 0-12.pdf
   and questions/NPTEL Assessment Answer Key - Weeks 0-12.pdf -> data/weekly_questions.json
2. questions/bank_a_important.pdf -> data/bank_a_questions.json (Important Questions)
3. questions/bank_b_additional.pdf -> data/bank_b_questions.json (Additional Practice Questions)

Outputs:
- data/weekly_questions.json (130 questions)
- data/bank_a_questions.json (156 questions)
- data/bank_b_questions.json (150 questions)
- data/review_required.json
"""

import json
import os
import re
import pymupdf


def clean_text(text: str) -> str:
    if not text:
        return ""
    # Remove cite markers like [cite: 37]
    text = re.sub(r"\[cite:\s*\d+\]", "", text)
    # Remove control characters except standard whitespace
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize excessive spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize smart quotes / dashes
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = text.replace("–", "-").replace("—", "-")
    return text.strip()


def extract_weekly_questions(pdf_dir: str):
    qb_path = os.path.join(pdf_dir, "NPTEL Assessment Question Bank - Weeks 0-12.pdf")
    ak_path = os.path.join(pdf_dir, "NPTEL Assessment Answer Key - Weeks 0-12.pdf")

    # 1. Parse Answer Key
    ak_doc = pymupdf.open(ak_path)
    ak_text = "\n".join(page.get_text() for page in ak_doc)
    ak_pattern = re.compile(r"WEEK\s+(\d+)\s+[^\n]*?ANSWER KEY", re.IGNORECASE)
    ak_matches = list(ak_pattern.finditer(ak_text))

    answers = {}
    for i, m in enumerate(ak_matches):
        week_num = int(m.group(1))
        start_pos = m.end()
        end_pos = ak_matches[i + 1].start() if i + 1 < len(ak_matches) else len(ak_text)
        sec = ak_text[start_pos:end_pos]
        for line in sec.split("\n"):
            line = line.strip()
            ans_m = re.match(r"^Question\s+(\d+)\s*-\s*Correct answer:\s*([A-D])\.\s*(.*)", line)
            if ans_m:
                q_num = int(ans_m.group(1))
                key = ans_m.group(2)
                exp = clean_text(ans_m.group(3))
                answers[(week_num, q_num)] = {"key": key, "text": exp}
            else:
                other_m = re.match(r"^Question\s+(\d+)\s*-\s*Correct answer:\s*([A-D])\b(.*)", line)
                if other_m:
                    q_num = int(other_m.group(1))
                    key = other_m.group(2)
                    exp = clean_text(other_m.group(3))
                    answers[(week_num, q_num)] = {"key": key, "text": exp}

    # 2. Parse Question Bank
    qb_doc = pymupdf.open(qb_path)
    qb_text = "\n".join(page.get_text() for page in qb_doc)
    qb_pattern = re.compile(r"WEEK\s+(\d+)\s+[^\n]*?ASSESSMENT QUESTIONS", re.IGNORECASE)
    qb_matches = list(qb_pattern.finditer(qb_text))

    weekly_questions = []
    review_items = []

    for i, m in enumerate(qb_matches):
        week_num = int(m.group(1))
        start_pos = m.end()
        end_pos = qb_matches[i + 1].start() if i + 1 < len(qb_matches) else len(qb_text)
        sec = qb_text[start_pos:end_pos]

        q_splits = list(re.finditer(r"Question\s+(\d+)\s*:", sec))
        for q_idx, qm in enumerate(q_splits):
            q_num = int(qm.group(1))
            q_start = qm.end()
            q_end = q_splits[q_idx + 1].start() if q_idx + 1 < len(q_splits) else len(sec)
            q_content = sec[q_start:q_end].strip()

            lines = [l.strip() for l in q_content.split("\n") if l.strip()]
            q_lines = []
            options = {}
            curr_opt = None

            for line in lines:
                clean_l = clean_text(line)
                if not clean_l:
                    continue
                opt_m = re.match(r"^([A-D])\.\s*(.*)", clean_l)
                if opt_m:
                    curr_opt = opt_m.group(1)
                    options[curr_opt] = opt_m.group(2).strip()
                elif curr_opt:
                    options[curr_opt] += " " + clean_l
                else:
                    q_lines.append(clean_l)

            q_text = clean_text(" ".join(q_lines))
            ans_info = answers.get((week_num, q_num))

            correct_key = ans_info["key"] if ans_info else None
            explanation = ans_info["text"] if ans_info else ""

            # Check verification
            if not correct_key:
                review_items.append({
                    "source": "Weekly Question Bank",
                    "week": week_num,
                    "question_num": q_num,
                    "issue": "Missing answer key in answer key document",
                    "question": q_text
                })
            elif correct_key not in options:
                review_items.append({
                    "source": "Weekly Question Bank",
                    "week": week_num,
                    "question_num": q_num,
                    "issue": f"Answer key '{correct_key}' not in extracted options {list(options.keys())}",
                    "question": q_text
                })

            weekly_questions.append({
                "id": f"W{week_num}_Q{q_num}",
                "week": week_num,
                "week_label": f"Week {week_num}",
                "question_number": q_num,
                "question": q_text,
                "options": options,
                "correct_answer": correct_key,
                "explanation": explanation
            })

    return weekly_questions, review_items


def extract_bank_a_questions(pdf_dir: str):
    """
    Extracts Question Bank A (Important Questions) from bank_a_important.pdf.
    Contains 156 questions (Weeks 0-12) with full answer key at the end.
    """
    pdf_path = os.path.join(pdf_dir, "bank_a_important.pdf")
    doc = pymupdf.open(pdf_path)
    full_text = "\n".join(page.get_text() for page in doc)

    ak_pos = full_text.find("ANSWER KEY")
    q_text = full_text[:ak_pos]
    ak_text = full_text[ak_pos:]

    # Parse answer key
    ans_dict = {}
    for q_num, ans in re.findall(r"Q(\d+):\s*([A-D])", ak_text):
        ans_dict[int(q_num)] = ans

    week_titles = {
        0: "Week 0 - Introduction to PM & Rewards",
        1: "Week 1 - PM Process & Reward Basics",
        2: "Week 2 - Strategic Alignment & SWOT",
        3: "Week 3 - Performance Measurement Approaches",
        4: "Week 4 - Appraisal Methods & Errors",
        5: "Week 5 - Development, Teams & Coaching",
        6: "Week 6 - Total Rewards & Fairness",
        7: "Week 7 - Incentive Theories & Pay Plans",
        8: "Week 8 - Job Evaluation & Pay Structures",
        9: "Week 9 - Executive Pay & Incentive Design",
        10: "Week 10 - Government Pay & Pension",
        11: "Week 11 - Reward System Design",
        12: "Week 12 - Ethics in PM & Rewards",
    }

    lines = [clean_text(l) for l in q_text.split("\n")]
    questions = []
    curr_q = None
    curr_week = 0
    review_items = []

    for line in lines:
        if not line:
            continue
        wm = re.match(r"^WEEK\s+(\d+)\s*[-–]\s*(.*)", line, re.IGNORECASE)
        if wm:
            curr_week = int(wm.group(1))
            continue
        qm = re.match(r"^Q(\d+)\.\s*(.*)", line)
        if qm:
            if curr_q:
                questions.append(curr_q)
            q_num = int(qm.group(1))
            curr_q = {
                "id": f"BANK_A_Q{q_num}",
                "question_number": q_num,
                "week": curr_week,
                "topic": week_titles.get(curr_week, f"Week {curr_week}"),
                "question": qm.group(2).strip(),
                "options": {},
                "curr_opt": None,
                "correct_answer": ans_dict.get(q_num),
                "explanation": ""
            }
            continue

        opt_m = re.match(r"^([A-D])\.\s*(.*)", line)
        if opt_m and curr_q:
            curr_q["curr_opt"] = opt_m.group(1)
            curr_q["options"][opt_m.group(1)] = opt_m.group(2).strip()
            continue

        if curr_q:
            if curr_q["curr_opt"]:
                curr_q["options"][curr_q["curr_opt"]] += " " + line
            else:
                curr_q["question"] += (" " if curr_q["question"] else "") + line

    if curr_q:
        questions.append(curr_q)

    # Clean and validate
    for q in questions:
        q.pop("curr_opt", None)
        q["question"] = clean_text(q["question"])
        for k in list(q["options"].keys()):
            q["options"][k] = clean_text(q["options"][k])

        if len(q["options"]) != 4:
            review_items.append({
                "source": "Question Bank A (Important Questions)",
                "question_num": q["question_number"],
                "issue": f"Expected 4 options, found {len(q['options'])}",
                "question": q["question"]
            })
        if not q["correct_answer"]:
            review_items.append({
                "source": "Question Bank A (Important Questions)",
                "question_num": q["question_number"],
                "issue": "Missing answer key in key section",
                "question": q["question"]
            })
        elif q["correct_answer"] not in q["options"]:
            review_items.append({
                "source": "Question Bank A (Important Questions)",
                "question_num": q["question_number"],
                "issue": f"Answer key {q['correct_answer']} not in options",
                "question": q["question"]
            })

    return questions, review_items


def extract_bank_b_questions(pdf_dir: str):
    """
    Extracts Question Bank B (Additional Practice Questions) from bank_b_additional.pdf.
    Contains 150 questions (Weeks 0-12) with correct answers identified by green text color (#155724) and '\x13'.
    """
    pdf_path = os.path.join(pdf_dir, "bank_b_additional.pdf")
    doc = pymupdf.open(pdf_path)

    week_titles = {
        0: "Week 0 - Foundations of Performance and Reward Management",
        1: "Week 1 - The Performance-Management Process",
        2: "Week 2 - Strategic Planning, SWOT, and SMART Goals",
        3: "Week 3 - Performance Dimensions, Competencies, and Measurement",
        4: "Week 4 - Appraisal Methods, Rating Errors, and Implementation",
        5: "Week 5 - Development, Coaching, Teams, and Recognition",
        6: "Week 6 - Total Rewards, Fairness, and Engagement",
        7: "Week 7 - Incentive Plans and Reward Theories",
        8: "Week 8 - Job Evaluation and Pay Structures",
        9: "Week 9 - Executive Rewards, Incentive Risks, and Knowledge Workers",
        10: "Week 10 - Public-Sector Pay and Retirement Benefits",
        11: "Week 11 - Reward-System Design and Review",
        12: "Week 12 - Ethics, Bias, and Fair Appraisal",
    }

    questions = []
    review_items = []
    curr_q = None
    curr_week = 0

    for p_idx in range(2, len(doc)):
        page = doc[p_idx]
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                line_str = "".join(s["text"] for s in l["spans"])
                has_marker = ("\x13" in line_str) or any(s["color"] == 0x155724 for s in l["spans"])
                cleaned_line = clean_text(line_str)
                if not cleaned_line:
                    continue

                # Header check
                wm = re.match(r"^WEEK\s+(\d+)\s*[-–]\s*(.*)", cleaned_line, re.IGNORECASE)
                if wm:
                    curr_week = int(wm.group(1))
                    continue

                # Question start check
                qm = re.match(r"^Q(\d+)\.\s*(.*)", cleaned_line)
                if qm:
                    if curr_q:
                        questions.append(curr_q)
                    q_num = int(qm.group(1))
                    curr_q = {
                        "id": f"BANK_B_Q{q_num}",
                        "question_number": q_num,
                        "week": curr_week,
                        "topic": week_titles.get(curr_week, f"Week {curr_week}"),
                        "question": qm.group(2).strip(),
                        "options": {},
                        "curr_opt": None,
                        "correct_answer": None,
                        "explanation": ""
                    }
                    continue

                # Option start check
                opt_m = re.match(r"^([A-D])\.\s*(.*)", cleaned_line)
                if opt_m and curr_q:
                    opt_letter = opt_m.group(1)
                    opt_text = opt_m.group(2).strip()
                    curr_q["options"][opt_letter] = opt_text
                    curr_q["curr_opt"] = opt_letter
                    if has_marker:
                        curr_q["correct_answer"] = opt_letter
                    continue

                if curr_q:
                    if curr_q["curr_opt"]:
                        curr_q["options"][curr_q["curr_opt"]] += " " + cleaned_line
                        if has_marker and not curr_q["correct_answer"]:
                            curr_q["correct_answer"] = curr_q["curr_opt"]
                    else:
                        curr_q["question"] += (" " if curr_q["question"] else "") + cleaned_line

    if curr_q:
        questions.append(curr_q)

    # Clean and validate
    for q in questions:
        q.pop("curr_opt", None)
        q["question"] = clean_text(q["question"])
        for k in list(q["options"].keys()):
            q["options"][k] = clean_text(q["options"][k])

        if len(q["options"]) != 4:
            review_items.append({
                "source": "Question Bank B (Additional Practice Questions)",
                "question_num": q["question_number"],
                "issue": f"Expected 4 options, found {len(q['options'])}",
                "question": q["question"]
            })
        if not q["correct_answer"]:
            review_items.append({
                "source": "Question Bank B (Additional Practice Questions)",
                "question_num": q["question_number"],
                "issue": "Missing or undetermined correct answer",
                "question": q["question"]
            })
        elif q["correct_answer"] not in q["options"]:
            review_items.append({
                "source": "Question Bank B (Additional Practice Questions)",
                "question_num": q["question_number"],
                "issue": f"Answer key {q['correct_answer']} not in options",
                "question": q["question"]
            })

    return questions, review_items


def main():
    base_dir = r"c:\NPTEL_quizzard"
    pdf_dir = os.path.join(base_dir, "questions")
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    print("Extracting Weekly Questions...")
    weekly_questions, weekly_reviews = extract_weekly_questions(pdf_dir)

    print("Extracting Question Bank A (Important Questions)...")
    bank_a_questions, bank_a_reviews = extract_bank_a_questions(pdf_dir)

    print("Extracting Question Bank B (Additional Practice Questions)...")
    bank_b_questions, bank_b_reviews = extract_bank_b_questions(pdf_dir)

    all_reviews = weekly_reviews + bank_a_reviews + bank_b_reviews

    # Save to JSON files
    weekly_file = os.path.join(data_dir, "weekly_questions.json")
    bank_a_file = os.path.join(data_dir, "bank_a_questions.json")
    bank_b_file = os.path.join(data_dir, "bank_b_questions.json")
    review_file = os.path.join(data_dir, "review_required.json")

    with open(weekly_file, "w", encoding="utf-8") as f:
        json.dump(weekly_questions, f, indent=2, ensure_ascii=False)

    with open(bank_a_file, "w", encoding="utf-8") as f:
        json.dump(bank_a_questions, f, indent=2, ensure_ascii=False)

    with open(bank_b_file, "w", encoding="utf-8") as f:
        json.dump(bank_b_questions, f, indent=2, ensure_ascii=False)

    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("EXTRACTION & VERIFICATION SUMMARY REPORT")
    print("=" * 60)
    print(f"Weekly Questions: {len(weekly_questions)} (Weeks 0-12, 10 each)")
    print(f"  Verified answers: {sum(1 for q in weekly_questions if q['correct_answer'])} / {len(weekly_questions)}")
    print(f"  Reviews required: {len(weekly_reviews)}")

    print(f"\nQuestion Bank A (Important Questions): {len(bank_a_questions)}")
    print(f"  Verified answers: {sum(1 for q in bank_a_questions if q['correct_answer'])} / {len(bank_a_questions)}")
    print(f"  Reviews required: {len(bank_a_reviews)}")

    print(f"\nQuestion Bank B (Additional Practice Questions): {len(bank_b_questions)}")
    print(f"  Verified answers: {sum(1 for q in bank_b_questions if q['correct_answer'])} / {len(bank_b_questions)}")
    print(f"  Reviews required: {len(bank_b_reviews)}")

    print(f"\nTotal questions across all banks: {len(weekly_questions) + len(bank_a_questions) + len(bank_b_questions)}")
    print(f"Total manual reviews required: {len(all_reviews)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
