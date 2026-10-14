"""Luật chơi thuần Python — không import pygame để dễ test."""
import random
from dataclasses import dataclass, field

import config
from database import Database, Song


class NotEnoughSongsError(Exception):
    pass


@dataclass
class Question:
    song: Song
    choices: list
    correct_index: int
    started_at: float


@dataclass
class AnswerResult:
    is_correct: bool
    points: int
    correct_index: int
    chosen_index: int | None
    response_time: float


class QuizGame:
    def __init__(self, db: Database, num_questions=config.NUM_QUESTIONS):
        self.db = db
        self.num_questions = num_questions
        self.songs: list[Song] = []
        self.index = -1
        self.score = 0
        self.correct = 0
        self.current: Question | None = None
        self.history: list[tuple] = []  # (song_id, is_correct, response_time)

    # ---- vòng đời ván chơi ----
    def start(self):
        if self.db.count_songs() < config.MIN_SONGS:
            raise NotEnoughSongsError(
                f"Cần ít nhất {config.MIN_SONGS} bài trong {config.MUSIC_DIR}"
            )
        self.songs = self.db.get_random_songs(self.num_questions)
        self.num_questions = len(self.songs)
        self.index, self.score, self.correct = -1, 0, 0
        self.current, self.history = None, []

    def is_finished(self):
        return self.index >= self.num_questions - 1 and self.current is None

    def next_question(self, now):
        if self.index + 1 >= self.num_questions:
            self.current = None
            return None
        self.index += 1
        song = self.songs[self.index]
        distractors = self.db.get_random_distractors(song.id, config.NUM_CHOICES - 1)
        choices = [song] + distractors
        random.shuffle(choices)
        self.current = Question(song, choices, choices.index(song), now)
        return self.current

    def time_left(self, now):
        if not self.current:
            return 0.0
        return max(0.0, config.QUESTION_TIME - (now - self.current.started_at))

    def submit_answer(self, chosen_index, now):
        """chosen_index=None nghĩa là hết giờ."""
        q = self.current
        elapsed = min(now - q.started_at, config.QUESTION_TIME)
        ok = chosen_index is not None and chosen_index == q.correct_index
        points = 0
        if ok:
            remaining_ratio = 1 - elapsed / config.QUESTION_TIME
            points = config.POINTS_CORRECT + int(config.POINTS_TIME_BONUS_MAX * remaining_ratio)
            self.score += points
            self.correct += 1
        self.history.append((q.song.id, ok, round(elapsed, 2)))
        result = AnswerResult(ok, points, q.correct_index, chosen_index, elapsed)
        return result

    def finish_question(self):
        """Gọi sau khi hiện feedback xong để chuyển trạng thái."""
        if self.index >= self.num_questions - 1:
            self.current = None

    def save(self, player_name):
        name = (player_name.strip() or "Player")[: config.MAX_NAME_LENGTH]
        return self.db.save_result(name, self.score, self.correct, self.num_questions, self.history)