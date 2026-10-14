"""Chạy từ thư mục MusicQuiz: python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from database import Database
from game_logic import NotEnoughSongsError, QuizGame


def fake_songs(n):
    return [{"title": f"Song {i}", "artist": f"Artist {i}", "file_path": f"/x/{i}.mp3"} for i in range(n)]


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def test_sync_inserts_and_is_idempotent(self):
        self.db.sync_songs(fake_songs(5))
        self.db.sync_songs(fake_songs(5))
        self.assertEqual(self.db.count_songs(), 5)

    def test_sync_removes_missing_files(self):
        self.db.sync_songs(fake_songs(5))
        self.db.sync_songs(fake_songs(3))
        self.assertEqual(self.db.count_songs(), 3)

    def test_distractors_exclude_correct(self):
        self.db.sync_songs(fake_songs(6))
        song = self.db.get_all_songs()[0]
        d = self.db.get_random_distractors(song.id, 3)
        self.assertEqual(len(d), 3)
        self.assertNotIn(song.id, [x.id for x in d])

    def test_scores_sorted_desc(self):
        for s in (50, 300, 120):
            self.db.save_result("A", s, 1, 10)
        self.assertEqual([r["score"] for r in self.db.get_top_scores()], [300, 120, 50])


class LogicTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.db.sync_songs(fake_songs(8))

    def test_not_enough_songs(self):
        db = Database(":memory:")
        db.sync_songs(fake_songs(2))
        with self.assertRaises(NotEnoughSongsError):
            QuizGame(db).start()

    def test_question_has_unique_choices_with_answer(self):
        g = QuizGame(self.db, num_questions=5)
        g.start()
        q = g.next_question(0)
        self.assertEqual(len(q.choices), config.NUM_CHOICES)
        self.assertEqual(len({c.id for c in q.choices}), config.NUM_CHOICES)
        self.assertEqual(q.choices[q.correct_index].id, q.song.id)

    def test_scoring_fast_slow_wrong(self):
        g = QuizGame(self.db, num_questions=3)
        g.start()
        q = g.next_question(0)
        fast = g.submit_answer(q.correct_index, 0)
        self.assertEqual(fast.points, config.POINTS_CORRECT + config.POINTS_TIME_BONUS_MAX)
        q = g.next_question(100)
        slow = g.submit_answer(q.correct_index, 100 + config.QUESTION_TIME)
        self.assertEqual(slow.points, config.POINTS_CORRECT)
        q = g.next_question(200)
        wrong = g.submit_answer((q.correct_index + 1) % config.NUM_CHOICES, 201)
        self.assertEqual(wrong.points, 0)
        self.assertEqual(g.correct, 2)

    def test_timeout_counts_as_wrong(self):
        g = QuizGame(self.db, num_questions=2)
        g.start()
        g.next_question(0)
        r = g.submit_answer(None, config.QUESTION_TIME)
        self.assertFalse(r.is_correct)
        self.assertEqual(g.score, 0)

    def test_full_game_saves_score(self):
        g = QuizGame(self.db, num_questions=3)
        g.start()
        for _ in range(3):
            q = g.next_question(0)
            g.submit_answer(q.correct_index, 1)
            g.finish_question()
        self.assertIsNone(g.next_question(0))
        g.save("Tester")
        top = self.db.get_top_scores()
        self.assertEqual(top[0]["player_name"], "Tester")
        self.assertEqual(top[0]["correct"], 3)


if __name__ == "__main__":
    unittest.main()