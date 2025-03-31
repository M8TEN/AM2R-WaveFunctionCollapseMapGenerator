import json
import time
from copy import deepcopy
from random import randint, seed

WIDTH = 74 # Width of the map to generate. Maximum is 74
HEIGHT = 57 # Height of the map to generate. Maximum is 57
START = (3,3) # Coordinate of the top-left corner in the output space

# Data Container class to hold information about a tile in the grid
class Tile:
    def __init__(self, r: int, u: int, l: int, d: int):
        self.r = r
        self.u = u
        self.l = l
        self.d = d

# Returns a dict where coordinate tuples are the key and None is the value
def create_grid(w: int, h: int) -> dict:
    grid = {}
    for y in range(h):
        for x in range(w):
            grid[(x,y)] = None
    
    return grid

# Returns a list of all rooms with only 1 door
def get_dead_ends(data: list) -> list:
    dead_ends = []
    for room in data:
        if room["IsDeadEnd"]:
            dead_ends.append(room)
    
    return dead_ends

# Returns true if the room has a door that points in the direction of door_dir. door_dir is an index into the layout tile's data
def has_door(layout: dict, door_dir: int) -> bool:
    for tile in layout.values():
        if tile[door_dir] == 2:
            return True
    
    return False

# Returns a list of rooms filtered by their probability (weight) and if they have a door in the direction given
def get_possible_rooms(door_dir):
    possible_rooms = [r for r in room_data if r["Weight"] > 0]
    idx = 0
    while idx < len(possible_rooms):
        room = possible_rooms[idx]
        if not has_door(room["Layout"], door_dir):
            del possible_rooms[idx]
            continue
        else:
            idx += 1
    
    return possible_rooms

# Returns a list of local coordinate keys with tiles that have doors in the given door direction
def start_positions(layout: dict, door_dir: int) -> list:
    positions = []
    for key in layout:
        if layout[key][door_dir] == 2:
            positions.append(key)
    return positions

# Checks if a room can go next to another room
def validate_room_position(grid: dict, global_start_pos: tuple, relative_key: str, layout: dict) -> bool:
    relative_door_position = tuple(map(int, relative_key.split(",")))
    draw_begin = (global_start_pos[0] - relative_door_position[0], global_start_pos[1] - relative_door_position[1])
    for key in layout:
        relative_tile_pos = tuple(map(int, key.split(",")))
        global_tile_pos = (draw_begin[0] + relative_tile_pos[0], draw_begin[1] + relative_tile_pos[1])
        if global_tile_pos[0] < 0 or global_tile_pos[0] >= WIDTH or global_tile_pos[1] < 0 or global_tile_pos[1] >= HEIGHT or grid[global_tile_pos] != None or\
            (global_tile_pos[0] == 0 and layout[key][2] == 2) or (global_tile_pos[0] == WIDTH-1 and layout[key][0] == 2) or\
            (global_tile_pos[1] == 0 and layout[key][1] == 2) or (global_tile_pos[1] == HEIGHT-1 and layout[key][3] == 2):
            return False
    
        right_pos = (global_tile_pos[0] + 1, global_tile_pos[1])
        top_pos = (global_tile_pos[0], global_tile_pos[1] - 1)
        left_pos = (global_tile_pos[0] - 1, global_tile_pos[1])
        bottom_pos = (global_tile_pos[0], global_tile_pos[1] + 1)

        if ((right_pos[0] >= WIDTH or (grid[right_pos] and grid[right_pos].l == 1)) and layout[key][0] == 2)\
            or ((top_pos[1] < 0 or (grid[top_pos] and grid[top_pos].d == 1)) and layout[key][1] == 2)\
            or ((left_pos[0] < 0 or (grid[left_pos] and grid[left_pos].r == 1)) and layout[key][2] == 2)\
            or ((bottom_pos[1] >= HEIGHT or (grid[bottom_pos] and grid[bottom_pos].u == 1)) and layout[key][3] == 2):
            return False

        if right_pos[0] < WIDTH:
            if (grid[right_pos] and grid[right_pos].l == 2) and layout[key][0] == 1:
                return False
        if top_pos[1] > 0:
            if (grid[top_pos] and grid[top_pos].d == 2) and layout[key][1] == 1:
                return False
        if left_pos[0] > 0:
            if (grid[left_pos] and grid[left_pos].r == 2) and layout[key][2] == 1:
                return False
        if bottom_pos[1] < HEIGHT:
            if (grid[bottom_pos] and grid[bottom_pos].u == 2) and layout[key][3] == 1:
                return False

    return True

# Writes the tile data into the grid
def draw_room(draw_begin: tuple, layout: dict, open_connections: list):
    last_tile_placed: Tile = None
    for key in layout:
        tile_pos = tuple(map(int, key.split(",")))
        grid_pos = (draw_begin[0] + tile_pos[0], draw_begin[1] + tile_pos[1])
        tile_data = layout[key]
        grid[grid_pos] = Tile(tile_data[0], tile_data[1], tile_data[2], tile_data[3])
        last_tile_placed = grid[grid_pos]
        if tile_data[0] == 2:
            open_connections.append([(grid_pos[0] + 1, grid_pos[1]), 2])
        if tile_data[1] == 2:
            open_connections.append([(grid_pos[0], grid_pos[1] - 1), 3])
        if tile_data[2] == 2:
            open_connections.append([(grid_pos[0] - 1, grid_pos[1]), 0])
        if tile_data[3] == 2:
            open_connections.append([(grid_pos[0], grid_pos[1] + 1), 1])
    
    if len(layout) == 1 and (int(has_door(layout, 0)) + int(has_door(layout, 1)) + int(has_door(layout, 2)) + int(has_door(layout, 3)) == 1):
        placed_dead_ends.append(draw_begin)

# Recursively creates branches of rooms until the grid is fully populated or no more room can be placed
def generate(grid, next_tile, door_dir, depth = 0):
    possible_rooms = get_possible_rooms(door_dir)
    possible_connections = []

    for room in possible_rooms:
        connection_points = start_positions(room["Layout"], door_dir)
        allowed_connections = []
        for connection in connection_points:
            if validate_room_position(grid, next_tile, connection, room["Layout"]):
                allowed_connections.append(connection)
        possible_connections.append(allowed_connections)
    
    possible_rooms = [r for r in possible_rooms if len(possible_connections[possible_rooms.index(r)]) > 0]
    possible_connections = [c for c in possible_connections if len(c) > 0]
    if len(possible_rooms) == 0:
        if grid[next_tile]:
            return
        ends = deepcopy(dead_ends)
        ends = [e for e in ends if has_door(e["Layout"], door_dir)]
        valid_connections = []
        for e in ends:
            end_connections = []
            entrances = start_positions(e["Layout"], door_dir)
            for connection in entrances:
                if validate_room_position(grid, next_tile, connection, e["Layout"]):
                    end_connections.append(connection)
            valid_connections.append(end_connections)
        
        ends = [e for e in ends if len(valid_connections[ends.index(e)]) > 0]
        valid_connections = [c for c in valid_connections if len(c) > 0]
        end_to_place_idx = randint(0, len(ends)-1)
        end_chosen = ends[end_to_place_idx]
        end_offset_str = valid_connections[end_to_place_idx][randint(0, len(valid_connections[end_to_place_idx])-1)]
        end_offset = tuple(map(int, end_offset_str.split(",")))
        draw_begin = (next_tile[0] - end_offset[0], next_tile[1] - end_offset[1])
        draw_room(draw_begin, end_chosen["Layout"], [])
        return


    room_to_place_idx = randint(0, len(possible_rooms)-1)
    room_chosen = possible_rooms[room_to_place_idx]
    room_offset_str = possible_connections[room_to_place_idx][randint(0, len(possible_connections[room_to_place_idx])-1)]
    room_offset = tuple(map(int, room_offset_str.split(",")))
    draw_begin = (next_tile[0] - room_offset[0], next_tile[1] - room_offset[1])
    open_connections = []
    draw_room(draw_begin, room_chosen["Layout"], open_connections)
    
    
    for connection in open_connections:
        generate(grid, connection[0], connection[1], depth + 1)
        

    
# START OF MAIN PROGRAM
start_time = time.time()
#seed(100)

with open("Test.json", "r") as file:
    room_data = json.load(file)

grid = create_grid(WIDTH, HEIGHT)
dead_ends = get_dead_ends(room_data)
start_pos = (randint(0, WIDTH-1), randint(0, HEIGHT-1))

if start_pos[0] == 0:
    possible_start_tiles = [Tile(2, 1, 1, 1)]
elif start_pos[0] == WIDTH-1:
    possible_start_tiles = [Tile(1, 1, 2, 1)]
else:
    possible_start_tiles = [
    Tile(2, 1, 1, 1),
    Tile(1, 1, 2, 1),
]

start_tile = possible_start_tiles[randint(0, len(possible_start_tiles)-1)]
grid[start_pos] = start_tile

if start_tile.r == 2:
    next_pos = (start_pos[0] + 1, start_pos[1])
    direction = 2
elif start_tile.l == 2:
    next_pos = (start_pos[0] - 1, start_pos[1])
    direction = 0
else:
    next_pos = start_pos
    direction = 0

placed_dead_ends = []
generate(grid, next_pos, direction, 0)

# Format output

prototype_tile = {
    "color": 0,
    "corner": 0,
    "isCorner": False,
    "special": 0,
    "wallD": 1,
    "wallL": 1,
    "wallU": 1,
    "wallR": 1,
    "x": 0,
    "y": 0
}

out = []
boss_tile = placed_dead_ends[randint(0, len(placed_dead_ends)-1)]

for position in grid:
    if grid[position] != None:
        new_tile = deepcopy(prototype_tile)
        new_tile["wallL"] = grid[position].l
        new_tile["wallU"] = grid[position].u
        new_tile["wallD"] = grid[position].d
        new_tile["wallR"] = grid[position].r
        new_tile["x"] = position[0] + START[0]
        new_tile["y"] = position[1] + START[1]
        if position == start_pos:
            new_tile["special"] = 1
        if position == boss_tile:
            new_tile["special"] = 4
        out.append(new_tile)

with open("BranchingOutput.json", "w") as file:
    json.dump(out, file, indent=2)

print(f"Execution time: {(time.time() - start_time)}s")
print("Done")