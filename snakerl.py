import pygame
import neat
import time
import os
import pickle
import random
import sys
import math
pygame.font.init()

START_TIME = 0
CUR_TIME = 0

WIN_WIDTH = 952
WIN_HEIGHT = 812

MAX_GEN = 300000
GEN = 0

PREV_BEST_GENES = []

FPS = 5

MODE = 'scroll'

SNAKE_IMG = pygame.transform.scale2x(pygame.image.load("imgs\\snake.png"))
APPLE_IMG = pygame.transform.scale2x(pygame.image.load("imgs\\apple.png"))

STAT_FONT = pygame.font.SysFont("comicsans", 25)

class Snake:
    IMG = SNAKE_IMG

    def __init__(self, snake_index):
        self.img = self.IMG
        self.pos_base = self.img.get_width()
        self.x = self.pos_base * (random.randrange(WIN_WIDTH / 4, WIN_WIDTH * (3 / 4) - self.pos_base + 1) // self.pos_base)
        self.y = self.pos_base * (random.randrange(WIN_HEIGHT / 4, WIN_HEIGHT * (3 / 4) - self.pos_base + 1) // self.pos_base)
        self.dir = 'right'
        self.prev_dir = 'right'
        self.snakebody = []
        self.hunger = 35
        self.num_apples = 0
        self.snake_index = snake_index

    def move(self):
        d = self.img.get_width()

        if self.dir == 'right':
            self.x += d
        elif self.dir == 'left':
            self.x -= d
        elif self.dir == 'up':
            self.y -= d
        else:
            self.y += d

        for x, body in enumerate(self.snakebody):
            if x == 0:
                body.move(self.x, self.y)
            else:
                body.move(self.snakebody[x-1].x, self.snakebody[x-1].y)

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))
        for body in self.snakebody:
            body.draw(win)

    def collide_apple(self, apple):
        snake_mask = self.get_mask()
        apple_mask = apple.get_mask()

        offset = (self.x - apple.x, self.y - apple.y)

        if snake_mask.overlap(apple_mask, offset):
            return True
        return False

    def collide_wall(self):
        return self.x < 0 or self.y < 0 or self.x + self.img.get_width() > WIN_WIDTH or self.y + self.img.get_width() > WIN_HEIGHT

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class SnakeBody:
    IMG = SNAKE_IMG

    def __init__(self, snake):
        self.x = snake.x
        self.y = snake.y
        self.next_x = snake.x
        self.next_y = snake.y
        self.img = self.IMG

    def move(self, x, y):
        self.x = self.next_x
        self.y = self.next_y
        self.next_x = x
        self.next_y = y

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))

    def collide_apple(self, apple):
        snakebody_mask = self.get_mask()
        apple_mask = apple.get_mask()

        offset = (self.x - apple.x, self.y - apple.y)

        if snakebody_mask.overlap(apple_mask, offset):
            return True
        return False

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Apple:
    IMG = APPLE_IMG

    def __init__(self, snake):
        self.img = self.IMG
        self.pos_base = self.img.get_width()
        self.reset_loc(snake)

    def reset_loc(self, snake):
        good_coord = False
        while good_coord == False:
            good_coord = True
            self.x = self.pos_base * (random.randrange(0, WIN_WIDTH - self.pos_base + 1) // self.pos_base)
            self.y = self.pos_base * (random.randrange(0, WIN_HEIGHT - self.pos_base + 1) // self.pos_base)

            if self.x + self.pos_base > WIN_WIDTH or self.y + self.pos_base > WIN_HEIGHT:
                good_coord = False
                continue

            if snake.collide_apple(self):
                good_coord = False
                continue

            for body in snake.snakebody:
                if body.collide_apple(self):
                    good_coord = False
                    break

    def draw(self, win):
        win.blit(self.img, (self.x, self.y))

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


def draw_window(win, snakes, apples, scores, gen, pop, clock, fps, genes, ind, prev_best_genes, dist_apples, dist_walls, dist_bodies):
    global MODE
    global START_TIME
    global CUR_TIME
    pygame.display.set_caption('Snake AI')
    win.fill((0, 0, 0))

    score = 0
    snake_txt = ""
    if len(genes) > 0 and len(scores) > 0:
        if MODE == 'best':
            fitness_index = 0
            for x, g in enumerate(genes):
                if g.fitness > genes[fitness_index].fitness:
                    fitness_index = x
            snake_txt = "Current Best "
        elif MODE == 'scroll':
            fitness_index = ind
            while ind > len(snakes) - 1:
                ind -= 1
                fitness_index = ind
            snake_txt = ""
        elif MODE == 'overall best':
            fitness_index = 0
            fitness_index_b = 0
            fitness_index_f = 0
            found_best_genes = False
            for x, g in enumerate(genes):
                if g == prev_best_genes:
                    fitness_index_b = x
                    found_best_genes = True
                if g.fitness > genes[fitness_index_f].fitness:
                    fitness_index_f = x
            if found_best_genes and prev_best_genes != []:
                fitness_index = fitness_index_b
                snake_txt = "Overall Best "
            else:
                fitness_index = fitness_index_f
                snake_txt = "Current Best "

        score = scores[fitness_index]

        directions = [[0, -1], [0, 1], [-1, 0], [1, 0], [1, -1], [-1, -1], [1, 1], [-1, 1]]

        for x, dist in enumerate(dist_walls[fitness_index]):
            if dist > 0:
                if x == 1 or x == 3 or x == 4 or x == 6:
                    a_dist = dist - int(snakes[fitness_index].pos_base / 2)
                else:
                    a_dist = dist + int(snakes[fitness_index].pos_base / 2)
                x_start_pos = int(snakes[fitness_index].x + snakes[fitness_index].pos_base / 2)
                x_end_pos = a_dist * directions[x][0] + x_start_pos
                y_start_pos = int(snakes[fitness_index].y + snakes[fitness_index].pos_base / 2)
                y_end_pos = a_dist * directions[x][1] + y_start_pos
                pygame.draw.line(win, (207, 207, 207), [x_start_pos, y_start_pos], [x_end_pos, y_end_pos], 1)

        dirs = ['up', 'down', 'left', 'right', 'up-right', 'up-left', 'down-right', 'down-left']
        for x, dist in enumerate(dist_bodies[fitness_index]):
            if dist > 0:
                x_start_pos = int(snakes[fitness_index].x + snakes[fitness_index].pos_base / 2)
                x_end_pos = dist * directions[x][0] + x_start_pos
                y_start_pos = int(snakes[fitness_index].y + snakes[fitness_index].pos_base / 2)
                y_end_pos = dist * directions[x][1] + y_start_pos
                pygame.draw.line(win, (152, 247, 115), [x_start_pos, y_start_pos], [x_end_pos, y_end_pos], 3)

        for x, dist in enumerate(dist_apples[fitness_index]):
            if dist > 0:
                x_start_pos = int(snakes[fitness_index].x + snakes[fitness_index].pos_base / 2)
                x_end_pos = dist * directions[x][0] + x_start_pos
                y_start_pos = int(snakes[fitness_index].y + snakes[fitness_index].pos_base / 2)
                y_end_pos = dist * directions[x][1] + y_start_pos
                pygame.draw.line(win, (250, 100, 88), [x_start_pos, y_start_pos], [x_end_pos, y_end_pos], 3)

        apples[fitness_index].draw(win)
        snakes[fitness_index].draw(win)

        text = STAT_FONT.render(snake_txt + "Snake: #" + str(snakes[fitness_index].snake_index + 1), 1, (255, 255, 255))
        win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

        text = STAT_FONT.render("Length: " + str(len(snakes[fitness_index].snakebody) + 1), 1, (255, 255, 255))
        win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 40))

        text = STAT_FONT.render("Hunger: " + str(snakes[fitness_index].hunger), 1, (255, 255, 255))
        win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 100))

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 70))

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    text = STAT_FONT.render("Pop: " + str(pop), 1, (255, 255, 255))
    win.blit(text, (10, 40))

    text = STAT_FONT.render("Max Fps: " + (str(fps) if fps > 0 and fps < 1000 else "MAX") + " (Fps: " + str(math.ceil(clock.get_fps())) + ")", 1,
                            (255, 255, 255))
    win.blit(text, (10, 70))

    text = STAT_FONT.render("Mode: " + MODE, 1, (255, 255, 255))
    win.blit(text, (10, WIN_HEIGHT - 10 - text.get_height()))

    CUR_TIME = START_TIME + time.perf_counter()

    time_since_start = CUR_TIME
    hours = int(time_since_start / 60 / 60)
    if hours < 0:
        hours = 0
    minutes = int(time_since_start / 60) - hours * 60
    if minutes < 0:
        minutes = 0
    seconds = round(time_since_start - minutes * 60 - hours * 60 * 60)
    if seconds < 0:
        seconds = 0

    avg_time = time_since_start / gen
    hours_g = int(avg_time / 60 / 60)
    if hours_g < 0:
        hours_g = 0
    minutes_g = int(avg_time / 60) - hours_g * 60
    if minutes_g < 0:
        minutes_g = 0
    seconds_g = round(avg_time - minutes_g * 60 - hours_g * 60 * 60)
    if seconds_g < 0:
        seconds_g = 0

    total_time = ("Time: " + (("0" + str(hours)) if hours < 10 else str(hours)) + ":" + (("0" + str(minutes)) if minutes < 10 else str(minutes))
                 + ":" + (("0" + str(seconds)) if seconds < 10 else str(seconds)))

    avg_time = ("(Avg: " + (("0" + str(hours_g)) if hours_g < 10 else str(hours_g)) + ":" + (("0" + str(minutes_g)) if minutes_g < 10 else
                str(minutes_g)) + ":" + (("0" + str(seconds_g)) if seconds_g < 10 else str(seconds_g)) + ")")

    text = STAT_FONT.render(total_time + " " + avg_time, 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), WIN_HEIGHT - 10 - text.get_height()))

    pygame.display.update()


def get_inputs(snakes, apples):
    dist_all_apples = []
    dist_all_walls = []
    dist_all_bodies = []
    for x, snake in enumerate(snakes):
        dist_apple = []
        dist_wall = []
        dist_body = []
        for i in range(8):
            dist_apple.append(-1)
            dist_body.append(-1)

        # distance upwards
        dist_wall.append(snake.y)
        for i in range(0, snake.y):
            if dist_apple[0] == -1:
                if snake.x == apples[x].x and snake.y - i == apples[x].y:
                    dist_apple[0] = i
            if dist_body[0] == -1:
                for body in snake.snakebody:
                    if snake.x == body.x and snake.y - i == body.y:
                        dist_body[0] = i
                        break

        # distance downwards
        dist_wall.append(WIN_HEIGHT - snake.y)
        for i in range(snake.y, WIN_HEIGHT):
            if dist_apple[1] == -1:
                if snake.x == apples[x].x and i == apples[x].y:
                    dist_apple[1] = i - snake.y
            if dist_body[1] == -1:
                for body in snake.snakebody:
                    if snake.x == body.x and i == body.y:
                        dist_body[1] = i - snake.y
                        break

        # distance to the left
        dist_wall.append(snake.x)
        for i in range(snake.x, 0, -1):
            if dist_apple[2] == -1:
                if snake.y == apples[x].y and i == apples[x].x:
                    dist_apple[2] = snake.x - i
            if dist_body[2] == -1:
                for body in snake.snakebody:
                    if snake.y == body.y and i == body.x:
                        dist_body[2] = snake.x - i
                        break

        # distance to the right
        dist_wall.append(WIN_WIDTH - snake.x)
        for i in range(snake.x, WIN_WIDTH):
            if dist_apple[3] == -1:
                if snake.y == apples[x].y and i == apples[x].x:
                    dist_apple[3] = i - snake.x
            if dist_body[3] == -1:
                for body in snake.snakebody:
                    if snake.y == body.y and i == body.x:
                        dist_body[3] = i - snake.x
                        break

        # distance up-right
        for i in range(WIN_WIDTH * 2):
            if snake.x + i == WIN_WIDTH or snake.y - i == 0:
                dist_wall.append(i)
                break
            if dist_apple[4] == -1:
                if snake.x + i == apples[x].x and snake.y - i == apples[x].y:
                    dist_apple[4] = i
            if dist_body[4] == -1:
                for body in snake.snakebody:
                    if snake.x + i == body.x and snake.y - i == body.y:
                        dist_body[4] = i
                        break

        # distance up-left
        for i in range(WIN_WIDTH * 2):
            if snake.x - i == 0 or snake.y - i == 0:
                dist_wall.append(i)
                break
            if dist_apple[5] == -1:
                if snake.x - i == apples[x].x and snake.y - i == apples[x].y:
                    dist_apple[5] = i
            if dist_body[5] == -1:
                for body in snake.snakebody:
                    if snake.x - i == body.x and snake.y - i == body.y:
                        dist_body[5] = i
                        break

        # distance down-right
        for i in range(WIN_WIDTH * 2):
            if snake.x + i == WIN_WIDTH or snake.y + i == WIN_HEIGHT:
                dist_wall.append(i)
                break
            if dist_apple[6] == -1:
                if snake.y + i == apples[x].y and snake.x + i == apples[x].x:
                    dist_apple[6] = i
            if dist_body[6] == -1:
                for body in snake.snakebody:
                    if snake.y + i == body.y and snake.x + i == body.x:
                        dist_body[6] = i
                        break

        # distance down-left
        for i in range(WIN_WIDTH * 2):
            if snake.x - i == 0 or snake.y + i == WIN_HEIGHT:
                dist_wall.append(i)
                break
            if dist_apple[7] == -1:
                if snake.y + i == apples[x].y and snake.x - i == apples[x].x:
                    dist_apple[7] = i
            if dist_body[7] == -1:
                for body in snake.snakebody:
                    if snake.y + i == body.y and snake.x - i == body.x:
                        dist_body[7] = i
                        break

        dist_all_apples.append(dist_apple)
        dist_all_walls.append(dist_wall)
        dist_all_bodies.append(dist_body)

    return dist_all_apples, dist_all_walls, dist_all_bodies


def eval_genomes(genomes, config):
    global GEN
    global FPS
    global MODE
    global PREV_BEST_GENES
    global CUR_TIME

    if os.path.exists("checkpoints\\snake-ai-gen-" + str(GEN - 6)):
        os.remove("checkpoints\\snake-ai-gen-" + str(GEN - 6))

    GEN += 1

    best_genes = []
    best_genes_fitness = []

    nets = []
    genes = []
    snakes = []
    apples = []
    scores = []

    ind = 0
    for _, g in genomes:
        g.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        snake = Snake(ind)
        snake.snakebody.append(SnakeBody(snake))
        snake.snakebody.append(SnakeBody(snake.snakebody[-1]))
        snake.snakebody.append(SnakeBody(snake.snakebody[-1]))
        snakes.append(snake)
        apples.append(Apple(snake))
        genes.append(g)
        scores.append(0)
        ind += 1

    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    s_ind = 0

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

                save_data = (GEN - 1, FPS, MODE, PREV_BEST_GENES, CUR_TIME)

                pickle_out = open("saved_data.pickle", "wb")
                pickle.dump(save_data, pickle_out)
                pickle_out.close()

                pygame.quit()
                quit()
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    FPS += 5

                if event.key == pygame.K_DOWN:
                    FPS -= 5

                if event.key == pygame.K_SPACE:
                    if MODE == 'scroll':
                        MODE = 'best'
                    elif MODE == 'best':
                        MODE = 'overall best'
                    elif MODE == 'overall best':
                        MODE = 'scroll'

                if MODE == 'scroll':
                    if event.key == pygame.K_LEFT:
                        s_ind -= 1
                    if event.key == pygame.K_RIGHT:
                        s_ind += 1

        if s_ind < 0:
            s_ind = len(snakes) - 1

        if s_ind > len(snakes) - 1:
            s_ind = 0

        if len(snakes) == 0:
            run = False
            break

        for x, snake in enumerate(snakes):
            dist_apple = []
            dist_wall = []
            dist_body = []
            for i in range(8):
                dist_apple.append(-1)
                dist_body.append(-1)

            # distance upwards
            dist_wall.append(snake.y)
            for i in range(0, snake.y):
                if dist_apple[0] == -1:
                    if snake.x == apples[x].x and snake.y - i == apples[x].y:
                        dist_apple[0] = i
                if dist_body[0] == -1:
                    for body in snake.snakebody:
                        if snake.x == body.x and snake.y - i == body.y:
                            dist_body[0] = i
                            break

            # distance downwards
            dist_wall.append(WIN_HEIGHT - snake.y)
            for i in range(snake.y, WIN_HEIGHT):
                if dist_apple[1] == -1:
                    if snake.x == apples[x].x and i == apples[x].y:
                        dist_apple[1] = i - snake.y
                if dist_body[1] == -1:
                    for body in snake.snakebody:
                        if snake.x == body.x and i == body.y:
                            dist_body[1] = i - snake.y
                            break

            # distance to the left
            dist_wall.append(snake.x)
            for i in range(snake.x, 0, -1):
                if dist_apple[2] == -1:
                    if snake.y == apples[x].y and i == apples[x].x:
                        dist_apple[2] = snake.x - i
                if dist_body[2] == -1:
                    for body in snake.snakebody:
                        if snake.y == body.y and i == body.x:
                            dist_body[2] = snake.x - i
                            break

            # distance to the right
            dist_wall.append(WIN_WIDTH - snake.x)
            for i in range(snake.x, WIN_WIDTH):
                if dist_apple[3] == -1:
                    if snake.y == apples[x].y and i == apples[x].x:
                        dist_apple[3] = i - snake.x
                if dist_body[3] == -1:
                    for body in snake.snakebody:
                        if snake.y == body.y and i == body.x:
                            dist_body[3] = i - snake.x
                            break

            # distance up-right
            for i in range(WIN_WIDTH * 2):
                if snake.x + i == WIN_WIDTH or snake.y - i == 0:
                    dist_wall.append(i)
                    break
                if dist_apple[4] == -1:
                    if snake.x + i == apples[x].x and snake.y - i == apples[x].y:
                        dist_apple[4] = i
                if dist_body[4] == -1:
                    for body in snake.snakebody:
                        if snake.x + i == body.x and snake.y - i == body.y:
                            dist_body[4] = i
                            break

            # distance up-left
            for i in range(WIN_WIDTH * 2):
                if snake.x - i == 0 or snake.y - i == 0:
                    dist_wall.append(i)
                    break
                if dist_apple[5] == -1:
                    if snake.x - i == apples[x].x and snake.y - i == apples[x].y:
                        dist_apple[5] = i
                if dist_body[5] == -1:
                    for body in snake.snakebody:
                        if snake.x - i == body.x and snake.y - i == body.y:
                            dist_body[5] = i
                            break

            # distance down-right
            for i in range(WIN_WIDTH * 2):
                if snake.x + i == WIN_WIDTH or snake.y + i == WIN_HEIGHT:
                    dist_wall.append(i)
                    break
                if dist_apple[6] == -1:
                    if snake.y + i == apples[x].y and snake.x + i == apples[x].x:
                        dist_apple[6] = i
                if dist_body[6] == -1:
                    for body in snake.snakebody:
                        if snake.y + i == body.y and snake.x + i == body.x:
                            dist_body[6] = i
                            break

            # distance down-left
            for i in range(WIN_WIDTH * 2):
                if snake.x - i == 0 or snake.y + i == WIN_HEIGHT:
                    dist_wall.append(i)
                    break
                if dist_apple[7] == -1:
                    if snake.y + i == apples[x].y and snake.x - i == apples[x].x:
                        dist_apple[7] = i
                if dist_body[7] == -1:
                    for body in snake.snakebody:
                        if snake.y + i == body.y and snake.x - i == body.x:
                            dist_body[7] = i
                            break

            old_dist_to_apple = ((snake.x - apples[x].x) ** 2 + (snake.y - apples[x].y) ** 2) ** 0.5

            output = nets[x].activate((dist_apple[0], dist_apple[1], dist_apple[2], dist_apple[3], dist_apple[4],
                                        dist_apple[5], dist_apple[6], dist_apple[7], dist_wall[0], dist_wall[1],
                                        dist_wall[2], dist_wall[3], dist_wall[4], dist_wall[5], dist_wall[6],
                                        dist_wall[7], dist_body[0], dist_body[1], dist_body[2], dist_body[3],
                                        dist_body[4], dist_body[5], dist_body[6], dist_body[7], old_dist_to_apple,
                                        snake.hunger))

            max_output_ind = output.index(max(output))
            output_labels = ['right', 'left', 'up', 'down']
            snake.dir = output_labels[max_output_ind]

            snake.move()

            new_dist_to_apple = ((snake.x - apples[x].x) ** 2 + (snake.y - apples[x].y) ** 2) ** 0.5

            genes[x].fitness += 0.1

            invalid_dir = False
            if snake.dir == 'right' and snake.prev_dir == 'left':
                invalid_dir = True
            elif snake.dir == 'left' and snake.prev_dir == 'right':
                invalid_dir = True
            elif snake.dir == 'up' and snake.prev_dir == 'down':
                invalid_dir == True
            elif snake.dir == 'down' and snake.prev_dir == 'up':
                invalid_dir == True

            if invalid_dir and len(snake.snakebody) > 0:
                genes[x].fitness -= 1
                best_genes_fitness.append(genes[x].fitness)
                best_genes.append(genes[x])
                snakes.pop(x)
                apples.pop(x)
                nets.pop(x)
                genes.pop(x)
                scores.pop(x)
                continue
            else:
                snake.prev_dir = snake.dir

            if snake.collide_apple(apples[x]):
                apples[x].reset_loc(snake)
                scores[x] += 1
                snake.hunger += 25
                genes[x].fitness += 5
                if len(snake.snakebody) == 0:
                    snake.snakebody.append(SnakeBody(snake))
                else:
                    snake.snakebody.append(SnakeBody(snake.snakebody[-1]))
                    snake.snakebody.append(SnakeBody(snake.snakebody[-1]))
                    snake.snakebody.append(SnakeBody(snake.snakebody[-1]))
                    snake.snakebody.append(SnakeBody(snake.snakebody[-1]))
                snake.num_apples += 1
            else:
                snake.hunger -= 1
                if snake.hunger == 0:
                    genes[x].fitness -= 1
                    best_genes_fitness.append(genes[x].fitness)
                    best_genes.append(genes[x])
                    snakes.pop(x)
                    apples.pop(x)
                    nets.pop(x)
                    genes.pop(x)
                    scores.pop(x)
                    continue

            if snake.collide_wall():
                genes[x].fitness -= 1
                best_genes_fitness.append(genes[x].fitness)
                best_genes.append(genes[x])
                snakes.pop(x)
                apples.pop(x)
                nets.pop(x)
                genes.pop(x)
                scores.pop(x)
                continue

            for body in snake.snakebody:
                if snake.x == body.x and snake.y == body.y:
                    genes[x].fitness -= 1
                    best_genes_fitness.append(genes[x].fitness)
                    best_genes.append(genes[x])
                    snakes.pop(x)
                    apples.pop(x)
                    nets.pop(x)
                    genes.pop(x)
                    scores.pop(x)
                    break

        dist_all_apples, dist_all_walls, dist_all_bodies = get_inputs(snakes, apples)
        draw_window(win, snakes, apples, scores, GEN, len(snakes), clock, FPS, genes, s_ind, PREV_BEST_GENES, dist_all_apples,
            dist_all_walls, dist_all_bodies)

    if len(best_genes) > 0 and len(best_genes_fitness) > 0:
        PREV_BEST_GENES = best_genes[best_genes_fitness.index(max(best_genes_fitness))]


def run(config_path):
    global GEN
    global FPS
    global MODE
    global PREV_BEST_GENES
    global START_TIME
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    if os.path.exists("saved_data.pickle"):
        pickle_in = open("saved_data.pickle", "rb")
        load_data = pickle.load(pickle_in)

        GEN = load_data[0] - 1
        FPS = load_data[1]
        MODE = load_data[2]
        PREV_BEST_GENES = load_data[3]
        START_TIME = load_data[4]

        p = neat.Checkpointer.restore_checkpoint("checkpoints\\snake-ai-gen-" + str(GEN + 1))
        print("Starting from saved simulation...")
    else:
        GEN = 0
        FPS = 5
        MODE = 'scroll'
        PREV_BEST_GENES = []
        START_TIME = 0

        p = neat.Population(config)
        print("Starting new simulation...")

    # give output
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    cp = neat.Checkpointer(generation_interval=1, time_interval_seconds=600, filename_prefix='checkpoints\\snake-ai-gen-')
    p.add_reporter(cp)

    winner = p.run(eval_genomes, MAX_GEN)

    pickle_out = open("best_snake.pickle", "wb")
    pickle.dump(winner, pickle_out)
    pickle_out.close()


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
