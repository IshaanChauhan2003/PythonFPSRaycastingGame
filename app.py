"""
app.py - Main entry point for the RayCasting FPS game.
Initializes pygame, loads all systems, and runs the game loop.
"""

import pygame
import sys
import random
import math

# Initialize pygame BEFORE any module that loads assets
pygame.init()
pygame.mixer.init()

# Screen setup
from config import (
    WIDTH, HEIGHT, HALF_WIDTH, HALF_HEIGHT,
    BLACK, DARKGRAY, LIGHTGRAY, RED, GREEN, YELLOW, ORANGE,
    PLAYER_JUMP_VEL, LOW_HP_THRESHOLD,
    SHAKE_DURATION, SHAKE_INTENSITY,
    MAX_BULLETS, SNIPER_EQUIP_TIME, SNIPER_SCOPE_ZOOM,
    load_image, resource_path
)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Raycasting FPS - Enhanced")

# --- Initialize all game systems ---
from mechanics import audioSystem
from mechanics import animationSystem
from mechanics import enemySystem
from mechanics import gunSystem
from mechanics import playerSystem
from mechanics import pickupSystem
from mechanics import renderSystem
from mechanics import mapSystem
from mechanics.gameState import GameState

# Load assets for each system
audioSystem.init()
enemySystem.init()
gunSystem.init()
pickupSystem.init()
renderSystem.init()

# Initialize animation system with enemy image (needed for death animations)
animationSystem.init(enemySystem._enemy_img)

# Hide mouse cursor for FPS controls
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)


# =============================================================================
# GAME LOOP
# =============================================================================

def game_loop():
    """Main game loop handling input, updates, and rendering."""
    clock = pygame.time.Clock()
    game_state = GameState()

    while True:
        # --- Audio ---
        audioSystem.manage_ambient_sound()

        # --- Reload check ---
        gunSystem.update_reload(game_state)

        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not game_state.is_swapping:
                    gunSystem.shoot(game_state)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if game_state.current_weapon == 'sniper':
                    game_state.is_scoping = True
                    game_state.scope_start_time = pygame.time.get_ticks()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                game_state.is_scoping = False
                game_state.scope_start_time = pygame.time.get_ticks()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_SPACE:
                    playerSystem.try_jump(game_state)
                elif event.key == pygame.K_r:
                    if not game_state.is_reloading and game_state.bullets_left < MAX_BULLETS:
                        game_state.is_reloading = True
                        game_state.reload_start_time = pygame.time.get_ticks()
                elif event.key == pygame.K_1:
                    if game_state.current_weapon != 'primary' and not game_state.is_swapping:
                        game_state.is_swapping = True
                        game_state.swap_start_time = pygame.time.get_ticks()
                        game_state.swap_to = 'primary'
                        animationSystem.trigger_screen_flash(game_state, (255, 255, 0))
                        if game_state.player_pos:
                            animationSystem.create_particle_effect(game_state, game_state.player_pos, YELLOW, 8)
                elif event.key == pygame.K_2:
                    if game_state.current_weapon != 'shotgun' and not game_state.is_swapping:
                        game_state.is_swapping = True
                        game_state.swap_start_time = pygame.time.get_ticks()
                        game_state.swap_to = 'shotgun'
                        animationSystem.trigger_screen_flash(game_state, (255, 165, 0))
                        if game_state.player_pos:
                            animationSystem.create_particle_effect(game_state, game_state.player_pos, ORANGE, 8)
                elif event.key == pygame.K_3:
                    if game_state.current_weapon != 'sniper' and not game_state.is_swapping:
                        game_state.is_swapping = True
                        game_state.swap_start_time = pygame.time.get_ticks()
                        game_state.swap_to = 'sniper'
                        animationSystem.trigger_screen_flash(game_state, (100, 200, 255))
                        if game_state.player_pos:
                            animationSystem.create_particle_effect(game_state, game_state.player_pos, (100, 200, 255), 8)
                elif event.key == pygame.K_e:
                    pickupSystem.pickup_item(game_state)
                elif event.key == pygame.K_q:
                    pickupSystem.start_healing(game_state)
                elif event.key == pygame.K_x:
                    if game_state.current_weapon == 'sniper':
                        game_state.is_scoping = True

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_x:
                    if game_state.current_weapon == 'sniper':
                        game_state.is_scoping = False

        # --- Player updates ---
        playerSystem.handle_mouse_look(game_state)
        keys = pygame.key.get_pressed()
        playerSystem.handle_movement(game_state, keys)

        # --- Weapon swap ---
        gunSystem.update_weapon_swap(game_state)

        # --- Pickup system ---
        pickupSystem.update_dropped_items(game_state)
        pickupSystem.update_healing(game_state)

        # --- Animations ---
        animationSystem.update_animations(game_state)

        # --- Screen shake ---
        shake_x, shake_y = 0, 0
        if pygame.time.get_ticks() - game_state.shake_timer < SHAKE_DURATION:
            shake_x = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)
            shake_y = random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY)

        # =====================================================================
        # RENDERING
        # =====================================================================
        base_surf = pygame.Surface((WIDTH, HEIGHT))

        # Sky
        renderSystem.render_sky(base_surf, game_state.player_angle)

        # Ground
        ground_color = LIGHTGRAY if game_state.player_z > 0 else DARKGRAY
        pygame.draw.rect(base_surf, ground_color, (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))

        # Walls (raycasting)
        if game_state.player_pos is not None:
            renderSystem.ray_casting(base_surf, game_state.player_pos[0],
                                     game_state.player_pos[1], game_state.player_angle)

        # Entities
        enemySystem.draw_enemies(base_surf, game_state)
        pickupSystem.draw_dropped_items(base_surf, game_state)

        # Effects
        gunSystem.draw_bullets(base_surf, game_state)
        gunSystem.draw_muzzle_flash(base_surf, game_state)
        renderSystem.draw_blood_screen(base_surf, game_state)
        animationSystem.draw_animations(base_surf, game_state)
        animationSystem.draw_screen_flash(base_surf, game_state)

        # HUD
        renderSystem.draw_hud(base_surf, game_state)
        renderSystem.draw_minimap(base_surf, game_state)

        # Gun (drawn last, on top of everything)
        gunSystem.draw_gun(base_surf, game_state)

        # Jump shadow
        renderSystem.draw_jump_shadow(base_surf, game_state)

        # Low HP overlay
        renderSystem.draw_low_hp_overlay(base_surf, game_state)

        # --- Sniper scope or normal crosshair ---
        if not renderSystem.draw_sniper_scope(screen, base_surf, game_state):
            renderSystem.draw_crosshair(base_surf, game_state)
            screen.blit(base_surf, (shake_x, shake_y))

        # =====================================================================
        # GAME STATE CHECKS
        # =====================================================================

        # Win check
        if mapSystem.check_win(game_state):
            renderSystem.show_round_stats(screen, game_state)
            continue

        # Time up
        if mapSystem.check_time_up(game_state):
            renderSystem.show_message(screen, "TIME UP! Press R to restart or Q to quit", ORANGE, "medium")
            _wait_for_restart_or_quit(game_state)

        # Enemy AI + death check
        if enemySystem.enemy_ai(game_state) or game_state.player_hp <= 0:
            renderSystem.show_message(screen, "YOU DIED! Press R to restart or Q to quit", RED, "medium")
            _wait_for_restart_or_quit(game_state)

        pygame.display.flip()
        clock.tick(60)


def _wait_for_restart_or_quit(game_state):
    """Block until the player presses R (restart) or Q (quit)."""
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_state.reset()
                    waiting = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
        pygame.time.wait(100)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    renderSystem.landing_screen(screen)
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    renderSystem.show_message(screen, "GET READY!", YELLOW, "large", 800)
    game_loop()
