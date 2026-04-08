"""
gunSystem.py - Weapon rendering, shooting mechanics, bullet visuals,
               and muzzle flash effects for all three weapons.
"""

import pygame
import math
import random
from config import (
    WIDTH, HEIGHT, HALF_WIDTH, HALF_HEIGHT, FOV,
    MAX_BULLETS, RELOAD_TIME, MAX_SHOTGUN_AMMO,
    SNIPER_FIRE_COOLDOWN, SNIPER_EQUIP_TIME, SNIPER_SCOPE_ZOOM,
    RED, YELLOW, ORANGE,
    load_image, resource_path
)
from mechanics import audioSystem
from mechanics import animationSystem
from mechanics import enemySystem

# Module-level assets (set during init)
_gun_img = None
_shotgun_img = None
_sniper_img = None


def init():
    """Load weapon images. Call after pygame.init()."""
    global _gun_img, _shotgun_img, _sniper_img
    _gun_img = load_image(resource_path("assets/images/gun.png"), scale=(320, 320))
    _shotgun_img = load_image(resource_path("assets/images/shotgun.png"), scale=(320, 320))
    _sniper_img = load_image(resource_path("assets/images/sniper.png"), scale=(340, 340))


# =============================================================================
# RELOAD / SWAP UPDATES
# =============================================================================

def update_reload(game_state):
    """Check if reload has completed and refill ammo."""
    if game_state.is_reloading:
        now = pygame.time.get_ticks()
        if now - game_state.reload_start_time >= RELOAD_TIME:
            game_state.is_reloading = False
            game_state.bullets_left = MAX_BULLETS


def update_weapon_swap(game_state):
    """Advance weapon swap animation and finalize swap when done."""
    if game_state.is_swapping:
        swap_elapsed = pygame.time.get_ticks() - game_state.swap_start_time
        equip_time = 1000
        if game_state.swap_to == 'sniper':
            equip_time = SNIPER_EQUIP_TIME
        if swap_elapsed > equip_time:
            game_state.is_swapping = False
            game_state.current_weapon = game_state.swap_to
            if game_state.current_weapon == 'primary':
                game_state.bullets_left = MAX_BULLETS
            game_state.swap_to = 'primary'
            if game_state.current_weapon == 'sniper' and game_state.scope_start_time > 0:
                game_state.is_scoping = True


# =============================================================================
# SHOOT
# =============================================================================

def shoot(game_state):
    """Fire the currently equipped weapon."""
    now = pygame.time.get_ticks()
    if game_state.is_swapping or game_state.player_pos is None:
        return
    if game_state.is_healing:
        return

    if game_state.current_weapon == 'primary':
        _shoot_primary(game_state, now)
    elif game_state.current_weapon == 'shotgun':
        _shoot_shotgun(game_state, now)
    elif game_state.current_weapon == 'sniper':
        _shoot_sniper(game_state, now)


def _shoot_primary(game_state, now):
    if game_state.is_reloading:
        return
    if game_state.bullets_left <= 0:
        game_state.is_reloading = True
        game_state.reload_start_time = now
        return
    
    # Stop sprinting when shooting
    game_state.is_sprinting = False
    game_state.last_sprint_time = now
    
    game_state.muzzle_flash_timer = now
    audioSystem.gunshot_sound.play()
    game_state.bullets_left -= 1
    gun_margin = 32
    start_pos = (WIDTH - gun_margin, HEIGHT - gun_margin)
    end_pos = (HALF_WIDTH, HALF_HEIGHT)
    game_state.bullet_lines.append((start_pos, end_pos, now))
    for enemy in game_state.enemies[:]:
        if not enemy['detected']:
            continue
        dx = enemy['pos'][0] - game_state.player_pos[0]
        dy = enemy['pos'][1] - game_state.player_pos[1]
        enemy_angle = math.atan2(dy, dx)
        angle_diff = enemy_angle - game_state.player_angle
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        if -0.06 < angle_diff < 0.06:
            damage = 25
            enemy['hp'] -= damage
            game_state.damage_numbers.append(
                animationSystem.create_damage_number(damage, enemy['pos'], RED))
            game_state.enemy_hit_flashes.append(
                animationSystem.create_enemy_hit_flash(enemy['pos']))
            if enemy['hp'] <= 0:
                audioSystem.enemy_dead_sound.play()
                game_state.enemy_death_animations.append(
                    animationSystem.create_enemy_death_animation(enemy['pos']))
                animationSystem.create_particle_effect(game_state, enemy['pos'], RED, 12)
                game_state.dropped_items.append(enemySystem.enemy_drop_item(enemy['pos']))
                game_state.enemies.remove(enemy)
            break


def _shoot_shotgun(game_state, now):
    if now - game_state.last_shotgun_shot_time < 800:
        return
    if game_state.shotgun_bullets <= 0:
        return
    
    # Stop sprinting when shooting
    game_state.is_sprinting = False
    game_state.last_sprint_time = now
    
    game_state.last_shotgun_shot_time = now
    game_state.muzzle_flash_timer = now
    audioSystem.shotgunshot_sound.play()
    game_state.shotgun_bullets -= 1
    game_state.shotgun_recoil_timer = now
    gun_margin = 32
    start_pos = (WIDTH + 40 - gun_margin, HEIGHT - gun_margin + 120)
    end_pos = (HALF_WIDTH, HALF_HEIGHT)
    game_state.bullet_lines.append((start_pos, end_pos, now))
    for enemy in game_state.enemies[:]:
        if not enemy['detected']:
            continue
        dx = enemy['pos'][0] - game_state.player_pos[0]
        dy = enemy['pos'][1] - game_state.player_pos[1]
        enemy_dist = math.hypot(dx, dy)
        enemy_angle = math.atan2(dy, dx)
        angle_diff = enemy_angle - game_state.player_angle
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        if -0.09 < angle_diff < 0.09:
            damage = 100 if enemy_dist < 150 else 50
            enemy['hp'] -= damage
            game_state.damage_numbers.append(
                animationSystem.create_damage_number(damage, enemy['pos'], ORANGE))
            game_state.enemy_hit_flashes.append(
                animationSystem.create_enemy_hit_flash(enemy['pos']))
            if enemy['hp'] <= 0:
                audioSystem.enemy_dead_sound.play()
                game_state.enemy_death_animations.append(
                    animationSystem.create_enemy_death_animation(enemy['pos']))
                animationSystem.create_particle_effect(game_state, enemy['pos'], ORANGE, 15)
                game_state.dropped_items.append(enemySystem.enemy_drop_item(enemy['pos']))
                game_state.enemies.remove(enemy)
            break


def _shoot_sniper(game_state, now):
    if now - game_state.last_sniper_shot_time < SNIPER_FIRE_COOLDOWN:
        return
    if game_state.sniper_bullets <= 0:
        return
    
    # Stop sprinting when shooting
    game_state.is_sprinting = False
    game_state.last_sprint_time = now
    
    game_state.last_sniper_shot_time = now
    game_state.muzzle_flash_timer = now
    audioSystem.snipershot_sound.play()
    game_state.sniper_bullets -= 1
    game_state.sniper_recoil_timer = now
    gun_margin = 32
    start_pos = (WIDTH - gun_margin, HEIGHT - gun_margin)
    end_pos = (HALF_WIDTH, HALF_HEIGHT)
    game_state.bullet_lines.append((start_pos, end_pos, now))
    hit_enemy = None
    for enemy in game_state.enemies[:]:
        if not enemy['detected']:
            continue
        dx = enemy['pos'][0] - game_state.player_pos[0]
        dy = enemy['pos'][1] - game_state.player_pos[1]
        enemy_dist = math.hypot(dx, dy)
        enemy_angle = math.atan2(dy, dx)
        angle_diff = enemy_angle - game_state.player_angle
        if angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        elif angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        if game_state.is_scoping:
            if -0.04 < angle_diff < 0.04:
                hit_enemy = enemy
                break
        else:
            if enemy_dist < 180 and -0.08 < angle_diff < 0.08 and random.random() < 0.45:
                hit_enemy = enemy
                break
    if hit_enemy:
        damage = 120
        hit_enemy['hp'] -= damage
        game_state.damage_numbers.append(
            animationSystem.create_damage_number(damage, hit_enemy['pos'], (0, 255, 255)))
        game_state.enemy_hit_flashes.append(
            animationSystem.create_enemy_hit_flash(hit_enemy['pos']))
        if hit_enemy['hp'] <= 0:
            audioSystem.enemy_dead_sound.play()
            game_state.enemy_death_animations.append(
                animationSystem.create_enemy_death_animation(hit_enemy['pos']))
            animationSystem.create_particle_effect(game_state, hit_enemy['pos'], (0, 255, 255), 18)
            game_state.dropped_items.append(enemySystem.enemy_drop_item(hit_enemy['pos']))
            game_state.enemies.remove(hit_enemy)


# =============================================================================
# DRAW FUNCTIONS
# =============================================================================

def draw_bullets(surface, game_state):
    """Draw bullet trail lines with fade-out."""
    now = pygame.time.get_ticks()
    for line in game_state.bullet_lines[:]:
        if now - line[2] < 100:
            alpha = 255 - int(255 * (now - line[2]) / 100)
            color = (YELLOW[0], YELLOW[1], YELLOW[2], alpha)
            surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(surf, color, line[0], line[1], 3)
            surface.blit(surf, (0, 0))
        else:
            game_state.bullet_lines.remove(line)


def draw_muzzle_flash(surface, game_state):
    """Draw muzzle flash effect at crosshair."""
    flash_time = pygame.time.get_ticks() - game_state.muzzle_flash_timer
    if flash_time < 100:
        center = (HALF_WIDTH, HALF_HEIGHT)
        if flash_time < 50:
            radius = 25 - int(25 * flash_time / 50)
            pygame.draw.circle(surface, YELLOW, center, radius)
            for _ in range(3):
                ox = random.randint(-10, 10)
                oy = random.randint(-10, 10)
                pygame.draw.circle(surface, ORANGE, (center[0] + ox, center[1] + oy), radius // 2)
        else:
            alpha = 255 - int(255 * (flash_time - 50) / 50)
            surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 200, 0, alpha), (25, 25), 15)
            surface.blit(surf, (center[0] - 25, center[1] - 25))


def draw_gun(surface, game_state):
    """Draw the currently equipped weapon with animations."""
    now = pygame.time.get_ticks()
    y_offset = int(game_state.player_z * 0.5)
    swap_anim = 0

    if game_state.is_swapping:
        swap_elapsed = now - game_state.swap_start_time
        if swap_elapsed < 500:
            swap_anim = int(400 * (swap_elapsed / 500.0))
            show_gun = game_state.current_weapon
        else:
            swap_anim = int(400 * (1 - (swap_elapsed - 500) / 500.0))
            show_gun = game_state.swap_to
    else:
        show_gun = game_state.current_weapon

    if show_gun == 'primary':
        _draw_primary(surface, game_state, now, y_offset, swap_anim)
    elif show_gun == 'shotgun':
        _draw_shotgun(surface, game_state, now, y_offset, swap_anim)
    elif show_gun == 'sniper':
        _draw_sniper(surface, game_state, now, y_offset, swap_anim)


def _draw_primary(surface, game_state, now, y_offset, swap_anim):
    gun_x = WIDTH
    gun_y = HEIGHT - y_offset + swap_anim
    recoil_y = 0
    recoil_duration = 100
    recoil = now - game_state.muzzle_flash_timer < recoil_duration
    if game_state.is_reloading:
        reload_elapsed = now - game_state.reload_start_time
        gun_height = _gun_img.get_height()
        if reload_elapsed < 800:
            gun_y = HEIGHT - y_offset + int(gun_height * (reload_elapsed / 800.0))
        elif reload_elapsed > 2500:
            gun_y = HEIGHT - y_offset + int(gun_height * (1 - (reload_elapsed - 2500) / 500.0))
        else:
            gun_y = HEIGHT - y_offset + gun_height
    elif recoil:
        recoil_y = -18
    gun_rect = _gun_img.get_rect(bottomright=(gun_x, gun_y + recoil_y))
    surface.blit(_gun_img, gun_rect.topleft)


def _draw_shotgun(surface, game_state, now, y_offset, swap_anim):
    gun_x = WIDTH + 100
    gun_y = HEIGHT - y_offset + swap_anim + 100
    base_angle = 20
    recoil_angle = 0
    recoil_y = 0
    recoil_duration = 120
    recoil_timer = game_state.shotgun_recoil_timer
    if recoil_timer and now - recoil_timer < recoil_duration:
        progress = (now - recoil_timer) / recoil_duration
        recoil_y = int(40 * (1 - progress))
        recoil_angle = 18 * (1 - progress)
    total_angle = base_angle - recoil_angle
    rotated = pygame.transform.rotate(_shotgun_img, total_angle)
    rotated_rect = rotated.get_rect(bottomright=(gun_x, gun_y + recoil_y))
    surface.blit(rotated, rotated_rect.topleft)
    if recoil_timer and now - recoil_timer >= recoil_duration:
        game_state.shotgun_recoil_timer = 0


def _draw_sniper(surface, game_state, now, y_offset, swap_anim):
    if game_state.is_scoping:
        return
    swap_anim_local = 0
    prev_gun_down = 800
    sniper_hidden = 700
    sniper_up = 500
    if game_state.is_swapping and game_state.swap_to == 'sniper':
        swap_elapsed = now - game_state.swap_start_time
        if swap_elapsed < prev_gun_down:
            return
        elif swap_elapsed < prev_gun_down + sniper_hidden:
            return
        elif swap_elapsed < prev_gun_down + sniper_hidden + sniper_up:
            progress = min(1.0, (swap_elapsed - prev_gun_down - sniper_hidden) / sniper_up)
            swap_anim_local = int((1.0 - progress) * 400)
    gun_x = WIDTH
    gun_y = HEIGHT + swap_anim_local + 100
    base_angle = 12
    recoil_angle = 0
    recoil_y = 0
    recoil_duration = 180
    recoil_timer = game_state.sniper_recoil_timer
    if recoil_timer and now - recoil_timer < recoil_duration:
        progress = (now - recoil_timer) / recoil_duration
        recoil_y = int(38 * (1 - progress))
        recoil_angle = 16 * (1 - progress)
    total_angle = base_angle - recoil_angle
    rotated = pygame.transform.rotate(_sniper_img, total_angle)
    rotated_rect = rotated.get_rect(bottomright=(gun_x, gun_y + recoil_y))
    surface.blit(rotated, rotated_rect.topleft)
    if recoil_timer and now - recoil_timer >= recoil_duration:
        game_state.sniper_recoil_timer = 0
