"""
config.py - Central configuration for the RayCasting FPS game.
Contains all constants, colors, and utility functions.
"""

import math
import sys
import os

# =============================================================================
# SCREEN
# =============================================================================
WIDTH, HEIGHT = 800, 600
HALF_WIDTH, HALF_HEIGHT = WIDTH // 2, HEIGHT // 2

# =============================================================================
# COLORS
# =============================================================================
BLACK = (0, 0, 0)
DARKGRAY = (50, 50, 50)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
LIGHTGRAY = (50, 50, 50)

# =============================================================================
# MAP / TILE
# =============================================================================
TILE = 50
ROUND_TIME = 60  # seconds per round

# =============================================================================
# RAYCASTING
# =============================================================================
FOV = math.pi / 3
NUM_RAYS = 100
MAX_DEPTH = 800
DELTA_ANGLE = FOV / NUM_RAYS
DIST = NUM_RAYS / (2 * math.tan(FOV / 2))
PROJ_COEFF = 3 * DIST * TILE
SCALE = WIDTH // NUM_RAYS

# =============================================================================
# PLAYER
# =============================================================================
PLAYER_SPEED = 1.8
PLAYER_SPRINT_MULTIPLIER = 1.2  # Reduced from 1.8 to 1.4 for more balanced sprint speed
PLAYER_EXHAUSTED_MULTIPLIER = 0.6
PLAYER_JUMP_VEL = 25.0
PLAYER_GRAVITY = 0.7

# =============================================================================
# STAMINA SYSTEM
# =============================================================================
MAX_STAMINA = 100
STAMINA_RECHARGE_RATE = 0.2  # per frame when not sprinting
STAMINA_RECHARGE_DELAY = 1000  # ms delay before recharge starts
EXHAUSTION_DURATION = 5000  # 5 seconds of slow movement
EXHAUSTION_RECHARGE_DELAY = 3000  # 3 seconds before stamina recharge after exhaustion

# Weapon-specific sprint drain rates (stamina per frame at 60fps)
# Formula: 100 stamina / (desired_seconds * 60 fps)
SPRINT_DRAIN_PRIMARY = 0.167  # 10 seconds (100 / 600 frames)
SPRINT_DRAIN_SHOTGUN = 0.208  # 8 seconds (100 / 480 frames)
SPRINT_DRAIN_SNIPER = 0.278  # 6 seconds (100 / 360 frames)

# =============================================================================
# ENEMY
# =============================================================================
ENEMY_SHOOT_COOLDOWN = 900
ENEMY_LOCK_ON_DELAY = 400
ENEMY_DETECTION_RANGE = TILE * 8
ENEMY_SHOOT_RANGE = TILE * 5

ENEMY_IDLE = 'idle'
ENEMY_PATROL = 'patrol'
ENEMY_CHASE = 'chase'
ENEMY_ATTACK = 'attack'
ENEMY_SEARCH = 'search'
ENEMY_FOV = math.pi / 2
ENEMY_SPEED = 1.2
ENEMY_PATROL_TIME = 2000

# =============================================================================
# WEAPONS
# =============================================================================
MAX_BULLETS = 9
RELOAD_TIME = 3000

MAX_SHOTGUN_AMMO = 4

SNIPER_BULLETS = 5
SNIPER_EQUIP_TIME = 3000
SNIPER_FIRE_COOLDOWN = 1400
SNIPER_SCOPE_ZOOM = 2.2
SNIPER_SCOPE_TRANSITION = 200

# =============================================================================
# PICKUPS
# =============================================================================
PICKUP_RANGE = 80
HEAL_TIME = 1500
MAX_HEALTH_KITS = 2
HEAL_AMOUNT = 25

# =============================================================================
# ANIMATION / VFX
# =============================================================================
SCREEN_FLASH_DURATION = 200
DAMAGE_NUMBER_DURATION = 1000
PARTICLE_DURATION = 1500
ENEMY_DEATH_ANIMATION_DURATION = 800
ENEMY_HIT_FLASH_DURATION = 150
ENEMY_SPAWN_ANIMATION_DURATION = 1000

MAX_PARTICLES = 50
PARTICLE_GRAVITY = 0.3
PARTICLE_FRICTION = 0.98

UI_FADE_DURATION = 300
BUTTON_HOVER_ANIMATION_DURATION = 200

# =============================================================================
# SCREEN SHAKE / LOW HP
# =============================================================================
SHAKE_DURATION = 300
SHAKE_INTENSITY = 8
LOW_HP_THRESHOLD = 40
LOW_HP_SLOW = 0.5
JUMP_SLOW = 0.4
JUMP_SLOW_TIME = 2000


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def resource_path(relative_path):
    """Get absolute path to resource. Works for dev and PyInstaller builds."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def load_image(name, scale=None):
    """Load a pygame image with optional scaling. Returns placeholder on failure."""
    import pygame
    try:
        img = pygame.image.load(name).convert_alpha()
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    except Exception:
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.rect(surf, RED, (0, 0, 50, 50), 2)
        pygame.draw.line(surf, RED, (0, 0), (50, 50), 2)
        pygame.draw.line(surf, RED, (50, 0), (0, 50), 2)
        return surf
