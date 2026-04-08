# Raycasting FPS Game

A first-person shooter built with Python and Pygame featuring classic raycasting rendering, multiple weapons, enemy AI, and advanced movement mechanics.

## Table of Contents
- [Controls](#controls)
- [Movement Mechanics](#movement-mechanics)
- [Weapon System](#weapon-system)
- [Stamina & Sprint System](#stamina--sprint-system)
- [Pickup System](#pickup-system)
- [Enemy System](#enemy-system)
- [Game Objectives](#game-objectives)
- [HUD Elements](#hud-elements)

---

## Controls

### Movement
- **W** - Move forward
- **A** - Strafe left
- **S** - Move backward
- **D** - Strafe right
- **Mouse** - Look around (horizontal rotation)
- **Space** - Jump
- **Left Shift / Right Shift** - Sprint (hold)

### Combat
- **Left Mouse Button** - Shoot
- **Right Mouse Button** - Aim down sights (Sniper only)
- **R** - Reload current weapon
- **1** - Switch to Primary (Handgun)
- **2** - Switch to Shotgun
- **3** - Switch to Sniper Rifle

### Items
- **E** - Pick up items (ammo/health kits)
- **Q** - Use health kit (heal)

### System
- **ESC** - Quit game

---

## Movement Mechanics

### Base Movement
- **Base Speed**: 1.8 units/frame
- **Sprint Multiplier**: 1.4x (2.52 units/frame)
- **Exhaustion Penalty**: 0.6x (1.08 units/frame)

### Weapon-Specific Movement Speed
When not sprinting, movement speed is affected by equipped weapon:

+-------------------+----------------+-----------------+
| Weapon            | Speed Modifier | Effective Speed |
|-------------------+----------------+-----------------|
| Primary (Handgun) | 1.0x           | 1.8 units/frame |
| Shotgun           | 0.7x           | 1.26 units/frame|
| Sniper            | 0.55x          | 0.99 units/frame|
+-------------------+----------------+-----------------+

### Jump Mechanics
- **Jump Velocity**: 25.0 units/frame
- **Gravity**: 0.7 units/frame²
- **Weapon Jump Penalties**:
  - Handgun: 1.0x (full jump height)
  - Shotgun: 0.7x (reduced jump)
  - Sniper: 0.6x (minimal jump)

### Low Health Penalties
When HP drops below 40:
- Movement speed reduced by 50%
- Additional 40% speed reduction for 2 seconds after jumping

---

## Weapon System

### Primary Weapon (Handgun)

**Stats:**
- **Damage**: 25 HP per shot
- **Magazine Size**: 9 bullets
- **Reload Time**: 3 seconds
- **Fire Rate**: Semi-automatic (click per shot)
- **Accuracy**: High (±0.06 radians)
- **Movement Speed**: 100% (1.8 units/frame)
- **Sprint Duration**: 10 seconds

**Characteristics:**
- Balanced all-around weapon
- Good for medium-range combat
- Fast movement and handling

---

### Shotgun

**Stats:**
- **Damage**: 
  - Close range (<150 units): 100 HP
  - Medium range (>150 units): 50 HP
- **Magazine Size**: 4 shells
- **Reload Time**: 3 seconds (full reload)
- **Fire Rate**: 800ms between shots
- **Accuracy**: Wide spread (±0.09 radians)
- **Movement Speed**: 70% (1.26 units/frame)
- **Sprint Duration**: 8 seconds

**Characteristics:**
- Devastating at close range
- Slower movement and handling
- Reduced jump height (70%)
- Heavy recoil animation

---

### Sniper Rifle

**Stats:**
- **Damage**: 120 HP per shot
- **Magazine Size**: 5 bullets
- **Reload Time**: 3 seconds
- **Fire Rate**: 1400ms between shots
- **Accuracy**: 
  - Scoped: Very high (±0.04 radians)
  - Unscoped: Low (±0.08 radians, 45% hit chance)
- **Movement Speed**: 55% (0.99 units/frame)
- **Sprint Duration**: 6 seconds
- **Scope Zoom**: 2.2x magnification

**Characteristics:**
- One-shot or two-shot kills
- Requires aiming down sights for accuracy
- Slowest movement speed
- Minimal jump height (60%)
- Long equip time (3 seconds)
- Scope transition time: 200ms

**Scope Controls:**
- Hold Right Mouse Button to scope
- Press X to toggle scope on/off

---

## Stamina & Sprint System

### Stamina Pool
- **Maximum Stamina**: 100 points
- **Recharge Rate**: 0.2 stamina/frame (~12 stamina/second)
- **Recharge Delay**: 1 second after stopping sprint

### Weapon-Specific Sprint Duration

+---------+-------------+-----------------+-----------------+
|  Weapon | Drain Rate  | Sprint Duration | Frames to Empty |
|---------+-------------+-----------------+-----------------|
| Primary | 0.167/frame | 10 seconds      | 600 frames      |
| Shotgun | 0.208/frame | 8 seconds       | 480 frames      |
| Sniper  | 0.278/frame | 6 seconds       | 360 frames      |
+---------+-------------+-----------------+-----------------+

### Sprint Restrictions
Cannot sprint while:
- Jumping
- Healing
- Reloading
- Exhausted
- Weapon swapping

### Exhaustion System

**Trigger**: Stamina reaches 0 while sprinting

**Penalties:**
- Movement speed reduced to 60% of base speed
- Cannot sprint
- Duration: 5 seconds
- Stamina recharge delayed by 3 seconds after exhaustion ends

**Recovery Timeline:**
1. Exhaustion phase: 5 seconds (red pulsing stamina bar)
2. Recharge delay: 3 seconds
3. Full stamina recharge: ~8.3 seconds
4. **Total recovery**: ~16.3 seconds

**Visual Indicators:**
- Stamina bar turns red and pulses
- "EXHAUSTED!" text displayed
- Border flashes red

---

## Pickup System

### Item Types

#### Ammo Pickups
- **Appearance**: Yellow/orange box
- **Effect**: Refills current weapon ammunition
  - Primary: +9 bullets
  - Shotgun: +4 shells
  - Sniper: +5 bullets
- **Pickup Range**: 80 units
- **Drop Source**: Enemies (random drop)

#### Health Kits
- **Appearance**: Green box with cross
- **Effect**: Restores 25 HP
- **Healing Time**: 1.5 seconds (channeled)
- **Maximum Carry**: 2 health kits
- **Pickup Range**: 80 units
- **Drop Source**: Enemies (random drop)

### Pickup Mechanics
1. Approach dropped item (within 80 units)
2. Press **E** to pick up
3. Items hover and animate for visibility
4. Cannot pick up while at maximum capacity

### Using Health Kits
1. Press **Q** to start healing
2. Stand still for 1.5 seconds (channeling)
3. Healing interrupted if:
   - You move
   - You take damage
   - You shoot
4. Restores 25 HP (cannot exceed 100 HP)
5. Health kit consumed after successful heal

---

## Enemy System

### Enemy Stats
- **Health**: 100 HP
- **Movement Speed**: 1.2 units/frame
- **Detection Range**: 400 units (8 tiles)
- **Attack Range**: 250 units (5 tiles)
- **Field of View**: 90° (π/2 radians)
- **Damage**: 20 HP per shot
- **Fire Rate**: 900ms cooldown
- **Lock-on Delay**: 400ms before first shot
- **Accuracy**: 95% hit chance when locked on

### AI States

#### 1. Idle
- Standing still
- Randomly rotates occasionally
- Transitions to Patrol randomly

#### 2. Patrol
- Moves to random waypoints
- Changes direction every 2 seconds
- Scans for player within FOV
- Transitions to Attack if player spotted

#### 3. Chase
- Moves directly toward player
- Maintains line of sight
- Transitions to Attack when in range

#### 4. Attack
- Stops moving
- Aims at player
- Fires after 400ms lock-on delay
- 900ms between shots
- Transitions to Search if line of sight lost

#### 5. Search
- Moves to last known player position
- Transitions to Patrol if position reached
- Returns to Attack if player spotted again

### Enemy Behavior
- **Line of Sight**: Raycasting check for walls
- **Pathfinding**: Direct movement with wall collision
- **Aggro**: Permanent once player is detected
- **Drops**: Random ammo or health kit on death

### Visual Feedback
- Health bar above enemy (green to red)
- Red outline when detected by player
- Death animation with particle effects
- Hit flash effect on damage

---

## Game Objectives

### Round System
- **Time Limit**: 60 seconds per round
- **Objective**: Eliminate all enemies
- **Win Condition**: All enemies defeated before time runs out
- **Lose Conditions**:
  - Player HP reaches 0
  - Time runs out with enemies remaining

### Round Progression
1. Start at spawn point (S on map)
2. Eliminate all enemies (E on map)
3. Reach goal position (W on map)
4. View round statistics
5. Continue to next round or exit

### Round Statistics
- Enemies killed
- Damage dealt
- Damage taken
- Time taken

---

## HUD Elements

### Health Bar (Top Left)
- **Color Coding**:
  - Green: >60 HP
  - Yellow: 30-60 HP
  - Red: <30 HP (pulsing)
- **Low HP Warning**: Red corner markers at <40 HP

### Stamina Bar (Top Center)
- **Color Coding**:
  - Blue: >60% stamina
  - Light Blue: 30-60% stamina
  - Purple: <30% stamina
  - Yellow: Currently sprinting
  - Red (pulsing): Exhausted
- **Status Text**:
  - "STAMINA [value]"
  - "SPRINTING [value]"
  - "EXHAUSTED!"

### Ammo Display (Left Side)
- Visual bullet/shell indicators
- Current magazine capacity
- Color-coded by weapon:
  - Yellow: Primary
  - Orange: Shotgun
  - Cyan: Sniper (when equipped)

### Health Kits (Left Side)
- Green cross icon
- Counter: "x [current]/2"
- Healing progress bar when using

### Enemy Counter (Top Right)
- Enemy icon with count
- Updates in real-time

### Timer (Top Center)
- Countdown from 60 seconds
- **Color Coding**:
  - Green: >20 seconds
  - Yellow: 10-20 seconds
  - Red: <10 seconds

### Minimap (Bottom Left)
- Top-down view of level
- White: Walls
- Green: Player (with direction indicator)
- Red: Detected enemies
- Gray: Undetected enemies
- Blue: Goal position

### Crosshair (Center)
- **Default**: Yellow, 6 pixels
- **Enemy Targeted**: Red pulsing, 8+ pixels
- **Healing**: Green
- **Reloading**: Orange
- **Sniper Scope**: Circular scope with crosshair

---

## Timing Reference

### Weapon Timings

+-------------+---------+---------+--------+
| Action      | Primary | Shotgun | Sniper |
|-------------+---------+---------+--------|
| Reload      | 3.0s    | 3.0s    | 3.0s   |
| Fire Rate   | Instant | 0.8s    | 1.4s   |
| Weapon Swap | 1.0s    | 1.0s    | 3.0s   |
+-------------+---------+---------+--------+

### Animation Timings
- **Muzzle Flash**: 100ms
- **Bullet Trail**: 100ms fade
- **Screen Flash**: 200ms
- **Blood Screen**: 500ms fade
- **Enemy Death**: 800ms
- **Enemy Hit Flash**: 150ms
- **Damage Numbers**: 1000ms
- **Particles**: 1500ms
- **Screen Shake**: 300ms

### Cooldowns
- **Enemy Fire Rate**: 900ms
- **Enemy Lock-on**: 400ms
- **Sniper Fire Rate**: 1400ms
- **Shotgun Fire Rate**: 800ms

---

## Tips & Strategies

1. **Stamina Management**: Don't fully deplete stamina to avoid exhaustion penalty
2. **Weapon Choice**: Use Primary for mobility, Shotgun for close quarters, Sniper for long range
3. **Cover Usage**: Break line of sight to reset enemy aggro
4. **Health Conservation**: Pick up health kits but save them for emergencies
5. **Ammo Economy**: Reload during safe moments, not during combat
6. **Movement**: Strafe while shooting to avoid enemy fire
7. **Positioning**: Use sprint to reposition between engagements
8. **Sniper Scope**: Always scope for accuracy with sniper rifle

---

## Technical Details

- **Engine**: Pygame
- **Rendering**: Raycasting (Wolfenstein 3D style)
- **Resolution**: 800x600
- **Frame Rate**: 60 FPS
- **FOV**: 60° (π/3 radians)
- **Ray Count**: 100 rays
- **Max Render Distance**: 800 units

---

## Credits

**Developer**: Ishaan Chauhan

**Built with**: Python, Pygame

---

## System Requirements

- Python 3.7+
- Pygame 2.0+
- Windows/Linux/macOS
- Mouse and keyboard

---

Enjoy the game!
Run : python app.py
