"""
gameState.py - Central game state management.
"""

import pygame
from config import (
    MAX_BULLETS, SNIPER_BULLETS, TILE, MAX_STAMINA
)
from mechanics import mapSystem


class GameState:
    """Holds all mutable game state for a single play session."""

    def __init__(self):
        # Player
        self.player_pos = None
        self.player_angle = 0.0
        self.player_hp = 100
        self.player_z = 0.0
        self.player_vz = 0.0
        self.is_jumping = False
        
        # Stamina system
        self.stamina = MAX_STAMINA
        self.is_sprinting = False
        self.is_exhausted = False
        self.exhaustion_start_time = 0
        self.last_sprint_time = 0

        # Goal
        self.goal_pos = None

        # Enemies
        self.enemies = []

        # Visual effects
        self.muzzle_flash_timer = 0
        self.bullet_lines = []
        self.blood_screen_timer = 0
        self.shake_timer = 0
        self.jump_slow_timer = 0

        # Round stats
        self.round_stats = {
            'enemies_killed': 0,
            'damage_dealt': 0,
            'damage_taken': 0,
            'time_taken': 0.0,
            'start_time': 0
        }

        # Primary weapon
        self.bullets_left = MAX_BULLETS
        self.is_reloading = False
        self.reload_start_time = 0

        # Weapon system
        self.current_weapon = 'primary'  # 'primary', 'shotgun', or 'sniper'
        self.is_swapping = False
        self.swap_start_time = 0
        self.swap_to = 'primary'

        # Shotgun
        self.shotgun_bullets = 4
        self.last_shotgun_shot_time = 0
        self.shotgun_recoil_timer = 0

        # Sniper
        self.sniper_bullets = SNIPER_BULLETS
        self.last_sniper_shot_time = 0
        self.sniper_recoil_timer = 0
        self.is_scoping = False
        self.scope_start_time = 0
        self.scope_zoom = 1.0

        # Pickup system
        self.dropped_items = []
        self.health_kits = 0
        self.is_healing = False
        self.heal_start_time = 0

        # Animation state
        self.screen_flash_timer = 0
        self.screen_flash_color = (255, 255, 255)
        self.damage_numbers = []
        self.particles = []
        self.enemy_death_animations = []
        self.enemy_hit_flashes = []
        self.ui_fade_timer = 0
        self.ui_fade_alpha = 255

        # Parse the current map to set positions
        self.parse_map()

    def parse_map(self):
        """Read the current map and place player, enemies, and goal."""
        self.enemies = []
        for j, row in enumerate(mapSystem.MAP):
            for i, ch in enumerate(row):
                if ch == 'S':
                    self.player_pos = [int(i * TILE + TILE // 2),
                                       int(j * TILE + TILE // 2)]
                elif ch == 'W':
                    self.goal_pos = (int(i * TILE + TILE // 2),
                                     int(j * TILE + TILE // 2))
                elif ch == 'E':
                    self.enemies.append({
                        'pos': [int(i * TILE + TILE // 2),
                                int(j * TILE + TILE // 2)],
                        'hp': 100,
                        'last_shot': 0,
                        'detected': False
                    })
        self.round_stats['start_time'] = pygame.time.get_ticks() / 1000.0

    def reset(self):
        """Reset all game state for a new round (keeps current map)."""
        self.player_hp = 100
        self.player_angle = 0.0
        self.enemies = []
        self.player_pos = [0, 0]
        self.parse_map()
        
        # Reset stamina
        self.stamina = MAX_STAMINA
        self.is_sprinting = False
        self.is_exhausted = False
        self.exhaustion_start_time = 0
        self.last_sprint_time = 0

        self.muzzle_flash_timer = 0
        self.bullet_lines = []
        self.blood_screen_timer = 0
        self.player_z = 0.0
        self.player_vz = 0.0
        self.is_jumping = False
        self.bullets_left = MAX_BULLETS
        self.is_reloading = False
        self.reload_start_time = 0
        self.shake_timer = 0
        self.jump_slow_timer = 0

        self.round_stats = {
            'enemies_killed': 0,
            'damage_dealt': 0,
            'damage_taken': 0,
            'time_taken': 0.0,
            'start_time': pygame.time.get_ticks() / 1000.0
        }

        self.current_weapon = 'primary'
        self.is_swapping = False
        self.swap_start_time = 0
        self.swap_to = 'primary'
        self.shotgun_bullets = 4
        self.last_shotgun_shot_time = 0
        self.shotgun_recoil_timer = 0

        self.sniper_bullets = SNIPER_BULLETS
        self.last_sniper_shot_time = 0
        self.sniper_recoil_timer = 0
        self.is_scoping = False
        self.scope_start_time = 0
        self.scope_zoom = 1.0

        self.dropped_items = []
        self.health_kits = 0
        self.is_healing = False
        self.heal_start_time = 0

        self.screen_flash_timer = 0
        self.screen_flash_color = (255, 255, 255)
        self.damage_numbers = []
        self.particles = []
        self.enemy_death_animations = []
        self.enemy_hit_flashes = []
        self.ui_fade_timer = 0
        self.ui_fade_alpha = 255
