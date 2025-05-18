import pygame
from os.path import join

def load_sprite_sheet(sheet_name, character_name, width, height, flip=False):
    sheet = pygame.image.load(join("assets", sheet_name + ".png")).convert_alpha()
    sprites = {}
    directions = ["left", "right"]
    actions = ["idle", "run", "jump", "double_jump", "fall"]

    for action in actions:
        for direction in directions:
            key = f"{action}_{direction}"
            sprites[key] = []
            for i in range(sheet.get_width() // width):
                rect = pygame.Rect(i * width, 0, width, height)
                image = sheet.subsurface(rect)
                if direction == "right" and flip:
                    image = pygame.transform.flip(image, True, False)
                sprites[key].append(image)
    return sprites

def load_block(size):
    block = pygame.Surface((size, size))
    block.fill((100, 100, 100))  # Basit gri blok
    return block
