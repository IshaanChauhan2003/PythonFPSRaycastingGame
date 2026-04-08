"""
renderSystem.py - Raycasting renderer, sky, HUD, minimap, crosshair,
                  blood screen, messages, and round stats screen.
"""

import pygame
import math
import sys
from config import (
    WIDTH, HEIGHT, HALF_WIDTH, HALF_HEIGHT,
    FOV, NUM_RAYS, MAX_DEPTH, DELTA_ANGLE, DIST, PROJ_COEFF, SCALE, TILE,
    ROUND_TIME, MAX_BULLETS, MAX_HEALTH_KITS, MAX_SHOTGUN_AMMO,
    LOW_HP_THRESHOLD, SNIPER_SCOPE_ZOOM,
    BLACK, DARKGRAY, RED, GREEN, WHITE, YELLOW, BLUE, ORANGE, LIGHTGRAY,
    load_image, resource_path
)
from mechanics import mapSystem

# Module-level assets (set during init)
_sky_texture = None
_ground_texture = None
_player_icon = None
_home_bg = None
font_small = None
font_medium = None
font_large = None


def init():
    """Load rendering assets and create fonts. Call after pygame.init()."""
    global _sky_texture, _ground_texture, _player_icon, _home_bg
    global font_small, font_medium, font_large

    _sky_texture = pygame.image.load(resource_path("assets/images/sky.png")).convert_alpha()
    _ground_texture = pygame.image.load(resource_path("assets/images/ground.png")).convert()
    _player_icon = load_image(resource_path("assets/images/player.png"), scale=(32, 32))
    _home_bg = pygame.image.load(resource_path("assets/images/homeBg.png")).convert()
    _home_bg = pygame.transform.scale(_home_bg, (WIDTH, HEIGHT))

    font_small = pygame.font.SysFont("Arial", 16)
    font_medium = pygame.font.SysFont("Arial", 24)
    font_large = pygame.font.SysFont("Arial", 48)


# =============================================================================
# SKY / GROUND
# =============================================================================

def render_sky(surface, player_angle):
    """Draw the scrolling sky panorama."""
    offset = int(player_angle * (_sky_texture.get_width() / (2 * math.pi))) % _sky_texture.get_width()
    surface.blit(_sky_texture, (-offset, 0))
    surface.blit(_sky_texture, (-offset + _sky_texture.get_width(), 0))
    if offset > 0:
        surface.blit(_sky_texture, (-offset - _sky_texture.get_width(), 0))


# =============================================================================
# RAYCASTING
# =============================================================================

def ray_casting(surface, px, py, pa):
    """Cast rays and draw textured walls."""
    cur_angle = pa - FOV / 2
    for ray in range(NUM_RAYS):
        sin_a = math.sin(cur_angle)
        cos_a = math.cos(cur_angle)
        for depth in range(MAX_DEPTH):
            x = px + depth * cos_a
            y = py + depth * sin_a
            i, j = int(x / TILE), int(y / TILE)
            if (0 <= i < mapSystem.MAP_WIDTH and 0 <= j < mapSystem.MAP_HEIGHT
                    and mapSystem.MAP[j][i] == '#'):
                depth *= math.cos(pa - cur_angle)
                proj_height = PROJ_COEFF / (depth + 0.0001)
                color_val = int(255 / (1 + depth * depth * 0.0001))
                pygame.draw.rect(surface, (color_val, color_val, color_val),
                                 (ray * SCALE, HALF_HEIGHT - proj_height // 2, SCALE, proj_height))
                break
        cur_angle += DELTA_ANGLE


# =============================================================================
# CROSSHAIR
# =============================================================================

def draw_crosshair(surface, game_state):
    """Draw animated crosshair that changes color based on game state."""
    center = (HALF_WIDTH, HALF_HEIGHT)
    crosshair_color = YELLOW
    crosshair_size = 6  # Reduced from 10 to 6

    # Check if aiming at an enemy
    enemy_in_crosshair = False
    if game_state.player_pos is not None:
        for enemy in game_state.enemies:
            if enemy.get('detected', False):
                dx = enemy['pos'][0] - game_state.player_pos[0]
                dy = enemy['pos'][1] - game_state.player_pos[1]
                enemy_angle = math.atan2(dy, dx)
                angle_diff = enemy_angle - game_state.player_angle
                if angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                elif angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                if abs(angle_diff) < 0.1:
                    enemy_in_crosshair = True
                    break

    if enemy_in_crosshair:
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.02)) * 50
        crosshair_color = (255, 255 - int(pulse), 255 - int(pulse))
        crosshair_size = 8 + int(pulse * 0.08)  # Reduced from 12 + pulse*0.1
    elif game_state.is_healing:
        crosshair_color = GREEN
    elif game_state.is_reloading:
        crosshair_color = ORANGE

    pygame.draw.line(surface, crosshair_color,
                     (center[0] - crosshair_size, center[1]), (center[0] + crosshair_size, center[1]), 2)
    pygame.draw.line(surface, crosshair_color,
                     (center[0], center[1] - crosshair_size), (center[0], center[1] + crosshair_size), 2)
    pygame.draw.circle(surface, crosshair_color, center, 2)


# =============================================================================
# HUD
# =============================================================================

def draw_hud(surface, game_state):
    """Draw the full heads-up display."""
    # --- Health Bar ---
    hp_ratio = game_state.player_hp / 100
    bg_color = (40, 0, 0)
    if game_state.player_hp < LOW_HP_THRESHOLD:
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 50
        bg_color = (40 + int(pulse), 0, 0)
    pygame.draw.rect(surface, bg_color, (20, 18, 210, 28), border_radius=8)
    hp_width = int(206 * hp_ratio)
    if hp_width > 0:
        if hp_ratio > 0.6:
            bar_color = (0, 200, 0)
        elif hp_ratio > 0.3:
            bar_color = (200, 200, 0)
        else:
            bar_color = (200, 0, 0)
        pygame.draw.rect(surface, bar_color, (22, 20, hp_width, 24), border_radius=6)
    pygame.draw.rect(surface, WHITE, (20, 18, 210, 28), 2, border_radius=8)

    hp_text_color = WHITE
    if game_state.player_hp < LOW_HP_THRESHOLD:
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.015)) * 100
        hp_text_color = (255, 255 - int(pulse), 255 - int(pulse))
    hp_text = font_medium.render(f"HP: {game_state.player_hp:3d}", True, hp_text_color)
    surface.blit(hp_text, (32, 22))

    # --- Stamina Bar (Top Center) ---
    from config import MAX_STAMINA
    stamina_bar_width = 300
    stamina_bar_height = 20
    stamina_x = (WIDTH - stamina_bar_width) // 2
    stamina_y = 20
    
    # Background
    stamina_bg_color = (20, 20, 40)
    if game_state.is_exhausted:
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.02)) * 30
        stamina_bg_color = (40 + int(pulse), 0, 0)
    pygame.draw.rect(surface, stamina_bg_color, (stamina_x, stamina_y, stamina_bar_width, stamina_bar_height), border_radius=6)
    
    # Stamina fill
    stamina_ratio = game_state.stamina / MAX_STAMINA
    stamina_fill_width = int((stamina_bar_width - 4) * stamina_ratio)
    
    if stamina_fill_width > 0:
        if game_state.is_exhausted:
            bar_color = (150, 0, 0)
        elif game_state.is_sprinting:
            bar_color = (255, 200, 0)
        elif stamina_ratio > 0.6:
            bar_color = (0, 180, 255)
        elif stamina_ratio > 0.3:
            bar_color = (100, 150, 255)
        else:
            bar_color = (150, 100, 200)
        pygame.draw.rect(surface, bar_color, (stamina_x + 2, stamina_y + 2, stamina_fill_width, stamina_bar_height - 4), border_radius=4)
    
    # Border
    border_color = WHITE
    if game_state.is_exhausted:
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.015)) * 100
        border_color = (255, 255 - int(pulse), 255 - int(pulse))
    pygame.draw.rect(surface, border_color, (stamina_x, stamina_y, stamina_bar_width, stamina_bar_height), 2, border_radius=6)
    
    # Stamina text
    stamina_text_color = WHITE
    if game_state.is_exhausted:
        stamina_label = "EXHAUSTED!"
        stamina_text_color = RED
    elif game_state.is_sprinting:
        stamina_label = f"SPRINTING {int(game_state.stamina)}"
        stamina_text_color = YELLOW
    else:
        stamina_label = f"STAMINA {int(game_state.stamina)}"
    
    stamina_text = font_small.render(stamina_label, True, stamina_text_color)
    text_x = stamina_x + (stamina_bar_width - stamina_text.get_width()) // 2
    text_y = stamina_y + (stamina_bar_height - stamina_text.get_height()) // 2
    surface.blit(stamina_text, (text_x, text_y))

    # --- Ammo Display ---
    ammo_bg = pygame.Surface((180, 40), pygame.SRCALPHA)
    ammo_bg.fill((30, 30, 0, 160))
    surface.blit(ammo_bg, (20, 56))
    bullet_box_w, bullet_box_h = 18, 28
    bullet_gap = 6
    bullet_start_x = 32
    bullet_y = 66
    current_weapon = game_state.current_weapon
    if current_weapon == 'primary':
        for i in range(MAX_BULLETS):
            rect = pygame.Rect(bullet_start_x + i * (bullet_box_w + bullet_gap), bullet_y, bullet_box_w, bullet_box_h)
            color = YELLOW if i < game_state.bullets_left else (80, 80, 40)
            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(surface, BLACK, rect, 2, border_radius=6)
            if i < game_state.bullets_left:
                pygame.draw.ellipse(surface, (220, 220, 80), rect.inflate(-8, -12))
    elif current_weapon == 'shotgun':
        for i in range(4):
            rect = pygame.Rect(bullet_start_x + i * (bullet_box_w + bullet_gap), bullet_y, bullet_box_w, bullet_box_h)
            color = ORANGE if i < game_state.shotgun_bullets else (80, 40, 0)
            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(surface, BLACK, rect, 2, border_radius=6)
            if i < game_state.shotgun_bullets:
                pygame.draw.ellipse(surface, (255, 140, 0), rect.inflate(-8, -12))

    # --- Health Kits ---
    kit_bg_y = 102
    kit_bg = pygame.Surface((120, 40), pygame.SRCALPHA)
    kit_bg.fill((0, 40, 0, 160))
    surface.blit(kit_bg, (20, kit_bg_y))
    kit_icon_rect = pygame.Rect(32, kit_bg_y + 10, 28, 28)
    pygame.draw.rect(surface, (0, 180, 0), kit_icon_rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, kit_icon_rect, 2, border_radius=8)
    pygame.draw.rect(surface, WHITE, (kit_icon_rect.x + 10, kit_icon_rect.y + 4, 8, 20), border_radius=2)
    pygame.draw.rect(surface, WHITE, (kit_icon_rect.x + 4, kit_icon_rect.y + 10, 20, 8), border_radius=2)
    kit_text = font_medium.render(f"x {game_state.health_kits}/{MAX_HEALTH_KITS}", True, WHITE)
    surface.blit(kit_text, (kit_icon_rect.right + 8, kit_icon_rect.y + 4))

    # --- Healing indicator ---
    if game_state.is_healing:
        from config import HEAL_TIME
        heal_progress = (pygame.time.get_ticks() - game_state.heal_start_time) / HEAL_TIME
        heal_text = font_medium.render(f"Healing... {int(heal_progress * 100)}%", True, GREEN)
        surface.blit(heal_text, (32, kit_bg_y + 48))

    # --- Enemy Counter ---
    enemy_bg = pygame.Surface((120, 36), pygame.SRCALPHA)
    enemy_bg.fill((40, 0, 0, 120))
    surface.blit(enemy_bg, (WIDTH - 140, 16))
    pygame.draw.circle(surface, (200, 200, 200), (WIDTH - 120, 34), 12)
    pygame.draw.rect(surface, (200, 200, 200), (WIDTH - 128, 38, 16, 8), border_radius=4)
    enemy_text = font_medium.render(f"{len(game_state.enemies):2d}", True, WHITE)
    surface.blit(enemy_text, (WIDTH - 100, 24))

    # --- Timer ---
    elapsed = pygame.time.get_ticks() / 1000.0 - game_state.round_stats['start_time']
    remaining = max(0, ROUND_TIME - elapsed)
    timer_color = GREEN if remaining > 20 else (YELLOW if remaining > 10 else RED)
    timer_text = font_large.render(f"{int(remaining // 60):02}:{int(remaining % 60):02}", True, timer_color)
    timer_bg = pygame.Surface((timer_text.get_width() + 24, timer_text.get_height() + 12), pygame.SRCALPHA)
    timer_bg.fill((0, 0, 0, 180))
    pygame.draw.rect(timer_bg, timer_color, timer_bg.get_rect(), 2, border_radius=8)
    surface.blit(timer_bg, (WIDTH // 2 - timer_text.get_width() // 2 - 12, 60))
    surface.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 66))


# =============================================================================
# BLOOD SCREEN / LOW HP / SCOPE
# =============================================================================

def draw_blood_screen(surface, game_state):
    """Draw red flash overlay when the player is hit."""
    elapsed = pygame.time.get_ticks() - game_state.blood_screen_timer
    if elapsed < 500:
        alpha = 200 - int(200 * elapsed / 500)
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        surf.fill((255, 0, 0, alpha))
        surface.blit(surf, (0, 0))


def draw_low_hp_overlay(surface, game_state):
    """Draw red corner markers and overlay when HP is low."""
    if game_state.player_hp < LOW_HP_THRESHOLD:
        red_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        red_overlay.fill((255, 0, 0, 80))
        ml, mt = 60, 8
        corners = [
            (0, 0, ml, mt), (0, 0, mt, ml),
            (WIDTH - ml, 0, ml, mt), (WIDTH - mt, 0, mt, ml),
            (0, HEIGHT - ml, mt, ml), (0, HEIGHT - mt, ml, mt),
            (WIDTH - ml, HEIGHT - mt, ml, mt), (WIDTH - mt, HEIGHT - ml, mt, ml),
        ]
        for rect_args in corners:
            pygame.draw.rect(red_overlay, (255, 0, 0, 180), rect_args)
        surface.blit(red_overlay, (0, 0))


def draw_jump_shadow(surface, game_state):
    """Draw shadow ellipse when the player is airborne."""
    if game_state.player_pos is not None and game_state.player_z > 0:
        shadow_x = HALF_WIDTH
        shadow_y = HEIGHT - 60
        shadow_radius = 30 + int(game_state.player_z * 0.2)
        shadow_alpha = max(60, 180 - int(game_state.player_z * 2))
        shadow_surf = pygame.Surface((shadow_radius * 2, shadow_radius), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (0, 0, shadow_radius * 2, shadow_radius))
        surface.blit(shadow_surf, (shadow_x - shadow_radius, shadow_y))


def draw_sniper_scope(screen, base_surf, game_state):
    """Render the sniper scope zoom overlay. Returns True if scope was drawn."""
    if game_state.current_weapon == 'sniper' and game_state.is_scoping:
        zoom = SNIPER_SCOPE_ZOOM
        zoomed = pygame.transform.smoothscale(base_surf, (int(WIDTH * zoom), int(HEIGHT * zoom)))
        zx = (zoomed.get_width() - WIDTH) // 2
        zy = (zoomed.get_height() - HEIGHT) // 2
        scope_radius = min(WIDTH, HEIGHT) // 2 - 10
        scope_center = (HALF_WIDTH, HALF_HEIGHT)
        # Masked zoomed view
        zoomed_masked = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), scope_center, scope_radius)
        zoomed_masked.blit(zoomed, (-zx, -zy))
        zoomed_masked.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        # Dark overlay
        dark_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 240))
        pygame.draw.circle(dark_overlay, (0, 0, 0, 0), scope_center, scope_radius)
        screen.blit(dark_overlay, (0, 0))
        screen.blit(zoomed_masked, (0, 0))
        # Scope ring and crosshair
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (80, 80, 80, 180), scope_center, scope_radius + 6, 12)
        pygame.draw.circle(overlay, (0, 0, 0, 0), scope_center, scope_radius - 2)
        cross_len = scope_radius - 8
        pygame.draw.line(overlay, (0, 0, 0), (HALF_WIDTH - cross_len, HALF_HEIGHT),
                         (HALF_WIDTH + cross_len, HALF_HEIGHT), 2)
        pygame.draw.line(overlay, (0, 0, 0), (HALF_WIDTH, HALF_HEIGHT - cross_len),
                         (HALF_WIDTH, HALF_HEIGHT + cross_len), 2)
        screen.blit(overlay, (0, 0))
        return True
    return False


# =============================================================================
# MINIMAP
# =============================================================================

def draw_minimap(surface, game_state):
    """Draw the bottom-left minimap showing walls, player, enemies, and goal."""
    map_size = 150
    cell_size = map_size // max(mapSystem.MAP_WIDTH, mapSystem.MAP_HEIGHT)
    offset_x, offset_y = 10, HEIGHT - map_size - 10

    pygame.draw.rect(surface, BLACK, (offset_x - 2, offset_y - 2, map_size + 4, map_size + 4))
    pygame.draw.rect(surface, DARKGRAY, (offset_x, offset_y, map_size, map_size))

    for j in range(mapSystem.MAP_HEIGHT):
        for i in range(mapSystem.MAP_WIDTH):
            if mapSystem.MAP[j][i] == '#':
                pygame.draw.rect(surface, WHITE,
                                 (offset_x + i * cell_size, offset_y + j * cell_size, cell_size, cell_size))

    if game_state.player_pos is not None:
        pmx = offset_x + int(game_state.player_pos[0] / TILE * cell_size)
        pmy = offset_y + int(game_state.player_pos[1] / TILE * cell_size)
        pygame.draw.circle(surface, GREEN, (pmx, pmy), 3)
        end_x = pmx + 10 * math.cos(game_state.player_angle)
        end_y = pmy + 10 * math.sin(game_state.player_angle)
        pygame.draw.line(surface, GREEN, (pmx, pmy), (end_x, end_y), 2)

    for enemy in game_state.enemies:
        emx = offset_x + int(enemy['pos'][0] / TILE * cell_size)
        emy = offset_y + int(enemy['pos'][1] / TILE * cell_size)
        color = RED if enemy.get('detected', False) else DARKGRAY
        pygame.draw.circle(surface, color, (emx, emy), 3)

    if game_state.goal_pos is not None:
        gmx = offset_x + int(game_state.goal_pos[0] / TILE * cell_size)
        gmy = offset_y + int(game_state.goal_pos[1] / TILE * cell_size)
        pygame.draw.circle(surface, BLUE, (gmx, gmy), 4)


# =============================================================================
# MESSAGES / SCREENS
# =============================================================================

def show_message(screen, text, color=WHITE, size="medium", duration=0):
    """Display a centered message box on screen."""
    if size == "large":
        font = font_large
    elif size == "small":
        font = font_small
    else:
        font = font_medium
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(HALF_WIDTH, HALF_HEIGHT))
    bg_rect = text_rect.inflate(20, 20)
    pygame.draw.rect(screen, BLACK, bg_rect)
    pygame.draw.rect(screen, color, bg_rect, 2)
    screen.blit(text_surf, text_rect)
    pygame.display.flip()
    if duration > 0:
        pygame.time.wait(duration)


def show_round_stats(screen, game_state):
    """Display round completion stats and wait for player choice."""
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    time_taken = pygame.time.get_ticks() / 1000.0 - game_state.round_stats['start_time']
    game_state.round_stats['time_taken'] = float(time_taken)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    title = font_large.render(f"ROUND {mapSystem.current_map_index + 1} COMPLETE!", True, YELLOW)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

    stats = [
        f"Enemies Killed: {game_state.round_stats['enemies_killed']}",
        f"Damage Dealt: {game_state.round_stats['damage_dealt']}",
        f"Damage Taken: {game_state.round_stats['damage_taken']}",
        f"Time Taken: {time_taken:.1f} seconds"
    ]
    for i, stat in enumerate(stats):
        text = font_medium.render(stat, True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 200 + i * 40))

    continue_btn = pygame.Rect(WIDTH // 2 - 150, 400, 300, 50)
    exit_btn = pygame.Rect(WIDTH // 2 - 150, 470, 300, 50)
    pygame.draw.rect(screen, GREEN, continue_btn, border_radius=12)
    pygame.draw.rect(screen, RED, exit_btn, border_radius=12)
    cont_text = font_medium.render("CONTINUE TO NEXT ROUND", True, BLACK)
    exit_text = font_medium.render("EXIT GAME", True, BLACK)
    screen.blit(cont_text, (continue_btn.centerx - cont_text.get_width() // 2,
                             continue_btn.centery - cont_text.get_height() // 2))
    screen.blit(exit_text, (exit_btn.centerx - exit_text.get_width() // 2,
                            exit_btn.centery - exit_text.get_height() // 2))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if continue_btn.collidepoint(mouse_pos):
                    mapSystem.switch_map(mapSystem.current_map_index + 1)
                    game_state.reset()
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    return True
                elif exit_btn.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
        pygame.time.wait(100)


def landing_screen(screen):
    """Show the title/landing screen with a Start button and background image."""
    # Draw background
    screen.blit(_home_bg, (0, 0))
    
    # Semi-transparent overlay for better text visibility
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))
    
    title = font_large.render("FPS AND SHIT IN PYTHON", True, YELLOW)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
    subtitle = font_medium.render("by Ishaan Chauhan", True, LIGHTGRAY)
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 200))
    start_btn = pygame.Rect(WIDTH // 2 - 120, 320, 240, 60)
    pygame.draw.rect(screen, GREEN, start_btn, border_radius=16)
    start_text = font_large.render("START", True, BLACK)
    screen.blit(start_text, (start_btn.centerx - start_text.get_width() // 2,
                              start_btn.centery - start_text.get_height() // 2))
    pygame.display.flip()
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(pygame.mouse.get_pos()):
                    waiting = False
        pygame.time.wait(100)
