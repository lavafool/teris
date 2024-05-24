import pygame
from settings import *
import random
import numpy as np

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
    
    def turn(self):
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

    def get_turn_coord_list(self):
        new_idx = self.idx + 1 if self.idx < len(BLOCK_DICT[self.name]['shape_list']) - 1 else 0
        new_shape = BLOCK_DICT[self.name]['shape_list'][new_idx]
        return list(map(lambda x: [x[0]+self.coord[0], x[1]+self.coord[1]], new_shape))


class Teris():
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.screen = pygame.display.set_mode((w * SIZE, h * SIZE))
        pygame.display.set_caption("Teris Game")
        self.game_clock = pygame.time.Clock()
        self.reset()
    
    def reset(self):
        self.pool = np.zeros((self.h, self.w), dtype=int)
        self.generate_block()
        self.last_move_time = pygame.time.get_ticks()

    def run(self):
        while True:
            # is game over?
            if self.is_block_in_pool():
                self.reset()
                self.update()
            
            # is fall?
            current_time = pygame.time.get_ticks()
            if current_time - self.last_move_time >= FALL_INTERVAL:
                self.block_move_down()
                self.last_move_time = current_time
            
            # get action
            action = self.get_action()
            if action == 'quit': break
            if action == 'left':
                self.block_move_left()
            elif action == 'right':
                self.block_move_right()
            elif action == 'down':
                self.block_move_down()
            elif action == 'fall':
                self.block_fall()
            elif action == 'turn':
                self.block_turn()

            # pool vanish
            self.pool_vanish()

        pygame.quit()

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
    
    def is_turn_bump(self):
        block_turn_coord_list = self.block.get_turn_coord_list()
        for i, j in block_turn_coord_list:
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
    
    def block_turn(self):
        if not self.is_turn_bump():
            self.block.turn()
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
                    action = 'turn'
                elif event.key == pygame.K_SPACE:
                    action = 'fall'
        return action
    
    def update(self, speed=GAME_SPEED):
        # draw updated state
        self.screen.fill(COLORS['white'])  # Fill the screen with white
        for i, j in self.block.shape_coord:
            pygame.draw.rect(self.screen, COLORS[self.block.color], (j * SIZE, i * SIZE, SIZE, SIZE))
        for index, element in np.ndenumerate(self.pool):
            if element == 0: continue
            color = COLORS[list(COLOR_DICT.keys())[element-1]]
            pygame.draw.rect(self.screen, color, (index[1] * SIZE, index[0] * SIZE, SIZE, SIZE))
        
        pygame.display.flip()
        self.game_clock.tick(speed)
    

if __name__ == '__main__':
    game = Teris(15, 25)
    game.run()