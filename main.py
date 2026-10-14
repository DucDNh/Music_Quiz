"""Điểm vào của Music Quiz: python main.py"""
import config
from audio_manager import AudioManager, scan_music_folder
from database import Database
from game_ui import GameUI
 
 
def main():
    db = Database(config.DB_PATH)
    db.sync_songs(scan_music_folder(config.MUSIC_DIR))
    print(f"Đã nạp {db.count_songs()} bài từ {config.MUSIC_DIR}")
    audio = AudioManager()
    try:
        GameUI(db, audio).run()
    finally:
        db.close()
 
 
if __name__ == "__main__":
    main()