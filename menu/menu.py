import pygame
import sys

from button import Button
import main

# -*- coding: UTF-8 -*-

pygame.init()
H, W = (700, 1400)
SCREEN = pygame.display.set_mode((W, H))
pygame.display.set_caption("Карамболь")

BG = pygame.image.load("assets/back.png")


def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)


def options():
    while True:
        OPTIONS_MOUSE_POS = pygame.mouse.get_pos()

        SCREEN.blit(BG, (0, 0))

        options_l = ["Прицельный результативный удар дает право продолжить серию.",'-',
                     "При выполнении удара необходимо, чтобы биток либо до соударения с прицельным ",
                     "шаром коснулся одного или нескольких бортов, или после соударения с ",
                     "прицельным шаром коснулся одного или нескольких бортов,",
                     "а затем другого прицельного шара. В противном случае - штраф.", "-",
                     "За каждую ошибку с текущего счета списывается одно очко.",
                     "Управление осуществляется исключительно мышью, фокусировка на шаре (битке) через ЛКМ, сила удара через оттягивание "]
        for i in range(len(options_l)):
            OPTIONS_TEXT = get_font(20).render(options_l[i], True, "#d7fcd4")
            OPTIONS_RECT = OPTIONS_TEXT.get_rect(center=(W/2, 300 + 20 * i))
            SCREEN.blit(OPTIONS_TEXT, OPTIONS_RECT)

        OPTIONS_BACK = Button(image=None, pos=(W/2, 660),
                              text_input="Назад", font=get_font(28), base_color="#d7fcd4", hovering_color="Purple")

        OPTIONS_BACK.changeColor(OPTIONS_MOUSE_POS)
        OPTIONS_BACK.update(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if OPTIONS_BACK.checkForInput(OPTIONS_MOUSE_POS):
                    main_menu()

        pygame.display.update()


def main_menu():
    while True:
        SCREEN.blit(BG, (0, 0))

        MENU_MOUSE_POS = pygame.mouse.get_pos()

        MENU_TEXT = get_font(80).render("Карамболь", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(W/2, 100))

        PLAY_BUTTON = Button(image=pygame.image.load("assets/play.png"), pos=(W/2, 250),
                             text_input="Начать игру", font=get_font(45), base_color="#d7fcd4", hovering_color="White")
        OPTIONS_BUTTON = Button(image=pygame.image.load("assets/opt.png"), pos=(W/2, 400),
                                text_input="Правила игры", font=get_font(45), base_color="#d7fcd4",
                                hovering_color="White")
        QUIT_BUTTON = Button(image=pygame.image.load("assets/quit.png"), pos=(W/2, 550),
                             text_input="Выход", font=get_font(45), base_color="#d7fcd4", hovering_color="White")

        SCREEN.blit(MENU_TEXT, MENU_RECT)

        for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.checkForInput(MENU_MOUSE_POS):
                    main.main()
                if OPTIONS_BUTTON.checkForInput(MENU_MOUSE_POS):
                    options()
                if QUIT_BUTTON.checkForInput(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()


main_menu()
