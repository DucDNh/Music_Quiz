"""Giao diện Pygame: máy trạng thái MENU -> NAME -> PLAYING -> FEEDBACK -> RESULT."""
import pygame

import config
from game_logic import NotEnoughSongsError, QuizGame

MENU, NAME, PLAYING, FEEDBACK, RESULT, HIGHSCORES = range(6)


class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, surf, font, hover=False, color=None):
        base = color or (config.COLOR_BUTTON_HOVER if hover else config.COLOR_BUTTON)
        pygame.draw.rect(surf, base, self.rect, border_radius=10)
        label = font.render(self.text, True, config.COLOR_TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


class GameUI:
    def __init__(self, db, audio):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.db, self.audio = db, audio
        self.f_big = pygame.font.SysFont(config.FONT_NAMES, 56, bold=True)
        self.f_mid = pygame.font.SysFont(config.FONT_NAMES, 30)
        self.f_small = pygame.font.SysFont(config.FONT_NAMES, 22)

        self.state = MENU
        self.running = True
        self.game: QuizGame | None = None
        self.player_name = ""
        self.message = ""
        self.last_result = None
        self.feedback_until = 0.0
        self.top_scores = []

        w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
        cx = w // 2
        self.menu_buttons = {
            "play": Button((cx - 140, 250, 280, 55), "Chơi"),
            "scores": Button((cx - 140, 325, 280, 55), "Bảng điểm"),
            "quit": Button((cx - 140, 400, 280, 55), "Thoát"),
        }
        self.back_button = Button((cx - 100, h - 90, 200, 50), "Về menu")
        self.choice_buttons = [
            Button((60, 260 + i * 80, w - 120, 65), "") for i in range(config.NUM_CHOICES)
        ]

    # ---------- tiện ích ----------
    @staticmethod
    def now():
        return pygame.time.get_ticks() / 1000.0

    def text(self, s, font, color, pos, center=False):
        surf = font.render(s, True, color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.screen.blit(surf, rect)

    # ---------- vòng lặp ----------
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(config.FPS)
        self.audio.quit()
        pygame.quit()

    # ---------- sự kiện ----------
    def handle_event(self, e):
        click = e.pos if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 else None
        if self.state == MENU and click:
            if self.menu_buttons["play"].hit(click):
                self.player_name, self.message, self.state = "", "", NAME
            elif self.menu_buttons["scores"].hit(click):
                self.top_scores = self.db.get_top_scores(config.HIGHSCORE_LIMIT)
                self.state = HIGHSCORES
            elif self.menu_buttons["quit"].hit(click):
                self.running = False
        elif self.state == NAME and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN:
                self.start_game()
            elif e.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            elif e.key == pygame.K_ESCAPE:
                self.state = MENU
            elif e.unicode.isprintable() and len(self.player_name) < config.MAX_NAME_LENGTH:
                self.player_name += e.unicode
        elif self.state == PLAYING:
            idx = None
            if click:
                for i, b in enumerate(self.choice_buttons):
                    if b.hit(click):
                        idx = i
            elif e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_9:
                idx = e.key - pygame.K_1
            if idx is not None and idx < len(self.game.current.choices):
                self.answer(idx)
        elif self.state == FEEDBACK:
            if click or (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN)):
                self.advance()
        elif self.state in (RESULT, HIGHSCORES):
            if (click and self.back_button.hit(click)) or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
            ):
                self.state = MENU

    # ---------- chuyển trạng thái ----------
    def start_game(self):
        self.game = QuizGame(self.db)
        try:
            self.game.start()
        except NotEnoughSongsError as err:
            self.message = str(err)
            return
        self.begin_question()

    def begin_question(self):
        q = self.game.next_question(self.now())
        self.audio.play_clip(q.song.file_path)
        self.state = PLAYING

    def answer(self, idx):
        self.audio.stop()
        self.last_result = self.game.submit_answer(idx, self.now())
        self.feedback_until = self.now() + config.FEEDBACK_SECONDS
        self.state = FEEDBACK

    def advance(self):
        last = self.game.index >= self.game.num_questions - 1
        self.game.finish_question()
        if last:
            self.game.save(self.player_name)
            self.state = RESULT
        else:
            self.begin_question()

    def update(self):
        now = self.now()
        if self.state == PLAYING and self.game.time_left(now) <= 0:
            self.answer(None)
        elif self.state == FEEDBACK and now >= self.feedback_until:
            self.advance()

    # ---------- vẽ ----------
    def draw(self):
        self.screen.fill(config.COLOR_BG)
        mouse = pygame.mouse.get_pos()
        w = config.SCREEN_WIDTH
        if self.state == MENU:
            self.text("♪ Music Quiz", self.f_big, config.COLOR_ACCENT, (w // 2, 150), True)
            self.text("Nghe nhạc, đoán tên bài hát", self.f_mid, config.COLOR_MUTED, (w // 2, 205), True)
            for b in self.menu_buttons.values():
                b.draw(self.screen, self.f_mid, b.hit(mouse))
        elif self.state == NAME:
            self.text("Nhập tên của bạn", self.f_mid, config.COLOR_TEXT, (w // 2, 200), True)
            box = pygame.Rect(w // 2 - 200, 250, 400, 60)
            pygame.draw.rect(self.screen, config.COLOR_PANEL, box, border_radius=8)
            self.text(self.player_name + "|", self.f_mid, config.COLOR_TEXT, box.center, True)
            self.text("Enter: bắt đầu  |  Esc: quay lại", self.f_small, config.COLOR_MUTED, (w // 2, 340), True)
            if self.message:
                self.text(self.message, self.f_small, config.COLOR_WRONG, (w // 2, 390), True)
        elif self.state in (PLAYING, FEEDBACK):
            self.draw_question(mouse)
        elif self.state == RESULT:
            g = self.game
            self.text("Kết thúc!", self.f_big, config.COLOR_ACCENT, (w // 2, 150), True)
            self.text(f"{self.player_name or 'Player'}: {g.score} điểm", self.f_mid, config.COLOR_TEXT, (w // 2, 250), True)
            self.text(f"Đúng {g.correct}/{g.num_questions} câu", self.f_mid, config.COLOR_MUTED, (w // 2, 300), True)
            self.back_button.draw(self.screen, self.f_mid, self.back_button.hit(mouse))
        elif self.state == HIGHSCORES:
            self.text("Bảng điểm", self.f_big, config.COLOR_ACCENT, (w // 2, 70), True)
            if not self.top_scores:
                self.text("Chưa có điểm nào", self.f_mid, config.COLOR_MUTED, (w // 2, 250), True)
            for i, r in enumerate(self.top_scores):
                line = f"{i + 1:>2}. {r['player_name']:<12} {r['score']:>5}  ({r['correct']}/{r['total']})  {r['played_at']}"
                self.text(line, self.f_small, config.COLOR_TEXT, (120, 130 + i * 36))
            self.back_button.draw(self.screen, self.f_mid, self.back_button.hit(mouse))

    def draw_question(self, mouse):
        g, w, now = self.game, config.SCREEN_WIDTH, self.now()
        q = g.current
        self.text(f"Câu {g.index + 1}/{g.num_questions}", self.f_small, config.COLOR_MUTED, (40, 30))
        self.text(f"Điểm: {g.score}", self.f_small, config.COLOR_ACCENT, (w - 160, 30))
        self.text("Bài hát này là gì?", self.f_big, config.COLOR_TEXT, (w // 2, 130), True)
        # thanh thời gian
        ratio = g.time_left(now) / config.QUESTION_TIME if self.state == PLAYING else 0
        bar = pygame.Rect(60, 190, w - 120, 18)
        pygame.draw.rect(self.screen, config.COLOR_PANEL, bar, border_radius=9)
        fill = bar.copy()
        fill.width = int(bar.width * ratio)
        pygame.draw.rect(self.screen, config.COLOR_ACCENT, fill, border_radius=9)

        for i, (btn, song) in enumerate(zip(self.choice_buttons, q.choices)):
            btn.text = f"{i + 1}. {song.title}"
            color = None
            if self.state == FEEDBACK:
                r = self.last_result
                if i == r.correct_index:
                    color = config.COLOR_CORRECT
                elif i == r.chosen_index:
                    color = config.COLOR_WRONG
                else:
                    color = config.COLOR_PANEL
            btn.draw(self.screen, self.f_mid, btn.hit(mouse) and self.state == PLAYING, color)
        if self.state == FEEDBACK:
            r = self.last_result
            msg = f"Đúng! +{r.points}" if r.is_correct else "Sai / hết giờ"
            self.text(f"{msg}  —  {q.song.artist}: {q.song.title}", self.f_small,
                      config.COLOR_CORRECT if r.is_correct else config.COLOR_WRONG,
                      (w // 2, config.SCREEN_HEIGHT - 40), True)