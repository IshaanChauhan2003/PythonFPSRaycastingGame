"""
enemySystem.py - Enemy AI, pathfinding behavior, rendering, and loot drops.
"""

import pygame
import math
import random
from config import (
    TILE, FOV, MAX_DEPTH, PROJ_COEFF, RED, GREEN, YELLOW,
    HALF_WIDTH, HALF_HEIGHT, WIDTH,
    ENEMY_IDLE, ENEMY_PATROL, ENEMY_CHASE, ENEMY_ATTACK, ENEMY_SEARCH,
    ENEMY_FOV, ENEMY_SPEED, ENEMY_PATROL_TIME,
    ENEMY_SHOOT_COOLDOWN, ENEMY_LOCK_ON_DELAY,
    load_image, resource_path
)
from mechanics import mapSystem
from mechanics import animationSystem
from mechanics import audioSystem

# Module-level assets (set during init)
_enemy_img = None


def init():
    """Load enemy assets. Call after pygame.init()."""
    global _enemy_img
    _enemy_img = load_image(resource_path("assets/images/enemy.png"))


# =============================================================================
# VISION / MOVEMENT HELPERS
# =============================================================================

def enemy_can_see_player(enemy, game_state):
    """Check if an enemy has line-of-sight to the player within its FOV."""
    ex, ey = enemy['pos']
    if game_state.player_pos is None:
        return False
    px, py = game_state.player_pos
    dx, dy = px - ex, py - ey
    dist = math.hypot(dx, dy)
    angle_to_player = math.atan2(dy, dx)
    rel_angle = angle_to_player - enemy.get('angle', 0)
    if rel_angle > math.pi:
        rel_angle -= 2 * math.pi
    elif rel_angle < -math.pi:
        rel_angle += 2 * math.pi
    if abs(rel_angle) > ENEMY_FOV / 2:
        return False
    # Line-of-sight ray
    steps = int(dist)
    for step in range(1, steps, 5):
        x = ex + dx * step / steps
        y = ey + dy * step / steps
        i, j = int(x / TILE), int(y / TILE)
        if (0 <= i < mapSystem.MAP_WIDTH and 0 <= j < mapSystem.MAP_HEIGHT
                and mapSystem.MAP[j][i] == '#'):
            return False
    return True


def enemy_move_towards(enemy, target, speed=ENEMY_SPEED):
    """Move an enemy toward a target position with wall collision."""
    ex, ey = enemy['pos']
    tx, ty = target
    dx, dy = tx - ex, ty - ey
    dist = math.hypot(dx, dy)
    if dist < 2:
        return
    dx, dy = dx / dist, dy / dist
    new_x = ex + dx * speed
    new_y = ey + dy * speed
    if mapSystem.check_wall(new_x, ey):
        enemy['pos'][0] = new_x
    if mapSystem.check_wall(enemy['pos'][0], new_y):
        enemy['pos'][1] = new_y
    enemy['angle'] = math.atan2(dy, dx)


def enemy_drop_item(enemy_pos):
    """Generate a random drop (ammo or health) at an enemy's position."""
    item_type = random.choice(['ammo', 'health'])
    return {
        'type': item_type,
        'pos': enemy_pos.copy(),
        'hover_offset': 0,
        'hover_direction': 1,
        'hover_speed': 0.5
    }


# =============================================================================
# ENEMY AI (state machine)
# =============================================================================

def enemy_ai(game_state):
    """
    Run one tick of enemy AI for every enemy.
    Returns True if the player has died.
    """
    current_time = pygame.time.get_ticks()
    player_hit = False
    if game_state.player_pos is None:
        return False
    px, py = game_state.player_pos

    for enemy in game_state.enemies:
        # Initialize AI state if missing
        if 'state' not in enemy:
            enemy['state'] = ENEMY_IDLE
            enemy['angle'] = 0
            enemy['patrol_target'] = mapSystem.get_random_patrol_point()
            enemy['last_patrol_time'] = current_time
            enemy['last_seen_player'] = None
            enemy['lock_on_time'] = 0

        ex, ey = enemy['pos']
        sees_player = enemy_can_see_player(enemy, game_state)

        # --- State Transitions ---
        if sees_player:
            enemy['last_seen_player'] = [px, py]
            if enemy['state'] != ENEMY_ATTACK:
                enemy['lock_on_time'] = current_time + ENEMY_LOCK_ON_DELAY
            enemy['state'] = ENEMY_ATTACK
        else:
            if enemy['state'] in [ENEMY_ATTACK, ENEMY_CHASE]:
                enemy['state'] = ENEMY_SEARCH if enemy['last_seen_player'] else ENEMY_PATROL
            elif enemy['state'] == ENEMY_IDLE and random.random() < 0.01:
                enemy['state'] = ENEMY_PATROL

        # --- State Behaviors ---
        if enemy['state'] == ENEMY_ATTACK:
            enemy['angle'] = math.atan2(py - ey, px - ex)
            if current_time >= enemy.get('lock_on_time', 0):
                if current_time - enemy.get('last_shot', 0) > ENEMY_SHOOT_COOLDOWN:
                    if random.random() < 0.95:
                        damage = 20
                        game_state.player_hp -= damage
                        game_state.blood_screen_timer = pygame.time.get_ticks()
                        player_hit = True
                        game_state.bullet_lines.append(((ex, ey), (px, py), current_time))
                        audioSystem.player_hit_sound.play()
                        game_state.shake_timer = pygame.time.get_ticks()
                        animationSystem.trigger_screen_flash(game_state, (255, 0, 0))
                        if game_state.player_pos:
                            game_state.damage_numbers.append(
                                animationSystem.create_damage_number(damage, game_state.player_pos, RED))
                    enemy['last_shot'] = current_time

        elif enemy['state'] == ENEMY_CHASE:
            enemy_move_towards(enemy, [px, py])

        elif enemy['state'] == ENEMY_SEARCH:
            if enemy['last_seen_player']:
                enemy_move_towards(enemy, enemy['last_seen_player'])
                dist = math.hypot(enemy['pos'][0] - enemy['last_seen_player'][0],
                                  enemy['pos'][1] - enemy['last_seen_player'][1])
                if dist < 10:
                    enemy['state'] = ENEMY_PATROL
                    enemy['patrol_target'] = mapSystem.get_random_patrol_point()
                    enemy['last_patrol_time'] = current_time
                    enemy['last_seen_player'] = None

        elif enemy['state'] == ENEMY_PATROL:
            enemy_move_towards(enemy, enemy['patrol_target'])
            dist = math.hypot(enemy['pos'][0] - enemy['patrol_target'][0],
                              enemy['pos'][1] - enemy['patrol_target'][1])
            if dist < 10 or current_time - enemy.get('last_patrol_time', 0) > ENEMY_PATROL_TIME:
                enemy['patrol_target'] = mapSystem.get_random_patrol_point()
                enemy['last_patrol_time'] = current_time
            if random.random() < 0.005:
                enemy['state'] = ENEMY_IDLE

        elif enemy['state'] == ENEMY_IDLE:
            if random.random() < 0.01:
                enemy['angle'] = random.uniform(-math.pi, math.pi)

    if player_hit:
        audioSystem.player_hit_sound.play()
    return game_state.player_hp <= 0


# =============================================================================
# DRAW
# =============================================================================

def draw_enemies(surface, game_state):
    """Render all visible enemies with HP bars."""
    if game_state.player_pos is None:
        return
    for enemy in game_state.enemies:
        ex, ey = enemy['pos']
        dx = ex - game_state.player_pos[0]
        dy = ey - game_state.player_pos[1]
        dist = math.hypot(dx, dy)
        angle_to_enemy = math.atan2(dy, dx)
        rel_angle = angle_to_enemy - game_state.player_angle
        if rel_angle > math.pi:
            rel_angle -= 2 * math.pi
        elif rel_angle < -math.pi:
            rel_angle += 2 * math.pi
        if -FOV / 2 < rel_angle < FOV / 2 and dist < MAX_DEPTH:
            # Line-of-sight check
            has_los = True
            steps = int(dist)
            for step in range(1, steps, 5):
                x = game_state.player_pos[0] + dx * step / steps
                y = game_state.player_pos[1] + dy * step / steps
                i, j = int(x / TILE), int(y / TILE)
                if (0 <= i < mapSystem.MAP_WIDTH and 0 <= j < mapSystem.MAP_HEIGHT
                        and mapSystem.MAP[j][i] == '#'):
                    has_los = False
                    break
            if has_los:
                enemy['detected'] = True
                proj_height = min(8000, PROJ_COEFF / (dist * math.cos(rel_angle)))
                size = (int(proj_height), int(proj_height))
                screen_x = int((rel_angle + FOV / 2) / FOV * WIDTH) - size[0] // 2
                screen_y = HALF_HEIGHT - size[1] // 2
                scaled = pygame.transform.scale(_enemy_img, size)
                surface.blit(scaled, (screen_x, screen_y))
                # HP bar
                bar_width = size[0]
                hp_width = int(bar_width * (enemy['hp'] / 100))
                pygame.draw.rect(surface, RED, (screen_x, screen_y - 10, bar_width, 5))
                pygame.draw.rect(surface, GREEN, (screen_x, screen_y - 10, hp_width, 5))
            else:
                enemy['detected'] = False
        else:
            enemy['detected'] = False
