"""
animationSystem.py - Particle effects, damage numbers, screen flashes,
                     and all visual animation logic.
"""

import pygame
import math
import random
from config import (
    WIDTH, HEIGHT, HALF_WIDTH, HALF_HEIGHT, FOV, MAX_DEPTH, PROJ_COEFF,
    RED, YELLOW, WHITE,
    DAMAGE_NUMBER_DURATION, PARTICLE_DURATION, PARTICLE_GRAVITY, PARTICLE_FRICTION,
    ENEMY_DEATH_ANIMATION_DURATION, ENEMY_HIT_FLASH_DURATION,
    SCREEN_FLASH_DURATION
)

# Module-level font (set during init)
_font_medium = None
_enemy_img = None  # needed for death animation rendering


def init(enemy_img):
    """Initialize animation system. Call after pygame.init()."""
    global _font_medium, _enemy_img
    _font_medium = pygame.font.SysFont("Arial", 24)
    _enemy_img = enemy_img


# =============================================================================
# CREATION HELPERS
# =============================================================================

def create_damage_number(damage, pos, color=RED):
    """Create a floating damage number dict."""
    return {
        'text': str(damage),
        'pos': pos.copy(),
        'vel': [random.uniform(-2, 2), random.uniform(-3, -1)],
        'timer': pygame.time.get_ticks(),
        'color': color,
        'alpha': 255
    }


def create_particle_effect(game_state, pos, color=YELLOW, count=8):
    """Spawn particle explosion at the given world position."""
    for _ in range(count):
        particle = {
            'pos': pos.copy(),
            'vel': [random.uniform(-5, 5), random.uniform(-5, 5)],
            'timer': pygame.time.get_ticks(),
            'color': color,
            'size': random.randint(2, 6),
            'alpha': 255
        }
        game_state.particles.append(particle)


def create_enemy_death_animation(pos):
    """Create an enemy death animation dict."""
    return {
        'pos': pos.copy(),
        'timer': pygame.time.get_ticks(),
        'scale': 1.0,
        'rotation': 0,
        'alpha': 255
    }


def create_enemy_hit_flash(pos):
    """Create an enemy hit flash dict."""
    return {
        'pos': pos.copy(),
        'timer': pygame.time.get_ticks(),
        'alpha': 255
    }


def trigger_screen_flash(game_state, color=(255, 255, 255)):
    """Trigger a full-screen color flash."""
    game_state.screen_flash_timer = pygame.time.get_ticks()
    game_state.screen_flash_color = color


# =============================================================================
# UPDATE
# =============================================================================

def update_animations(game_state):
    """Advance all animations by one frame."""
    now = pygame.time.get_ticks()

    # Damage numbers
    for number in game_state.damage_numbers[:]:
        elapsed = now - number['timer']
        if elapsed < DAMAGE_NUMBER_DURATION:
            number['pos'][1] += number['vel'][1]
            number['vel'][1] *= 0.98
            progress = elapsed / DAMAGE_NUMBER_DURATION
            number['alpha'] = int(255 * (1 - progress))
        else:
            game_state.damage_numbers.remove(number)

    # Particles
    for particle in game_state.particles[:]:
        elapsed = now - particle['timer']
        if elapsed < PARTICLE_DURATION:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['vel'][1] += PARTICLE_GRAVITY
            particle['vel'][0] *= PARTICLE_FRICTION
            particle['vel'][1] *= PARTICLE_FRICTION
            progress = elapsed / PARTICLE_DURATION
            particle['alpha'] = int(255 * (1 - progress))
        else:
            game_state.particles.remove(particle)

    # Enemy death animations
    for anim in game_state.enemy_death_animations[:]:
        elapsed = now - anim['timer']
        if elapsed < ENEMY_DEATH_ANIMATION_DURATION:
            progress = elapsed / ENEMY_DEATH_ANIMATION_DURATION
            anim['scale'] = 1.0 + progress * 0.5
            anim['rotation'] = progress * 360
            anim['alpha'] = int(255 * (1 - progress))
        else:
            game_state.enemy_death_animations.remove(anim)

    # Enemy hit flashes
    for flash in game_state.enemy_hit_flashes[:]:
        elapsed = now - flash['timer']
        if elapsed < ENEMY_HIT_FLASH_DURATION:
            progress = elapsed / ENEMY_HIT_FLASH_DURATION
            flash['alpha'] = int(255 * (1 - progress))
        else:
            game_state.enemy_hit_flashes.remove(flash)


# =============================================================================
# DRAW
# =============================================================================

def _world_to_screen(pos, game_state):
    """Convert a world position to (screen_x, angle, dist) or None if off-screen."""
    if game_state.player_pos is None:
        return None
    dx = pos[0] - game_state.player_pos[0]
    dy = pos[1] - game_state.player_pos[1]
    dist = math.hypot(dx, dy)
    angle = math.atan2(dy, dx) - game_state.player_angle
    if angle > math.pi:
        angle -= 2 * math.pi
    elif angle < -math.pi:
        angle += 2 * math.pi
    if -FOV / 2 < angle < FOV / 2 and dist < MAX_DEPTH:
        screen_x = int((angle + FOV / 2) / FOV * WIDTH)
        return screen_x, angle, dist
    return None


def draw_animations(surface, game_state):
    """Render all active animation effects."""
    # Damage numbers
    for number in game_state.damage_numbers:
        result = _world_to_screen(number['pos'], game_state)
        if result is None:
            continue
        screen_x, angle, dist = result
        screen_y = HALF_HEIGHT - int(dist * 0.1)
        text_surf = _font_medium.render(number['text'], True, number['color'])
        alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        alpha_surf.fill((255, 255, 255, number['alpha']))
        text_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(text_surf, (screen_x - text_surf.get_width() // 2, screen_y))

    # Particles
    for particle in game_state.particles:
        result = _world_to_screen(particle['pos'], game_state)
        if result is None:
            continue
        screen_x, angle, dist = result
        screen_y = HALF_HEIGHT
        sz = particle['size']
        particle_surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, (*particle['color'], particle['alpha']),
                           (sz, sz), sz)
        surface.blit(particle_surf, (screen_x - sz, screen_y - sz))

    # Enemy death animations
    for anim in game_state.enemy_death_animations:
        result = _world_to_screen(anim['pos'], game_state)
        if result is None:
            continue
        screen_x, angle, dist = result
        proj_height = min(8000, PROJ_COEFF / (dist * math.cos(angle)))
        size = (int(proj_height * anim['scale']), int(proj_height * anim['scale']))
        sx = screen_x - size[0] // 2
        sy = HALF_HEIGHT - size[1] // 2
        scaled = pygame.transform.scale(_enemy_img, size)
        rotated = pygame.transform.rotate(scaled, anim['rotation'])
        alpha_surf = pygame.Surface(rotated.get_size(), pygame.SRCALPHA)
        alpha_surf.fill((255, 255, 255, anim['alpha']))
        rotated.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(rotated, (sx, sy))

    # Enemy hit flashes
    for flash in game_state.enemy_hit_flashes:
        result = _world_to_screen(flash['pos'], game_state)
        if result is None:
            continue
        screen_x, angle, dist = result
        proj_height = min(8000, PROJ_COEFF / (dist * math.cos(angle)))
        size = (int(proj_height), int(proj_height))
        sx = screen_x - size[0] // 2
        sy = HALF_HEIGHT - size[1] // 2
        flash_surf = pygame.Surface(size, pygame.SRCALPHA)
        flash_surf.fill((255, 255, 255, flash['alpha']))
        surface.blit(flash_surf, (sx, sy))


def draw_screen_flash(surface, game_state):
    """Draw screen-wide flash overlay (damage, pickup, etc.)."""
    elapsed = pygame.time.get_ticks() - game_state.screen_flash_timer
    if elapsed < SCREEN_FLASH_DURATION:
        alpha = int(100 * (1 - elapsed / SCREEN_FLASH_DURATION))
        flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash_surf.fill((*game_state.screen_flash_color, alpha))
        surface.blit(flash_surf, (0, 0))
