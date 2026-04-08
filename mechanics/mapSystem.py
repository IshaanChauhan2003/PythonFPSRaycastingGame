"""
mapSystem.py - Map data, pathfinding, and map-related utilities.
"""

import math
import random
import heapq
from config import TILE

# =============================================================================
# MAP DEFINITIONS
# =============================================================================

MAPS = [
    [
        "###############################",
        "#....E........#........E..#.W.#",
        "#.##...#####..###....###...E..#",
        "#.#....#...##...#......####.E##",
        "###..###.#.#....###..###......#",
        "#....#...#...........E.#..##.##",
        "#..###############.E##.####...#",
        "#..........E..#........#..#...#",
        "#..#########..##########.##.E.#",
        "#......#...#..#..E........#..##",
        "####.......#..#..#..####..#.E.#",
        "#.S..#.....#.....#..E..#......#",
        "###############################"
    ],
    [
        "###############################",
        "#..E..#....#..E..#....#..E..W.#",
        "#..##..###..##..###..##..###..#",
        "#.#....#...##...#......####.E##",
        "###..###.#.#....###..###......#",
        "#....#...#...........E.#..##.##",
        "#..###############.E##.####...#",
        "#..........E..#........#..#...#",
        "#..#########..##########.##.E.#",
        "#......#...#..#..E........#..##",
        "####.......#..#..#..####..#.E.#",
        "#.S..#.....#.....#..E..#......#",
        "###############################"
    ],
    [
        "###############################",
        "#E..#..E..#..E..#..E..#..E..W.#",
        "#..##..###..##..###..##..###..#",
        "#.#....#...##...#......####.E##",
        "###..###.#.#....###..###......#",
        "#....#...#...........E.#..##.##",
        "#..###############.E##.####...#",
        "#..........E..#........#..#...#",
        "#..#########..##########.##.E.#",
        "#......#...#..#..E........#..##",
        "####.......#..#..#..####..#.E.#",
        "#.S..#.....#.....#..E..#......#",
        "###############################"
    ]
]

# Mutable module-level state (accessed via mapSystem.MAP etc.)
current_map_index = 0
MAP = MAPS[current_map_index]
MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)


# =============================================================================
# MAP UTILITIES
# =============================================================================

def switch_map(index):
    """Switch to a new map by index. Wraps around if index exceeds available maps."""
    global current_map_index, MAP, MAP_WIDTH, MAP_HEIGHT
    current_map_index = index % len(MAPS)
    MAP = MAPS[current_map_index]
    MAP_WIDTH = len(MAP[0])
    MAP_HEIGHT = len(MAP)


def check_wall(x, y):
    """Return True if position (x, y) is walkable (not a wall)."""
    i, j = int(x / TILE), int(y / TILE)
    return 0 <= i < MAP_WIDTH and 0 <= j < MAP_HEIGHT and MAP[j][i] != '#'


def check_win(game_state):
    """Check if the player has reached the goal."""
    if game_state.player_pos is None or game_state.goal_pos is None:
        return False
    dx = game_state.player_pos[0] - game_state.goal_pos[0]
    dy = game_state.player_pos[1] - game_state.goal_pos[1]
    return math.hypot(dx, dy) < TILE


def check_time_up(game_state):
    """Check if the round time has expired."""
    import pygame
    from config import ROUND_TIME
    elapsed = pygame.time.get_ticks() / 1000.0 - game_state.round_stats['start_time']
    return elapsed >= ROUND_TIME


def get_open_tiles(player_pos, min_distance_from_player=5):
    """Return all open tiles at least min_distance tiles from the player."""
    open_tiles = []
    for j, row in enumerate(MAP):
        for i, ch in enumerate(row):
            if ch != '#':
                x = i * TILE + TILE // 2
                y = j * TILE + TILE // 2
                if player_pos:
                    dist = math.hypot(x - player_pos[0], y - player_pos[1])
                    if dist > min_distance_from_player * TILE:
                        open_tiles.append((i, j))
    return open_tiles


def tile_line_of_sight(i1, j1, i2, j2):
    """Check line of sight between two tiles using Bresenham's algorithm."""
    dx = abs(i2 - i1)
    dy = abs(j2 - j1)
    x, y = i1, j1
    n = 1 + dx + dy
    x_inc = 1 if i2 > i1 else -1
    y_inc = 1 if j2 > j1 else -1
    error = dx - dy
    dx *= 2
    dy *= 2
    for _ in range(n):
        if MAP[y][x] == '#':
            return False
        if x == i2 and y == j2:
            break
        if error > 0:
            x += x_inc
            error -= dy
        else:
            y += y_inc
            error += dx
    return True


def astar(start, goal):
    """A* pathfinding from start (i,j) to goal (i,j) on the current map."""
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    def h(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + di, current[1] + dj)
            if 0 <= neighbor[0] < MAP_WIDTH and 0 <= neighbor[1] < MAP_HEIGHT:
                if MAP[neighbor[1]][neighbor[0]] == '#':
                    continue
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + h(neighbor, goal)
                    heapq.heappush(open_set, (f_score, neighbor))
    return []


def get_random_patrol_point():
    """Pick a random walkable tile and return its center position."""
    while True:
        i = random.randint(1, MAP_WIDTH - 2)
        j = random.randint(1, MAP_HEIGHT - 2)
        if MAP[j][i] != '#':
            return [i * TILE + TILE // 2, j * TILE + TILE // 2]
