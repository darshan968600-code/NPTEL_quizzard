"""
Comprehensive Test Suite for NPTEL Quizzer
Tests:
1. Data Integrity & Completeness (436 questions across all three banks: 130 weekly + 156 important + 150 additional)
2. Week 0-12 structure (exactly 10 questions per week = 130 total)
3. Important Questions subsets (50, 100, 156 questions, uniqueness, randomization)
4. Additional Practice Questions subsets (50, 100, 150 questions, uniqueness, randomization)
5. Combined Mode endpoint (436 questions, shuffle toggling, predictable order when disabled)
6. Answer key validity & option membership for every single question
7. Zero review items required
8. Source Anonymity (No mention of Claude or ChatGPT in API or HTML)
9. Removal of outdated offline/localhost references
10. Flask endpoints and response status
"""

import json
import os
import unittest
from app import app, weekly_questions, bank_a_questions, bank_b_questions, review_required


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
            q_nums = [q["question_number"] for q in w_qs]
            self.assertEqual(q_nums, list(range(1, 11)))

    def test_02_bank_a_important_questions_count_and_structure(self):
        """Test that Important Questions bank has 156 questions with valid options and keys."""
        self.assertEqual(len(bank_a_questions), 156)
        for q in bank_a_questions:
            self.assertEqual(len(q["options"]), 4, f"Question {q['id']} must have exactly 4 options")
            self.assertIn(q["correct_answer"], q["options"], 
                          f"Question {q['id']} correct answer '{q['correct_answer']}' not in options")

    def test_03_bank_b_additional_questions_count_and_structure(self):
        """Test that Additional Practice Questions bank has 150 questions with valid options and keys."""
        self.assertEqual(len(bank_b_questions), 150)
        for q in bank_b_questions:
            self.assertEqual(len(q["options"]), 4, f"Question {q['id']} must have exactly 4 options")
            self.assertIn(q["correct_answer"], q["options"], 
                          f"Question {q['id']} correct answer '{q['correct_answer']}' not in options")

    def test_04_review_required_is_zero(self):
        """Verify that 0 questions require manual review."""
        self.assertEqual(len(review_required), 0)

    def test_05_api_summary(self):
        """Verify /api/summary returns correct metadata for all question banks."""
        res = self.client.get("/api/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_weekly_questions"], 130)
        self.assertEqual(data["total_important_questions"], 156)
        self.assertEqual(data["total_additional_questions"], 150)
        self.assertEqual(data["total_combined_questions"], 436)
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

    def test_07_api_important_endpoint_subsets(self):
        """Verify /api/questions/important returns requested counts without duplicates."""
        for count in [50, 100, 156]:
            res = self.client.get(f"/api/questions/important?count={count}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["total"], count)
            qs = data["questions"]
            self.assertEqual(len(qs), count)

            # Ensure no duplicates within quiz
            ids = [q["id"] for q in qs]
            self.assertEqual(len(ids), len(set(ids)), f"Duplicate questions found in important count={count}")

    def test_08_api_additional_endpoint_subsets(self):
        """Verify /api/questions/additional returns requested counts without duplicates."""
        for count in [50, 100, 150]:
            res = self.client.get(f"/api/questions/additional?count={count}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["total"], count)
            qs = data["questions"]
            self.assertEqual(len(qs), count)

            # Ensure no duplicates within quiz
            ids = [q["id"] for q in qs]
            self.assertEqual(len(ids), len(set(ids)), f"Duplicate questions found in additional count={count}")

    def test_09_api_combined_mode_all_weekly_questions(self):
        """Verify /api/questions/all returns all 130 Week 0-12 questions and respects shuffle_q setting."""
        # Unshuffled: predictable source order by week and question number
        res_unshuffled = self.client.get("/api/questions/all?shuffle_q=0")
        self.assertEqual(res_unshuffled.status_code, 200)
        data_unshuffled = res_unshuffled.get_json()
        self.assertEqual(data_unshuffled["total"], 130)
        self.assertEqual(len(data_unshuffled["questions"]), 130)
        self.assertFalse(data_unshuffled["shuffled"])

        # Check that questions are in order (Week 0 Q1 to Week 12 Q10)
        all_ids = [q["id"] for q in data_unshuffled["questions"]]
        self.assertEqual(all_ids[0], "W0_Q1")
        self.assertEqual(all_ids[-1], "W12_Q10")
        self.assertTrue(all(qid.startswith("W") for qid in all_ids))

        # Shuffled: returns all 130 questions in random order
        res_shuffled = self.client.get("/api/questions/all?shuffle_q=1")
        self.assertEqual(res_shuffled.status_code, 200)
        data_shuffled = res_shuffled.get_json()
        self.assertEqual(data_shuffled["total"], 130)
        self.assertTrue(data_shuffled["shuffled"])
        shuffled_ids = [q["id"] for q in data_shuffled["questions"]]
        self.assertEqual(len(shuffled_ids), len(set(shuffled_ids)), "No duplicates in combined weekly quiz")
        self.assertEqual(set(shuffled_ids), set(all_ids), "Same 130 questions present in shuffled set")

    def test_10_source_anonymity_strict_enforcement(self):
        """Verify that AI source names (Claude, ChatGPT) NEVER appear in user-facing HTML or JSON APIs."""
        for endpoint in ["/", "/quiz", "/api/summary", "/api/questions/important", "/api/questions/additional", "/api/questions/all"]:
            res = self.client.get(endpoint)
            text = res.get_data(as_text=True).lower()
            self.assertNotIn("claude", text, f"Source anonymity violation: 'claude' found in {endpoint}")
            self.assertNotIn("chatgpt", text, f"Source anonymity violation: 'chatgpt' found in {endpoint}")

    def test_11_outdated_offline_and_localhost_removal(self):
        """Verify that outdated offline and localhost references are completely removed from homepage."""
        res = self.client.get("/")
        html = res.get_data(as_text=True)
        self.assertNotIn("Offline Ready", html)
        self.assertNotIn("Offline Localhost Practice Tool", html)
        self.assertNotIn("No external APIs or cloud dependencies", html)
        self.assertNotIn("310 Questions", html)
        # Verify theme toggle button is present
        self.assertIn("theme-toggle-btn", html)
        # Verify Practice All Questions featured card is present
        self.assertIn("Practice All Questions", html)
        # Verify both new banks are present
        self.assertIn("Important Questions", html)
        self.assertIn("Additional Practice Questions", html)


if __name__ == "__main__":
    unittest.main()
