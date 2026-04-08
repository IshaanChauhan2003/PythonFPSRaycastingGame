"""
pickupSystem.py - Item pickups, health kits, healing, and dropped item rendering.
"""

import pygame
import math
from config import (
    FOV, MAX_DEPTH, HALF_WIDTH, HALF_HEIGHT, WIDTH, TILE,
    PICKUP_RANGE, HEAL_TIME, MAX_HEALTH_KITS, MAX_SHOTGUN_AMMO, HEAL_AMOUNT,
    GREEN, ORANGE, YELLOW, BLACK,
    load_image, resource_path
)
from mechanics import mapSystem
from mechanics import audioSystem
from mechanics import animationSystem

# Module-level assets (set during init)
_ammo_img = None
_hpkit_img = None
_font_small = None


def init():
    """Load pickup images and font. Call after pygame.init()."""
    global _ammo_img, _hpkit_img, _font_small
    _ammo_img = load_image(resource_path("assets/images/ammo.png"), scale=(20, 20))
    _hpkit_img = load_image(resource_path("assets/images/hpKit.png"), scale=(20, 20))
    _font_small = pygame.font.SysFont("Arial", 16)


# =============================================================================
# UPDATE
# =============================================================================

def update_dropped_items(game_state):
    """Update hover animation for all dropped items."""
    for item in game_state.dropped_items:
        item['hover_offset'] += item['hover_speed'] * item['hover_direction']
        if item['hover_offset'] > 10 or item['hover_offset'] < -10:
            item['hover_direction'] *= -1


def update_healing(game_state):
    """Progress the healing timer and apply healing when done."""
    if game_state.is_healing:
        now = pygame.time.get_ticks()
        if now - game_state.heal_start_time >= HEAL_TIME:
            game_state.player_hp = min(100, game_state.player_hp + HEAL_AMOUNT)
            game_state.health_kits -= 1
            game_state.is_healing = False
            audioSystem.heal_sound.play()
            animationSystem.trigger_screen_flash(game_state, (0, 255, 0))
            if game_state.player_pos:
                animationSystem.create_particle_effect(game_state, game_state.player_pos, GREEN, 10)


# =============================================================================
# ACTIONS
# =============================================================================

def pickup_item(game_state):
    """Try to pick up items near the player."""
    if game_state.player_pos is None:
        return
    for item in game_state.dropped_items[:]:
        dx = item['pos'][0] - game_state.player_pos[0]
        dy = item['pos'][1] - game_state.player_pos[1]
        dist = math.hypot(dx, dy)
        if dist < PICKUP_RANGE:
            if item['type'] == 'ammo':
                if game_state.shotgun_bullets < MAX_SHOTGUN_AMMO:
                    game_state.shotgun_bullets = min(MAX_SHOTGUN_AMMO, game_state.shotgun_bullets + 2)
                    game_state.dropped_items.remove(item)
                    audioSystem.pickup_sound.play()
                    animationSystem.trigger_screen_flash(game_state, (0, 255, 0))
                    animationSystem.create_particle_effect(game_state, item['pos'], GREEN, 6)
            elif item['type'] == 'health':
                if game_state.health_kits < MAX_HEALTH_KITS:
                    game_state.health_kits += 1
                    game_state.dropped_items.remove(item)
                    audioSystem.pickup_sound.play()
                    animationSystem.trigger_screen_flash(game_state, (0, 255, 0))
                    animationSystem.create_particle_effect(game_state, item['pos'], GREEN, 6)


def start_healing(game_state):
    """Begin the healing process if the player has health kits."""
    if game_state.health_kits > 0 and not game_state.is_healing and game_state.player_hp < 100:
        game_state.is_healing = True
        game_state.heal_start_time = pygame.time.get_ticks()
    elif game_state.player_hp >= 100:
        pass  # Health already full
    elif game_state.health_kits <= 0:
        pass  # No health kits


# =============================================================================
# LINE OF SIGHT / DRAW
# =============================================================================

def _can_see_item(item_pos, game_state):
    """Check if the player has line-of-sight to an item."""
    if game_state.player_pos is None:
        return False
    dx = item_pos[0] - game_state.player_pos[0]
    dy = item_pos[1] - game_state.player_pos[1]
    dist = math.hypot(dx, dy)
    steps = int(dist)
    for step in range(1, steps, 5):
        x = game_state.player_pos[0] + dx * step / steps
        y = game_state.player_pos[1] + dy * step / steps
        i, j = int(x / TILE), int(y / TILE)
        if (0 <= i < mapSystem.MAP_WIDTH and 0 <= j < mapSystem.MAP_HEIGHT
                and mapSystem.MAP[j][i] == '#'):
            return False
    return True


def draw_dropped_items(surface, game_state):
    """Render dropped items with hover animation, distance scaling, and outlines."""
    for item in game_state.dropped_items:
        if game_state.player_pos is None:
            continue
        if not _can_see_item(item['pos'], game_state):
            continue
        dx = item['pos'][0] - game_state.player_pos[0]
        dy = item['pos'][1] - game_state.player_pos[1]
        dist = math.hypot(dx, dy)
        angle = math.atan2(dy, dx) - game_state.player_angle
        if angle > math.pi:
            angle -= 2 * math.pi
        elif angle < -math.pi:
            angle += 2 * math.pi
        if -FOV / 2 < angle < FOV / 2 and dist < MAX_DEPTH:
            min_size, max_size = 28, 64
            size_val = int(max(min_size, min(max_size, max_size - dist * 0.04)))
            size = (size_val, size_val)
            screen_x = int((angle + FOV / 2) / FOV * WIDTH) - size[0] // 2
            screen_y = HALF_HEIGHT - size[1] // 2 + int(item['hover_offset'])
            # Outline
            outline_surf = pygame.Surface((size[0] + 6, size[1] + 6), pygame.SRCALPHA)
            icon = _ammo_img if item['type'] == 'ammo' else _hpkit_img
            icon = pygame.transform.scale(icon, size)
            pygame.draw.ellipse(outline_surf, (255, 255, 255, 180), (0, 0, size[0] + 6, size[1] + 6))
            outline_surf.blit(icon, (3, 3))
            surface.blit(outline_surf, (screen_x - 3, screen_y - 3))
            # Distance indicator
            dist_text = _font_small.render(f"{int(dist)} px", True, YELLOW)
            text_rect = dist_text.get_rect(center=(screen_x + size[0] // 2, screen_y - 12))
            shadow = _font_small.render(f"{int(dist)} px", True, BLACK)
            surface.blit(shadow, (text_rect.x + 2, text_rect.y + 2))
            surface.blit(dist_text, text_rect)
