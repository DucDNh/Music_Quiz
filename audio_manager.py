"""Quét thư mục nhạc và phát/dừng đoạn nhạc bằng pygame.mixer."""
import random
from pathlib import Path

import pygame

import config


def parse_filename(path):
    """'Artist - Title.mp3' -> (artist, title). Không có ' - ' thì artist='Unknown'."""
    stem = Path(path).stem.replace("_", " ").strip()
    if " - " in stem:
        artist, title = stem.split(" - ", 1)
        return artist.strip(), title.strip()
    return "Unknown", stem


def scan_music_folder(folder=config.MUSIC_DIR):
    folder = Path(folder)
    if not folder.exists():
        return []
    result = []
    for p in sorted(folder.rglob("*")):
        if p.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            artist, title = parse_filename(p)
            result.append({"title": title, "artist": artist, "file_path": str(p)})
    return result


class AudioManager:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def play_clip(self, file_path):
        """Phát từ một vị trí ngẫu nhiên; nếu định dạng không hỗ trợ seek thì phát từ đầu."""
        try:
            pygame.mixer.music.load(file_path)
        except pygame.error:
            return False
        start = random.uniform(0, config.CLIP_START_MAX)
        try:
            pygame.mixer.music.play(start=start)
        except pygame.error:
            try:
                pygame.mixer.music.play()
            except pygame.error:
                return False
        # Nếu start vượt độ dài bài, mixer có thể không phát -> thử lại từ đầu
        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.play()
            except pygame.error:
                return False
        return True

    def stop(self):
        pygame.mixer.music.stop()

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def quit(self):
        pygame.mixer.music.stop()
        pygame.mixer.quit()