import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()
pygame.display.set_caption("2D ZIP MAN")

WIDTH, HEIGHT = 500, 400
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheet(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def load_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return surface

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    CHARACTER_NAME = "MaskDude"
    SPRITES = load_sprite_sheet("MainCharacters", CHARACTER_NAME, 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.score = 0
        self.is_burning = False
        self.burn_time = 0
        self.burn_duration = FPS
        self.lives = 3
        self.dead = False
        self.update_sprite()

    def jump(self):
        if self.jump_count < 2:
            self.y_vel = -self.GRAVITY * 8
            self.animation_count = 0
            self.jump_count += 1
            if self.jump_count == 1:
                self.fall_count = 0

    def move(self, dx, dy, objects):
        self.rect.x += dx
        for obj in objects:
            if pygame.sprite.collide_mask(self, obj):
                if dx > 0:
                    self.rect.right = obj.rect.left
                elif dx < 0:
                    self.rect.left = obj.rect.right

        self.rect.y += dy
        for obj in objects:
            if pygame.sprite.collide_mask(self, obj):
                if dy > 0:
                    self.rect.bottom = obj.rect.top
                    self.landed()
                elif dy < 0:
                    self.rect.top = obj.rect.bottom
                    self.hit_head()

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.y_vel = 0

    def loop(self, fps, objects):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel, objects)
        self.fall_count += 1
        self.update_sprite()

        if self.is_burning:
            self.burn_time += 1
            if self.burn_time >= self.burn_duration:
                self.is_burning = False
                self.lives -= 1
                if self.lives <= 0:
                    self.dead = True
                else:
                    self.rect.x, self.rect.y = 100, 100
                    self.x_vel = 0
                    self.y_vel = 0

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)

        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, window):
        if self.is_burning:
            burn_color = (255, 215, 0) if self.burn_time % 10 < 5 else (255, 0, 0)
            temp_sprite = self.sprite.copy()
            temp_sprite.fill(burn_color, special_flags=pygame.BLEND_MULT)
            window.blit(temp_sprite, (self.rect.x, self.rect.y))
        else:
            window.blit(self.sprite, (self.rect.x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, window):
        window.blit(self.image, (self.rect.x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = load_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Collectible(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        self.image.fill((255, 215, 0))
        self.mask = pygame.mask.from_surface(self.image)

    def collected(self, player):
        return self.rect.colliderect(player.rect)

class Ball(Object):
    def __init__(self, x, y, size, speed):
        super().__init__(x, y, size, size)
        self.image.fill((0, 255, 0))
        self.speed = speed
        self.mask = pygame.mask.from_surface(self.image)
        self.passed = False

    def move(self):
        self.rect.x += self.speed
        if self.rect.x > WIDTH:
            self.rect.x = -self.rect.width
            self.passed = False

def get_background(name=None):
    return [], None

def draw(window, background, bg_image, player, objects, collectibles, balls):
    if bg_image:
        for tile in background:
            window.blit(bg_image, tile)
    else:
        window.fill((30, 30, 30))

    for obj in objects:
        obj.draw(window)
    for collectible in collectibles:
        collectible.draw(window)
    for ball in balls:
        ball.draw(window)

    player.draw(window)

    font = pygame.font.SysFont(None, 30)
    score_text = font.render(f"Score: {player.score}", True, (255, 255, 255))
    window.blit(score_text, (10, 10))

    lives_text = font.render(f"Lives: {player.lives}", True, (255, 255, 255))
    window.blit(lives_text, (WIDTH - 100, 10))

    pygame.display.update()

def handle_collectibles(player, collectibles):
    collected = []
    for collectible in collectibles:
        if collectible.collected(player):
            collected.append(collectible)
            player.score += 1
    for c in collected:
        collectibles.remove(c)

def check_score(player, balls):
    for ball in balls:
        if ball.rect.top > player.rect.bottom and not ball.passed:
            ball.passed = True
            player.score += 1

def handle_move(player, objects, collectibles):
    keys = pygame.key.get_pressed()
    player.x_vel = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.move_right(PLAYER_VEL)

    handle_collectibles(player, collectibles)

def main(window):
    clock = pygame.time.Clock()

    background, bg_image = get_background()

    player = Player(100, 100, 50, 50)
    block_size = 48
    floor = [
        Block(i * block_size, HEIGHT - block_size, block_size)
        for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)
    ]

    objects = floor.copy()

    collectibles = [
        Collectible(200, HEIGHT - 100, 30),
        Collectible(400, HEIGHT - 150, 30)
    ]

    balls = [
        Ball(0, HEIGHT - 80, 30, 5),
    ]

    run = True
    game_over = False
    font_game_over = pygame.font.SysFont(None, 60)

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    player.jump()
                if event.key == pygame.K_r and game_over:
                    player = Player(100, 100, 50, 50)
                    collectibles = [
                        Collectible(200, HEIGHT - 100, 30),
                        Collectible(400, HEIGHT - 150, 30)
                    ]
                    balls = [
                        Ball(0, HEIGHT - 80, 30, 5),
                    ]
                    game_over = False

        if not game_over:
            if not player.dead:
                player.loop(FPS, objects)

                for ball in balls:
                    ball.move()
                    if pygame.sprite.collide_mask(player, ball) and not player.is_burning:
                        player.is_burning = True
                        player.burn_time = 0

                handle_move(player, objects, collectibles)
                check_score(player, balls)
            else:
                game_over = True

            draw(window, background, bg_image, player, objects, collectibles, balls)

        else:
            window.fill((0, 0, 0))
            game_over_text = font_game_over.render("GAME OVER", True, (255, 0, 0))
            retry_text = pygame.font.SysFont(None, 30).render("R'ye basarak yeniden başlayın", True, (255, 255, 255))
            window.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 50))
            window.blit(retry_text, (WIDTH//2 - retry_text.get_width()//2, HEIGHT//2 + 10))
            pygame.display.update()

    pygame.quit()

if __name__ == "__main__":
    main(window)
