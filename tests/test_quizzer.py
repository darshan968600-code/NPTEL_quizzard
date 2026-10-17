"""
Comprehensive Test Suite for NPTEL Quizzer
Tests:
1. Data Integrity & Completeness (310 questions across both banks)
2. Week 0-12 structure (exactly 10 questions per week = 130 total)
3. PYQ subsets (50, 100, 150, 180 questions, uniqueness, randomization)
4. Answer key validity & option membership
5. Flask endpoints and response status
6. Scoring & evaluation simulation (correct, wrong, re-attempt update, unanswered)
"""

import json
import os
import unittest
from app import app, weekly_questions, pyq_questions, review_required


class TestNPTELQuizzer(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_weekly_questions_count_and_structure(self):
        """Test that weekly bank has 130 questions across Weeks 0-12 with 10 questions each."""
        self.assertEqual(len(weekly_questions), 130)
        weeks = set(q["week"] for q in weekly_questions)
        self.assertEqual(weeks, set(range(13)))  # Weeks 0 through 12

        for w in range(13):
            w_qs = [q for q in weekly_questions if q["week"] == w]
            self.assertEqual(len(w_qs), 10, f"Week {w} must have exactly 10 questions")
            # Verify continuous question numbering 1-10
            q_nums = [q["question_number"] for q in w_qs]
            self.assertEqual(q_nums, list(range(1, 11)))

    def test_02_pyq_questions_count_and_structure(self):
        """Test that PYQ bank has exactly 180 questions numbered 1 to 180."""
        self.assertEqual(len(pyq_questions), 180)
        q_nums = [q["question_number"] for q in pyq_questions]
        self.assertEqual(len(set(q_nums)), 180, "No duplicate question numbers in PYQ")
        self.assertEqual(sorted(q_nums), list(range(1, 181)))

    def test_03_all_questions_have_valid_answers_and_options(self):
        """Test that every single question has options and a verified correct answer."""
        for q in weekly_questions:
            self.assertIn(q["correct_answer"], q["options"], 
                          f"Weekly Q {q['id']} correct answer '{q['correct_answer']}' not in options")
            self.assertGreaterEqual(len(q["options"]), 2)

        for q in pyq_questions:
            self.assertIn(q["correct_answer"], q["options"], 
                          f"PYQ Q {q['id']} correct answer '{q['correct_answer']}' not in options")
            self.assertEqual(len(q["options"]), 4, f"PYQ Q {q['id']} must have exactly 4 options")

    def test_04_review_required_is_zero(self):
        """Verify that 0 questions require manual review."""
        self.assertEqual(len(review_required), 0)

    def test_05_api_summary(self):
        """Verify /api/summary returns correct metadata."""
        res = self.client.get("/api/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_weekly_questions"], 130)
        self.assertEqual(data["total_pyq_questions"], 180)
        self.assertEqual(data["questions_requiring_review"], 0)
        self.assertTrue(data["all_answers_verified"])

    def test_06_api_weekly_endpoint(self):
        """Verify /api/questions/weekly/<week> returns expected questions."""
        for w in range(13):
            res = self.client.get(f"/api/questions/weekly/{w}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["total"], 10)
            self.assertEqual(len(data["questions"]), 10)

        # Invalid week returns 404
        res = self.client.get("/api/questions/weekly/99")
        self.assertEqual(res.status_code, 404)

    def test_07_api_pyq_endpoint_subsets(self):
        """Verify /api/questions/pyq returns requested counts without duplicates."""
        for count in [50, 100, 150, 180]:
            res = self.client.get(f"/api/questions/pyq?count={count}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["total"], count)
            qs = data["questions"]
            self.assertEqual(len(qs), count)

            # Ensure no duplicates within quiz
            ids = [q["id"] for q in qs]
            self.assertEqual(len(ids), len(set(ids)), f"Duplicate questions found in PYQ count={count}")

    def test_08_api_pyq_randomization(self):
        """Verify that two subsequent 50-question requests generate different random sets / order."""
        res1 = self.client.get("/api/questions/pyq?count=50").get_json()["questions"]
        res2 = self.client.get("/api/questions/pyq?count=50").get_json()["questions"]
        ids1 = [q["id"] for q in res1]
        ids2 = [q["id"] for q in res2]
        self.assertNotEqual(ids1, ids2, "Two distinct 50-question requests should be randomized")

    def test_09_scoring_and_reattempt_logic_simulation(self):
        """Simulate answer evaluation, re-attempts, and unanswered questions."""
        # Scenario: 5 questions
        sample_qs = [
            {"id": "Q1", "correct": "B", "selected": "B", "evaluated": True},  # Correct (+1)
            {"id": "Q2", "correct": "A", "selected": "C", "evaluated": True},  # Wrong (0)
            {"id": "Q3", "correct": "D", "selected": None, "evaluated": False}, # Unanswered (0, not marked wrong)
            {"id": "Q4", "correct": "C", "selected": "C", "evaluated": True},  # Correct (+1)
            {"id": "Q5", "correct": "A", "selected": "B", "evaluated": True},  # Wrong initially
        ]

        def compute_score(qs):
            return sum(1 for q in qs if q["evaluated"] and q["selected"] == q["correct"])

        self.assertEqual(compute_score(sample_qs), 2)  # Q1 and Q4 correct

        # Now re-attempt Q5: change from 'B' to 'A'
        sample_qs[4]["selected"] = "A"
        sample_qs[4]["evaluated"] = True
        self.assertEqual(compute_score(sample_qs), 3)  # Now Q1, Q4, Q5 correct, no double counting!

        # Now change Q1 from 'B' to 'C' (wrong)
        sample_qs[0]["selected"] = "C"
        self.assertEqual(compute_score(sample_qs), 2)  # Score drops to 2, accurate latest evaluation!

    def test_10_html_routes_render_cleanly(self):
        """Verify that homepage and quiz page render without HTTP errors."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"NPTEL Quizzer", res.data)
        self.assertIn(b"Week 0", res.data)
        self.assertIn(b"Week 12", res.data)

        res = self.client.get("/quiz?mode=weekly&week=1")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Question Navigator", res.data)

        res = self.client.get("/quiz?mode=pyq&count=50")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Question Navigator", res.data)


if __name__ == "__main__":
    unittest.main()
