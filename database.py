"""Lớp truy cập SQLite. Chỉ module này được viết SQL."""
import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    artist    TEXT NOT NULL DEFAULT 'Unknown',
    file_path TEXT NOT NULL UNIQUE,
    genre     TEXT
);
CREATE TABLE IF NOT EXISTS scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL,
    score       INTEGER NOT NULL,
    correct     INTEGER NOT NULL,
    total       INTEGER NOT NULL,
    played_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS answers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    score_id      INTEGER NOT NULL REFERENCES scores(id) ON DELETE CASCADE,
    song_id       INTEGER REFERENCES songs(id) ON DELETE SET NULL,
    is_correct    INTEGER NOT NULL,
    response_time REAL
);
CREATE INDEX IF NOT EXISTS idx_scores_score ON scores(score DESC);
"""


@dataclass(frozen=True)
class Song:
    id: int
    title: str
    artist: str
    file_path: str
    genre: str | None = None


class Database:
    def __init__(self, path):
        path = Path(path) if path != ":memory:" else path
        if path != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------- songs ----------
    @staticmethod
    def _to_song(row):
        return Song(row["id"], row["title"], row["artist"], row["file_path"], row["genre"])

    def sync_songs(self, found):
        """Đồng bộ DB với thư mục nhạc. found: list dict(title, artist, file_path, genre?)."""
        with self.conn:
            for s in found:
                self.conn.execute(
                    """INSERT INTO songs (title, artist, file_path, genre)
                       VALUES (:title, :artist, :file_path, :genre)
                       ON CONFLICT(file_path) DO UPDATE SET
                         title = excluded.title, artist = excluded.artist""",
                    {"genre": None, **s},
                )
            paths = {s["file_path"] for s in found}
            for row in self.conn.execute("SELECT id, file_path FROM songs").fetchall():
                if row["file_path"] not in paths:
                    self.conn.execute("DELETE FROM songs WHERE id = ?", (row["id"],))

    def count_songs(self):
        return self.conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]

    def get_all_songs(self):
        rows = self.conn.execute("SELECT * FROM songs ORDER BY title").fetchall()
        return [self._to_song(r) for r in rows]

    def get_random_songs(self, n):
        rows = self.conn.execute("SELECT * FROM songs ORDER BY RANDOM() LIMIT ?", (n,)).fetchall()
        return [self._to_song(r) for r in rows]

    def get_random_distractors(self, exclude_id, n):
        rows = self.conn.execute(
            "SELECT * FROM songs WHERE id != ? ORDER BY RANDOM() LIMIT ?", (exclude_id, n)
        ).fetchall()
        return [self._to_song(r) for r in rows]

    # ---------- scores ----------
    def save_result(self, player_name, score, correct, total, answers=()):
        """Lưu ván chơi. answers: iterable (song_id, is_correct, response_time). Trả về score_id."""
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO scores (player_name, score, correct, total) VALUES (?, ?, ?, ?)",
                (player_name, score, correct, total),
            )
            score_id = cur.lastrowid
            self.conn.executemany(
                "INSERT INTO answers (score_id, song_id, is_correct, response_time) VALUES (?, ?, ?, ?)",
                [(score_id, sid, int(ok), rt) for sid, ok, rt in answers],
            )
        return score_id

    def get_top_scores(self, limit=10):
        rows = self.conn.execute(
            "SELECT player_name, score, correct, total, played_at FROM scores "
            "ORDER BY score DESC, played_at ASC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.conn.close()