"""
playerSystem.py - Player movement, mouse look, jumping, sprinting, and stamina management.
"""

import pygame
import math
from config import (
    PLAYER_SPEED, PLAYER_SPRINT_MULTIPLIER, PLAYER_EXHAUSTED_MULTIPLIER,
    PLAYER_JUMP_VEL, PLAYER_GRAVITY,
    LOW_HP_THRESHOLD, LOW_HP_SLOW, JUMP_SLOW, JUMP_SLOW_TIME,
    MAX_STAMINA, STAMINA_RECHARGE_RATE, STAMINA_RECHARGE_DELAY,
    EXHAUSTION_DURATION, EXHAUSTION_RECHARGE_DELAY,
    SPRINT_DRAIN_PRIMARY, SPRINT_DRAIN_SHOTGUN, SPRINT_DRAIN_SNIPER
)
from mechanics import mapSystem
from mechanics import audioSystem
from mechanics import animationSystem


def handle_mouse_look(game_state):
    """Update player angle based on mouse movement."""
    mouse_dx, _ = pygame.mouse.get_rel()
    game_state.player_angle = float(game_state.player_angle) + mouse_dx * 0.003


def handle_movement(game_state, keys):
    """
    Handle WASD movement, sprinting, stamina, jumping physics, and footstep sounds.
    Returns True if the player is moving.
    """
    if game_state.player_pos is None:
        return False

    sin_a = math.sin(game_state.player_angle)
    cos_a = math.cos(game_state.player_angle)
    new_x = game_state.player_pos[0]
    new_y = game_state.player_pos[1]
    is_moving = False
    current_time = pygame.time.get_ticks()

    # --- Check if player wants to sprint ---
    wants_to_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    
    # --- Update exhaustion state ---
    if game_state.is_exhausted:
        if current_time - game_state.exhaustion_start_time >= EXHAUSTION_DURATION:
            game_state.is_exhausted = False
    
    # --- Determine if player can sprint ---
    can_sprint = (wants_to_sprint and 
                  game_state.stamina > 0 and 
                  not game_state.is_exhausted and
                  not game_state.is_jumping and
                  not game_state.is_healing and
                  not game_state.is_reloading)
    
    game_state.is_sprinting = can_sprint
    
    # --- Update stamina ---
    if game_state.is_sprinting:
        # Drain stamina based on weapon
        drain_rate = SPRINT_DRAIN_PRIMARY
        if game_state.current_weapon == 'shotgun':
            drain_rate = SPRINT_DRAIN_SHOTGUN
        elif game_state.current_weapon == 'sniper':
            drain_rate = SPRINT_DRAIN_SNIPER
        
        game_state.stamina = max(0, game_state.stamina - drain_rate)
        game_state.last_sprint_time = current_time
        
        # Check if stamina depleted
        if game_state.stamina <= 0:
            game_state.is_exhausted = True
            game_state.exhaustion_start_time = current_time
            game_state.is_sprinting = False
    else:
        # Recharge stamina with delay
        if game_state.is_exhausted:
            # Longer delay after exhaustion
            if current_time - game_state.exhaustion_start_time >= EXHAUSTION_RECHARGE_DELAY:
                game_state.stamina = min(MAX_STAMINA, game_state.stamina + STAMINA_RECHARGE_RATE)
        else:
            # Normal recharge delay
            if current_time - game_state.last_sprint_time >= STAMINA_RECHARGE_DELAY:
                game_state.stamina = min(MAX_STAMINA, game_state.stamina + STAMINA_RECHARGE_RATE)

    # --- Speed modifiers ---
    move_speed = PLAYER_SPEED
    
    # Sprint multiplier
    if game_state.is_sprinting:
        move_speed *= PLAYER_SPRINT_MULTIPLIER
    
    # Exhaustion penalty
    if game_state.is_exhausted:
        move_speed *= PLAYER_EXHAUSTED_MULTIPLIER
    
    # Low HP penalty
    if game_state.player_hp < LOW_HP_THRESHOLD:
        move_speed *= LOW_HP_SLOW
        if pygame.time.get_ticks() - game_state.jump_slow_timer < JUMP_SLOW_TIME:
            move_speed *= JUMP_SLOW

    # Weapon-specific speed modifiers (only when not sprinting)
    if not game_state.is_sprinting:
        if game_state.current_weapon == 'shotgun':
            move_speed *= 0.7
        elif game_state.current_weapon == 'sniper':
            move_speed *= 0.55

    if game_state.is_swapping and game_state.swap_to == 'sniper':
        move_speed *= 0.45

    # Jump velocity based on weapon
    if game_state.current_weapon == 'shotgun':
        jump_vel = PLAYER_JUMP_VEL * 0.7
    elif game_state.current_weapon == 'sniper':
        jump_vel = PLAYER_JUMP_VEL * 0.6
    else:
        jump_vel = PLAYER_JUMP_VEL

    # --- Directional movement ---
    if keys[pygame.K_w]:
        new_x += move_speed * cos_a
        new_y += move_speed * sin_a
        is_moving = True
    if keys[pygame.K_s]:
        new_x -= move_speed * cos_a
        new_y -= move_speed * sin_a
        is_moving = True
    if keys[pygame.K_a]:
        new_x += move_speed * sin_a
        new_y -= move_speed * cos_a
        is_moving = True
    if keys[pygame.K_d]:
        new_x -= move_speed * sin_a
        new_y += move_speed * cos_a
        is_moving = True

    # --- Jump physics ---
    if game_state.is_jumping:
        game_state.player_z += game_state.player_vz
        game_state.player_vz -= PLAYER_GRAVITY
        if game_state.player_z <= 0:
            game_state.player_z = 0
            game_state.player_vz = 0
            game_state.is_jumping = False

    # --- Footstep sounds (faster when sprinting) ---
    if is_moving and not game_state.is_jumping:
        if audioSystem.footstep_channel:
            if game_state.is_sprinting:
                # Play footsteps more frequently when sprinting
                if not audioSystem.footstep_channel.get_busy():
                    audioSystem.footstep_sound.play()
            else:
                if not audioSystem.footstep_channel.get_busy():
                    audioSystem.footstep_sound.play()

    # --- Collision detection ---
    if mapSystem.check_wall(new_x, game_state.player_pos[1]):
        game_state.player_pos[0] = int(round(new_x))
    if mapSystem.check_wall(game_state.player_pos[0], new_y):
        game_state.player_pos[1] = int(round(new_y))

    return is_moving


def try_jump(game_state):
    """Attempt to jump. Applies low-HP penalty if applicable."""
    if not game_state.is_jumping and game_state.player_z == 0:
        game_state.is_jumping = True
        jump_vel = PLAYER_JUMP_VEL
        if game_state.current_weapon == 'shotgun':
            jump_vel *= 0.7
        elif game_state.current_weapon == 'sniper':
            jump_vel *= 0.6
        game_state.player_vz = float(jump_vel)
        audioSystem.jump_sound.play()
        animationSystem.trigger_screen_flash(game_state, (100, 100, 255))
        if game_state.player_pos:
            animationSystem.create_particle_effect(game_state, game_state.player_pos, (100, 100, 255), 6)
        if game_state.player_hp < LOW_HP_THRESHOLD:
            game_state.jump_slow_timer = pygame.time.get_ticks()
