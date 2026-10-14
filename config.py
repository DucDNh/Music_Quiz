"""Hằng số cấu hình cho Music Quiz. Mọi module khác chỉ đọc từ đây."""
import sys
from pathlib import Path

# ---- Đường dẫn ----
# Khi chạy từ file .exe (PyInstaller), nhạc và DB nằm cạnh file .exe
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
MUSIC_DIR = BASE_DIR / "assets" / "music"
DB_PATH = BASE_DIR / "data" / "music_quiz.db"
SUPPORTED_EXTENSIONS = (".mp3", ".ogg", ".wav")

# ---- Luật chơi ----
NUM_QUESTIONS = 10          # số câu mỗi ván
NUM_CHOICES = 4             # số đáp án mỗi câu
MIN_SONGS = NUM_CHOICES     # cần tối thiểu từng này bài để chơi
QUESTION_TIME = 15.0        # giây cho mỗi câu (cũng là độ dài đoạn nhạc phát)
FEEDBACK_SECONDS = 2.0      # thời gian hiện đáp án đúng
POINTS_CORRECT = 100
POINTS_TIME_BONUS_MAX = 50  # thưởng thêm nếu trả lời nhanh
CLIP_START_MAX = 40.0       # đoạn nhạc bắt đầu ngẫu nhiên trong 0..N giây đầu
MAX_NAME_LENGTH = 12
HIGHSCORE_LIMIT = 10

# ---- Giao diện ----
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Music Quiz"
FONT_NAMES = "segoeui,arial,dejavusans,liberationsans"  # có hỗ trợ tiếng Việt

COLOR_BG = (24, 24, 38)
COLOR_PANEL = (40, 40, 64)
COLOR_BUTTON = (70, 70, 120)
COLOR_BUTTON_HOVER = (100, 100, 170)
COLOR_TEXT = (240, 240, 250)
COLOR_MUTED = (160, 160, 190)
COLOR_CORRECT = (60, 180, 100)
COLOR_WRONG = (200, 70, 70)
COLOR_ACCENT = (250, 200, 80)