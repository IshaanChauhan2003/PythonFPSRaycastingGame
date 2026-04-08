"""
audioSystem.py - Sound loading and audio management.
"""

import pygame
from config import resource_path

# =============================================================================
# MODULE STATE (set during init)
# =============================================================================
ambient_sound = None
footstep_sound = None
jump_sound = None
gunshot_sound = None
player_hit_sound = None
enemy_dead_sound = None
shotgunshot_sound = None
pickup_sound = None
heal_sound = None
snipershot_sound = None
footstep_channel = None


# =============================================================================
# SOUND HELPERS
# =============================================================================

def _load_sound(filename, volume=1.0, loop=False):
    """Load a sound file. Returns a silent sound on failure."""
    try:
        sound = pygame.mixer.Sound(filename)
        sound.set_volume(volume)
        if loop:
            sound.play(loops=-1)
        return sound
    except Exception as e:
        print(f"Failed to load sound {filename}: {e}")
        silent = pygame.mixer.Sound(buffer=bytearray(44))
        silent.set_volume(0)
        return silent


# =============================================================================
# INITIALIZATION
# =============================================================================

def init():
    """Load all game sounds. Must be called after pygame.mixer.init()."""
    global ambient_sound, footstep_sound, jump_sound, gunshot_sound
    global player_hit_sound, enemy_dead_sound, shotgunshot_sound
    global pickup_sound, heal_sound, snipershot_sound, footstep_channel

    ambient_sound = _load_sound(resource_path("assets/sounds/ambience.mp3"), volume=0.4, loop=True)
    footstep_sound = _load_sound(resource_path("assets/sounds/footsteps.mp3"), volume=1.0)
    jump_sound = _load_sound(resource_path("assets/sounds/jump.mp3"), volume=1.0)
    gunshot_sound = _load_sound(resource_path("assets/sounds/gunshots.mp3"), volume=0.7)
    player_hit_sound = _load_sound(resource_path("assets/sounds/playerHit.mp3"), volume=0.8)
    enemy_dead_sound = _load_sound(resource_path("assets/sounds/enemyDead.mp3"), volume=0.8)
    shotgunshot_sound = _load_sound(resource_path("assets/sounds/shotgunshots.mp3"), volume=1.0)
    pickup_sound = _load_sound(resource_path("assets/sounds/pickup.mp3"), volume=1.0)
    heal_sound = _load_sound(resource_path("assets/sounds/heal.mp3"), volume=1.0)
    snipershot_sound = _load_sound(resource_path("assets/sounds/snipershots.mp3"), volume=1.0)

    footstep_channel = pygame.mixer.Channel(1)
    footstep_channel.set_volume(1.0)


# =============================================================================
# RUNTIME FUNCTIONS
# =============================================================================

def manage_ambient_sound():
    """Ensure ambient sound keeps playing on its dedicated channel."""
    if ambient_sound and not pygame.mixer.Channel(3).get_busy():
        pygame.mixer.Channel(3).play(ambient_sound, loops=-1)
