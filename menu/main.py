import sys
import pygame
import pymunk
import pymunk.pygame_util
import numpy as np
from button import Button
from math import sqrt, atan2, degrees, pi, sin, cos, radians

pymunk.pygame_util.positive_y_is_up = False
H, W = (700, 1400)


def draw_line_dashed(surface, color, start_pos, end_pos, width=1, dash_length=10, exclude_corners=True):
    start_pos = np.array(start_pos)
    end_pos = np.array(end_pos)
    length = np.linalg.norm(end_pos - start_pos)
    dash_amount = int(length / dash_length)
    dash_knots = np.array([np.linspace(start_pos[i], end_pos[i], dash_amount) for i in range(2)]).transpose()
    return [pygame.draw.line(surface, color, tuple(dash_knots[n]), tuple(dash_knots[n + 1]), width)
            for n in range(int(exclude_corners), dash_amount - int(exclude_corners), 2)]


class GameState:
    def __init__(self):
        self.check = False
        self.player1_score = 0
        self.player2_score = 0
        self.current_player = "1"

    def change_turn(self):  # проверка ивентов для счета
        if self.is_player1_turn():
            self.player1_score += 1 if self.check else -1
            if not self.check:
                self.current_player = "2"
        elif self.is_player2_turn():
            self.player2_score += 1 if self.check else -1
            if not self.check:
                self.current_player = "1"
        if self.check: self.check = False

    def is_player1_turn(self):
        return self.current_player == "1"

    def is_player2_turn(self):
        return self.current_player == "2"


def _create_cue():
    cue = pygame.image.load('assets/cue.png').convert_alpha()
    return cue


def rotate(image, origin, angle, pivot):  # функция поворота изображения, на вход получает изображение, координаты
    # точки вокруг которой идет вращение, угол доповорота изображения(чтобы спрайт отображался корректно,
    # а не под тем же углом что и на пнг-шке) и координаты точки вращения относительно изображения
    image_rect = image.get_rect(topleft=(origin[0] - pivot[0], origin[1] - pivot[1]))
    offset_center_to_pivot = pygame.math.Vector2(origin) - image_rect.center
    rotated_offset = offset_center_to_pivot.rotate(-angle)
    rotated_image_center = (origin[0] - rotated_offset.x, origin[1] - rotated_offset.y)
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
    return rotated_image, rotated_image_rect  # возвращает повернутое изображение и Rect того изображения


def is_hit_to_border(ball):
    return not (80 < ball.position.x < (W - 80)) or not (80 < ball.position.y < (H - 80))


class Game:
    def __init__(self):
        self.dict_events = dict()
        self.ball_selected = 0
        self.corr = (W, H)
        self.k = 1
        self._space = pymunk.Space()
        self.surf = pygame.Surface((W, H))
        self._space.damping = 0.6  # Трение шара о стол
        self._create_borders(0)
        self.is_selected_ball = False
        self.radius = 14  # радиус шара

        self._3_ball = self._create_ball(1, (255, 0, 0, 255))  # прицельный
        self._3_ball.position = W * 0.75, H / 2

        self._2_ball = self._create_ball(3, (255, 255, 0, 255))  # игрок № 2
        self._2_ball.position = W * 0.25, H / 2

        self._1_ball = self._create_ball(2, (255, 255, 255, 255))  # игрок №1
        self._1_ball.position = W * 0.25, H / 2 - 45

        self.cue = _create_cue()

        self.move = 0

        self.pivot_1 = False
        self.counter = 0
        self.angle = -36
        self.pivot_x, self.pivot_y = (-12, 9)
        self.pivot = (self.pivot_x, self.pivot_y + self.cue.get_size()[1])
        self.hit_cue_to_ball = False
        self.cont_ball = 0
        self.list_of_balls = {1: self._1_ball, 2: self._2_ball, 3: self._3_ball}

        self.game_state = GameState()

    def _create_borders(self, collision_type):
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (0, 0)

        thickness = 60
        width, height = W, H

        coordinates = [
            (0, 0),
            (0, height),
            (width, height),
            (width, 0)
        ]

        self._space.add(body)
        for i in range(len(coordinates) + 1):
            s = pymunk.Segment(
                body,
                coordinates[i % len(coordinates)],
                coordinates[(i + 1) % len(coordinates)],
                thickness
            )
            s.friction = 1
            s.elasticity = 1
            s.collision_type = collision_type
            self._space.add(s)

    def _create_ball(self, collision_type, color=(0, 0, 0, 255)):
        body = pymunk.Body()
        shape = pymunk.Circle(body, self.radius)
        shape.mass = 1
        shape.friction = 0.03
        shape.elasticity = 1.0
        shape.collision_type = collision_type
        shape.color = color
        self._space.add(body, shape)
        return body

    def is_idle(self):
        def f(v):
            self.move = abs(v[0]) + abs(v[1])
            return (abs(v[0]) + abs(v[1])) <= 2

        return f(self._1_ball.velocity) and f(self._2_ball.velocity) and f(self._3_ball.velocity)

    def step(self, time): self._space.step(time)

    def draw(self, screen):
        draw_options = pymunk.pygame_util.DrawOptions(screen)
        self._space.debug_draw(draw_options)
        for i in range(1, len(self.list_of_balls) + 1):
            if abs(self.list_of_balls[i].velocity[0]) + abs(self.list_of_balls[i].velocity[1]) <= 2: self.list_of_balls[i].velocity = pymunk.vec2d.Vec2d(0, 0)
        if not self.is_selected_ball and self.move <= 2:
            self.ball_selected = self.select(screen)
            self.cue_process(self.ball_selected, screen)
        elif self.move <= 2:
            self.cue_process(self.ball_selected, screen)
        else:
            self.rules_process()
            try:
                d = self.dict_events
                s = list(self.dict_events.keys())
                if 'ball' in s[0]:
                    self.game_state.check = True if 'ball' in s[2] and 'board' in s[1] and d[s[1]] == 1 and d[
                        s[0]] == 1 and d[s[2]] == 1 else False
                else:
                    self.game_state.check = True if 'ball' in s[2] and 'ball' in s[1] and d[s[1]] == 1 and d[
                        s[2]] == 1 else False
            except IndexError: pass

    def select(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        F = lambda x1, y1, x2, y2, r: sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) < r
        if F(mouse_pos[0], mouse_pos[1], self._1_ball.position[0], self._1_ball.position[1],
             self.radius) and self.game_state.current_player == '1':
            pygame.draw.circle(screen, (0, 255, 255), self._1_ball.position, self.radius + 10, 5)
            self.k = 1

        elif F(mouse_pos[0], mouse_pos[1], self._2_ball.position[0], self._2_ball.position[1],
               self.radius) and self.game_state.current_player == '2':
            pygame.draw.circle(screen, (0, 255, 255), self._2_ball.position, self.radius + 10, 5)
            self.k = 2
        else: self.k = 0
        return self.k

    def cue_process(self, ball, screen):
        cue = self.cue
        if ball != 0:
            cor = self.list_of_balls[ball].position
        else:
            return
        F = lambda x1, y1, x2, y2, r: sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) < r
        mouse_pos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and F(mouse_pos[0], mouse_pos[1], cor[0], cor[1], self.radius):
            self.is_selected_ball = True
            self.corr = self.list_of_balls[ball].position
        elif pygame.mouse.get_pressed()[1] or (
                pygame.mouse.get_pressed()[0] and not F(mouse_pos[0], mouse_pos[1], cor[0], cor[1], self.radius)):
            self.is_selected_ball = False
        if self.is_selected_ball:
            w, h = self.cue.get_size()
            #---нахождение угла позиции курсора относительно выбранного шара
            dx, dy = mouse_pos[0] - self.corr[0], mouse_pos[1] - self.corr[1]
            rads = atan2(-dy, dx)
            rads %= 2 * pi
            degs = degrees(rads)
            #---
            ang = degs
            if pygame.mouse.get_pressed()[2]:
                draw_line_dashed(screen, '#C6C3B5', mouse_pos,
                                 (2 * self.corr[0] - mouse_pos[0], 2 * self.corr[1] - mouse_pos[1]))
                if self.pivot_1:
                    self.counter = (sqrt((mouse_pos[0] - cor[0]) ** 2 + (mouse_pos[1] - cor[1]) ** 2) - sqrt(
                        (self.pivot_1[0] - cor[0]) ** 2 + (self.pivot_1[1] - cor[1]) ** 2)) / 20
                    if self.counter > 1:
                        self.pivot = (self.pivot_x * self.counter, self.pivot_y * self.counter + h)
                        if not self.hit_cue_to_ball: self.hit_cue_to_ball = True
                    else:
                        self.pivot = (self.pivot_x, self.pivot_y + h)
                else:
                    self.pivot_1, self.pivot = mouse_pos, (self.pivot_x, self.pivot_y + h)
                self.cont_ball = self.counter

            elif self.pivot[0] < self.pivot_x and self.pivot[1] > self.pivot_y:
                self.counter -= 2
                self.pivot = (self.pivot_x * self.counter, self.pivot_y * self.counter + h)
            else:
                if self.cont_ball <= 0: self.cont_ball = 0
                speed, angle_speed = (self.cont_ball * 100, ang + 180)
                if self.cont_ball > 0:
                    x, y = (cos(radians(angle_speed)) * speed, sin(radians(angle_speed)) * speed)
                    if abs(x) > 3000:
                        x = 3000 if x > 0 else -3000
                    if abs(y) > 3000:
                        y = 3000 if y > 0 else -3000
                else:
                    x, y = 0, 0
                if self.hit_cue_to_ball:
                    self.list_of_balls[ball].velocity = pymunk.vec2d.Vec2d(x, -y)
                    self.hit_cue_to_ball = False
                    self.cont_ball = 0
                    self.is_selected_ball = False
                ang, self.pivot_1, self.pivot = degs, False, (self.pivot_x, self.pivot_y + h)
            screen.blit(*rotate(cue, self.corr, ang - 36, self.pivot))

    def rules_process(self):
        count = self.ball_selected
        ball = self.list_of_balls[self.ball_selected]
        bw = self.is_hit_between_balls(ball, count)
        if is_hit_to_border(ball):
            if 'board' in self.dict_events.keys():
                self.dict_events['board'] += 1
            else:
                self.dict_events |= {'board': 1}
        elif bw:
            self.dict_events |= {f'ball {bw[1]}': 1}

    def is_hit_between_balls(self, ball, c):
        x, y = ball.position
        ball1 = c - 1
        if ball1 <= 0: ball1 += 3
        ball2 = c - 2
        if c - 2 <= 0: ball2 += 3
        x1, y1 = self.list_of_balls[ball1].position
        x2, y2 = self.list_of_balls[ball2].position
        if sqrt((x - x1) ** 2 + (y - y1) ** 2) <= self.radius * 2: return (
            self.list_of_balls.get(list(self.list_of_balls)[c - 1]), ball1)
        if sqrt((x - x2) ** 2 + (y - y2) ** 2) <= self.radius * 2:
            return self.list_of_balls.get(list(self.list_of_balls)[c - 2]), ball2
        else:
            return False


def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)


global pause_menu, a, c
BG = pygame.image.load("assets/back.png")


def menu(screen):
    global pause_menu, a, c
    screen.blit(BG, (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    PLAY_BUTTON = Button(image=pygame.image.load("assets/opt.png"), pos=(W/2, 250),
                         text_input="Продолжить игру", font=get_font(45), base_color="#d7fcd4",
                         hovering_color="White")
    OPTIONS_BUTTON = Button(image=pygame.image.load("assets/opt.png"), pos=(W/2, 400),
                            text_input="Правила игры", font=get_font(45), base_color="#d7fcd4",
                            hovering_color="White")
    QUIT_BUTTON = Button(image=pygame.image.load("assets/opt.png"), pos=(W/2, 550),
                         text_input="Выход в главное меню", font=get_font(45), base_color="#d7fcd4",
                         hovering_color="White")

    for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
        button.changeColor(mouse_pos)
        button.update(screen)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if PLAY_BUTTON.checkForInput(mouse_pos):
                pause_menu = False
                b = pygame.time.get_ticks()
                if c != 0: c += (b - a)
            if OPTIONS_BUTTON.checkForInput(mouse_pos):
                options(screen)
            if QUIT_BUTTON.checkForInput(mouse_pos):
                from menu import main_menu as mn
                mn()
    pygame.display.update()


def options(screen):
    while True:
        screen.blit(BG, (0, 0))
        OPTIONS_MOUSE_POS = pygame.mouse.get_pos()
        options_l = ["Прицельный результативный удар дает право продолжить серию.", '-',
                     "При выполнении удара необходимо, чтобы биток либо до соударения с прицельным ",
                     "шаром коснулся одного или нескольких бортов, или после соударения с ",
                     "прицельным шаром коснулся одного или нескольких бортов,",
                     "а затем другого прицельного шара. В противном случае - штраф.", "-",
                     "За каждую ошибку с текущего счета списывается одно очко.",
                     "Управление осуществляется исключительно мышью, фокусировка на шаре (битке) через ЛКМ, сила удара через оттягивание "]
        for i in range(len(options_l)):
            OPTIONS_TEXT = get_font(20).render(options_l[i], True, "#d7fcd4")
            OPTIONS_RECT = OPTIONS_TEXT.get_rect(center=(W/2, 300 + 20 * i))
            screen.blit(OPTIONS_TEXT, OPTIONS_RECT)

        OPTIONS_BACK = Button(image=None, pos=(W/2, 660),
                              text_input="Назад", font=get_font(28), base_color="#d7fcd4", hovering_color="Purple")

        OPTIONS_BACK.changeColor(OPTIONS_MOUSE_POS)
        OPTIONS_BACK.update(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if OPTIONS_BACK.checkForInput(OPTIONS_MOUSE_POS):
                    menu(screen)
                    return

        pygame.display.update()


def win_screen(screen, num_player, time):
    screen.blit(BG, (0, 0))
    mouse_pos = pygame.mouse.get_pos()
    win_says = [f'Победил игрок номер - {num_player}', f'Время игры - {time}']
    for i in range(len(win_says)):
        OPTIONS_TEXT = get_font(24).render(win_says[i], True, "#d7fcd4")
        OPTIONS_RECT = OPTIONS_TEXT.get_rect(center=(W / 2, 200 + 20 * i))
        screen.blit(OPTIONS_TEXT, OPTIONS_RECT)
    OPTIONS_BUTTON = Button(image=pygame.image.load("assets/opt.png"), pos=(W / 2, 400),
                            text_input="Начать заново", font=get_font(45), base_color="#d7fcd4",
                            hovering_color="White")
    QUIT_BUTTON = Button(image=pygame.image.load("assets/opt.png"), pos=(W / 2, 550),
                         text_input="Выход в главное меню", font=get_font(45), base_color="#d7fcd4",
                         hovering_color="White")

    for button in [OPTIONS_BUTTON, QUIT_BUTTON]:
        button.changeColor(mouse_pos)
        button.update(screen)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if OPTIONS_BUTTON.checkForInput(mouse_pos):
                from main import main as mn
                mn()
            if QUIT_BUTTON.checkForInput(mouse_pos):
                from menu import main_menu as mn
                mn()
    pygame.display.update()


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Карамболь")
    pygame.mouse.set_visible(True)
    clock = pygame.time.Clock()
    game = Game()
    font = pygame.font.Font("assets/font.ttf", 24)
    is_turn_in_process = False
    global pause_menu, a, c
    c, out, b, ticks, a = 0, 0, 0, 0, 0
    pause_menu = False

    while True:
        for event in pygame.event.get():  # Выход
            if event.type == pygame.QUIT:
                sys.exit(0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pause_menu = True
                a = pygame.time.get_ticks()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_EQUALS:
                game.game_state.player1_score += 1
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_MINUS:
                game.game_state.player1_score -= 1
        if game.game_state.player1_score >= 30: win_screen(screen, 1, out)
        elif game.game_state.player2_score >= 30: win_screen(screen, 2, out)
        elif not pause_menu:
            if not game.is_idle():
                is_turn_in_process = True

            if game.is_idle() and is_turn_in_process:
                game.game_state.change_turn()
                game.dict_events = {}
                is_turn_in_process = False
            screen.fill((23, 85, 50))

            fps = clock.get_fps()
            fps = fps if fps != 0 else 60
            game.step(1 / fps)
            game.draw(screen)

            if game.move != 0:
                if c == 0:
                    c = pygame.time.get_ticks()
            ticks = pygame.time.get_ticks() - c
            millis = int(ticks % 1000 / 100)
            seconds = int(ticks / 1000 % 60)
            minutes = int(ticks / 60000 % 24)
            out = '{minutes:02d} мин. {seconds:02d} сек. {millis:d} мс.'.format(minutes=minutes, millis=millis,
                                                                                   seconds=seconds)
            if c == 0: out = '00 мин. 00 сек. 00 мс.'
            time = font.render(out, True, [50, 50, 50])
            screen.blit(time, [575, 18])

            players = font.render('Ход: Игрок 1 (белый биток)' if game.game_state.is_player1_turn() else 'Ход: Игрок 2 (желтый биток)', True, [50, 50, 50])
            screen.blit(players, [1000, 18])  # вывод счетчиков и данных о ходе

            score1 = font.render(f'Счет игрока 1: {game.game_state.player1_score}', True, [50, 50, 50])
            screen.blit(score1, [450, 655])

            score2 = font.render(f'Счет игрока 2: {game.game_state.player2_score}', True, [50, 50, 50])
            screen.blit(score2, [750, 655])
        else:
            menu(screen)
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    sys.exit(main())
