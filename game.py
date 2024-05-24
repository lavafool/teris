import sys
import pygame
from settings import *
import random
import numpy as np

pygame.init()
pygame.font.init()

class Block():
    def __init__(self, init_y=0):
        self.coord = [0, init_y]
        self.rand()
    
    def rand(self):
        self.name = random.choice(['L','reL','Z','reZ','T','I','O'])
        self.color = BLOCK_DICT[self.name]['color']
        self.idx = random.randint(0, len(BLOCK_DICT[self.name]['shape_list'])-1)
        self.shape = BLOCK_DICT[self.name]['shape_list'][self.idx]
        self.shape_coord = list(map(lambda x: [x[0]+self.coord[0], x[1]+self.coord[1]], self.shape))
    
    def rotate(self):
        self.idx = self.idx + 1 if self.idx < len(BLOCK_DICT[self.name]['shape_list']) - 1 else 0
        self.shape = BLOCK_DICT[self.name]['shape_list'][self.idx]
        self.shape_coord = list(map(lambda x: [x[0]+self.coord[0], x[1]+self.coord[1]], self.shape))

    def down(self, n=1):
        self.coord = [self.coord[0] + n, self.coord[1]]
        self.shape_coord = list(map(lambda x: [x[0]+self.coord[0], x[1]+self.coord[1]], self.shape))
    
    def left(self, n=1):
        self.coord = [self.coord[0], self.coord[1] - n]
        self.shape_coord = list(map(lambda x: [x[0]+self.coord[0], x[1]+self.coord[1]], self.shape))
    
    def right(self, n=1):
        self.coord = [self.coord[0], self.coord[1] + n]
        self.shape_coord = list(map(lambda x: [x[0]+self.coord[0], x[1]+self.coord[1]], self.shape))

    def get_rotate_coord_list(self):
        new_idx = self.idx + 1 if self.idx < len(BLOCK_DICT[self.name]['shape_list']) - 1 else 0
        new_shape = BLOCK_DICT[self.name]['shape_list'][new_idx]
        return list(map(lambda x: [x[0]+self.coord[0], x[1]+self.coord[1]], new_shape))


class Teris():
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.screen = pygame.display.set_mode((w * SIZE, h * SIZE))
        pygame.display.set_caption("Teris Game")
        self.title_font = pygame.font.Font(None, 36)  # Use default font with size 36
        self.game_clock = pygame.time.Clock()
        self.speed = GAME_SPEED
    
    def run(self):
        self.running = True
        while self.running:
            self.start()
            self.play()
            self.end()
        pygame.quit()
        sys.exit()

    def start(self):
        self.fall_intv = FALL_INTERVAL
        self.score = 0
        self.round = 1
        self.pool = np.zeros((self.h, self.w), dtype=int)
        self.generate_block()
        self.last_move_time = pygame.time.get_ticks()
        self.draw_start()
        while self.running:
            if self.get_continue_flag():
                return

    def end(self):
        self.draw_end()
        while self.running:
            if self.get_continue_flag():
                return

    def play(self):
        while self.running:
            # is game over
            if self.is_block_in_pool():
                return
            # is auto fall
            current_time = pygame.time.get_ticks()
            if current_time - self.last_move_time >= self.fall_intv:
                self.block_move_down()
                self.last_move_time = current_time
            # receive action
            action = self.get_action()
            if action == 'quit': 
                self.running = False
            if action == 'left':
                self.block_move_left()
            elif action == 'right':
                self.block_move_right()
            elif action == 'down':
                self.block_move_down()
            elif action == 'fall':
                self.block_fall()
            elif action == 'rotate':
                self.block_rotate()
            # pool vanish
            self.pool_vanish()

        pygame.quit()
        sys.exit()

    def generate_block(self):
        self.block = Block(self.w // 2)

    def is_move_bump(self, action):
        if action not in ('left', 'right'): return False
        d = -1 if action == 'left' else 1
        for i, j in self.block.shape_coord:
            # bump wall / pool
            new_j = j + d
            if new_j < 0 or new_j >= self.w or self.pool[i, new_j] > 0:
                return True
        return False
    
    def is_rotate_bump(self):
        block_rotate_coord_list = self.block.get_rotate_coord_list()
        for i, j in block_rotate_coord_list:
            if i < 0 or j < 0 or i >= self.h or j >= self.w or self.pool[i, j] > 0:
                return True
        return False
    
    def block_move_left(self):
        if not self.is_move_bump('left'): 
            self.block.left()
            self.update()
            
    def block_move_right(self):
        if not self.is_move_bump('right'): 
            self.block.right()
            self.update()
    
    def block_rotate(self):
        if not self.is_rotate_bump():
            self.block.rotate()
            self.update()

    def block_move_down(self):
        if self.is_block_meet_pool():
            self.block_to_pool()
        else:
            self.block.down()
            self.update()

    def block_fall(self):
        if self.is_block_meet_pool():
            self.block_to_pool()
        else:
            while not self.is_block_meet_pool():
                self.block.down()
            self.block_to_pool()
            self.update()

    def is_block_in_pool(self):
        for i, j in self.block.shape_coord:
            if self.pool[i, j] > 0:
                return True
        return False
    
    def is_block_meet_pool(self):
        for i, j in self.block.shape_coord:
            if i == self.h - 1 or [i+1, j] not in self.block.shape_coord and self.pool[i+1, j] > 0:
                return True
        return False
    
    def block_to_pool(self):
        for i, j in self.block.shape_coord:
            self.pool[i, j] = COLOR_DICT[self.block.color]
        self.generate_block()
        self.update()
    
    def pool_vanish(self):
        vanish_list = []
        for i in range(self.h):
            non_zero_count = np.count_nonzero(self.pool[i])
            if non_zero_count == self.w:
                vanish_list.append(i)
        if not vanish_list: return
        self.score += len(vanish_list)
        if self.score % ROUND_PASS_SCORE == 0:
            self.round += 1
            self.fall_intv *= SPEED_UP_RATE
        self.pool = self.pool[np.array([True if i not in vanish_list else False for i in range(self.h)])]
        self.pool = np.vstack((np.zeros((len(vanish_list), self.w), dtype=int), self.pool))
        self.update()

    def get_action(self):
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = 'quit'
                elif event.key == pygame.K_LEFT:
                    action = 'left'
                elif event.key == pygame.K_RIGHT:
                    action = 'right'
                elif event.key == pygame.K_DOWN:
                    action = 'down'
                elif event.key == pygame.K_UP:
                    action = 'rotate'
                elif event.key == pygame.K_SPACE:
                    action = 'fall'
        return action
    
    def get_continue_flag(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                else:
                    return True
    
    def update(self):
        # draw updated state
        self.screen.fill(COLORS['black'])  # Fill the screen with black
        for i, j in self.block.shape_coord:
            pygame.draw.rect(self.screen, COLORS[self.block.color], (j * SIZE, i * SIZE, SIZE, SIZE))
        for index, element in np.ndenumerate(self.pool):
            if element == 0: continue
            color = COLORS[list(COLOR_DICT.keys())[element-1]]
            pygame.draw.rect(self.screen, color, (index[1] * SIZE, index[0] * SIZE, SIZE, SIZE))
        pygame.display.flip()
        self.game_clock.tick(self.speed)

    def draw_start(self):
        self.screen.fill(COLORS['black'])
        text = self.title_font.render("Teris Start", True, COLORS['white'])  # Render text with white color
        text_rect = text.get_rect(center=(self.w // 2 * SIZE, self.h // 2 * SIZE))  # Center the text
        self.screen.blit(text, text_rect)
        pygame.display.flip()

    def draw_end(self):
        self.screen.fill(COLORS['black'])
        text = self.title_font.render("Your Score: {}".format(self.score), True, COLORS['white'])  # Render text with white color
        text_rect = text.get_rect(center=(self.w // 2 * SIZE, self.h // 2 * SIZE))  # Center the text
        self.screen.blit(text, text_rect)
        pygame.display.flip()

if __name__ == '__main__':
    game = Teris(WIDTH, HEIGHT)
    game.run()