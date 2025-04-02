import json
import time
import traceback
from copy import deepcopy
from random import randint, uniform, seed

try:
    WIDTH = min(74, abs(int(input("How many tiles wide should the map be? ")))) # Width of the map to generate. Maximum is 74
    HEIGHT = min(57, abs(int(input("How many tiles high should the map be? ")))) # Height of the map to generate. Maximum is 57
except ValueError:
    print("Input must be single integer")
    exit(1)

START = (3,3) # Coordinate of the top-left corner in the output space
MAJOR_NAMES = ["Bombs", "Power Grip", "Spider Ball", "Spring Ball", "Hi-Jump", "Varia Suit", "Space Jump", "Speedbooster", "Screw Attack", "Gravity Suit",
                "Charge Beam", "Ice Beam", "Wave Beam", "Spazer", "Plasma Beam", "Flash Shift", "Scan Pulse", "Shotgun Missiles", "Reserve Tank", "Lightning Armor", "Power Spark"]

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
def get_possible_rooms(door_dir: int, depth: int) -> list:
    possible_rooms = [r for r in room_data if (room_weight(r, depth) > 0)]
    idx = 0
    while idx < len(possible_rooms):
        room = possible_rooms[idx]
        is_locked = False
        for lock in room["Lock"]:
            if not lock in possible_lock_states:
                is_locked = True
                break
        if not has_door(room["Layout"], door_dir) or is_locked:
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
    global possible_lock_states, tiles_with_items
    for key in layout:
        tile_pos = tuple(map(int, key.split(",")))
        grid_pos = (draw_begin[0] + tile_pos[0], draw_begin[1] + tile_pos[1])
        tile_data = layout[key]
        grid[grid_pos] = Tile(tile_data[0], tile_data[1], tile_data[2], tile_data[3])
        if tile_data[0] == 2:
            open_connections.append([(grid_pos[0] + 1, grid_pos[1]), 2])
        if tile_data[1] == 2:
            open_connections.append([(grid_pos[0], grid_pos[1] - 1), 3])
        if tile_data[2] == 2:
            open_connections.append([(grid_pos[0] - 1, grid_pos[1]), 0])
        if tile_data[3] == 2:
            open_connections.append([(grid_pos[0], grid_pos[1] + 1), 1])
        items_locks = [l for l in possible_lock_states if l in layout[key][5]]
        chance = uniform(0,1) * int(layout[key][4]) * int(len(possible_majors) > 0) * int(len(items_locks) == len(layout[key][5]))
        if chance >= 0.8:
            major = possible_majors.pop(randint(0, len(possible_majors)-1))
            inv[major] = 1
            possible_lock_states += unlocked_states(major, inv)
            tiles_with_items.append(grid_pos)
            print(f"Placed {MAJOR_NAMES[major]} (ID {major}) in Tile {grid_pos}")
    
    if len(layout) == 1 and (int(has_door(layout, 0)) + int(has_door(layout, 1)) + int(has_door(layout, 2)) + int(has_door(layout, 3)) == 1):
        placed_dead_ends.append(draw_begin)

# Recursively creates branches of rooms until the grid is fully populated or no more room can be placed
def generate(grid, next_tile, door_dir, depth = 0):
    global frames
    frames += 1
    possible_rooms = get_possible_rooms(door_dir, depth)
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


    total_weights: float = 0.0
    for room in possible_rooms:
        total_weights += room_weight(room, depth)
    choice = uniform(0, total_weights)
    room_to_place_idx = 0
    while (choice > 0):
        choice -= room_weight(possible_rooms[room_to_place_idx], depth)
        room_to_place_idx += 1
    room_to_place_idx -= 1
    room_chosen = possible_rooms[room_to_place_idx]
    room_offset_str = possible_connections[room_to_place_idx][randint(0, len(possible_connections[room_to_place_idx])-1)]
    room_offset = tuple(map(int, room_offset_str.split(",")))
    draw_begin = (next_tile[0] - room_offset[0], next_tile[1] - room_offset[1])
    open_connections = []
    draw_room(draw_begin, room_chosen["Layout"], open_connections)
    
    
    for connection in open_connections:
        generate(grid, connection[0], connection[1], depth + 1)

def room_weight(room: dict, depth: int) -> float:
    if depth < room["Scaling Min"]:
        scale_amount = 0.0
    elif depth < room["Scaling Max"] or room["Scaling Max"] == -1:
        scale_amount = depth
    else:
        scale_amount = room["Scaling Max"]
    return room["Weight"] + room["Scaling"] * scale_amount

def unlocked_states(item_id: int, inventory: list) -> list:
    match item_id:
        case 0: #Bombs
            return [0,9,12,13,14,15,16,17,18,19,27,33,35]
        case 2: #Spider ball
            return [9,10,11,12,15,16]
        case 3: #Spring ball
            if inventory[7] == 1:
                return [5]
            else:
                return []
        case 4: #Hi-Jump
            return [12,13,14]
        case 5: #Varia
            return [24]
        case 6: #Space Jump
            space_states = [15,16,17,18,19]
            if inventory[7] == 1:
                space_states.append(6)
            return space_states
        case 7: #Speedbooster
            return [4,5,33,34]
        case 8: #Screw Attack
            return [7]
        case 9: #Gravity
            return [23,25,26]
        case 11: #Ice Beam
            return [29]
        case 12: #Wave Beam
            return [20,21,22]
        case 20: #Power Spark
            return [3,4,5,15,16,17,18]
        case _:
            return []

# Maps an inventory loadout to possible room lock states        
def inventory_to_lock_states(inventory: list) -> list:
    states = []
    for idx in range(len(inventory)):
        is_collected = inventory[idx] == 1
        if not is_collected:
            continue
        states += unlocked_states(idx, inventory)
        
    
    return list(set(states))
            
    
# START OF MAIN PROGRAM
if __name__ == "__main__":
    start_time = time.time()
    #seed(100)

    with open("Test.json", "r") as file:
        room_data = json.load(file)

    success = False
    while not success:
        try:
            frames = 0
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
            inv = [0]*21
            possible_majors = list(range(21))
            possible_majors = [m for m in possible_majors if inv[m] == 0]
            tiles_with_items = []
            possible_lock_states = inventory_to_lock_states(inv)
            generate(grid, next_pos, direction, 0)
            success = True
        except:
            traceback.print_exc()
            print("Rerolling..\n\n\n\n")

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
    placed_dead_ends = [e for e in placed_dead_ends if not e in tiles_with_items]
    try:
        boss_tile = placed_dead_ends[randint(0, len(placed_dead_ends)-1)]
    except:
        print("Error: No dead end for boss placement, not setting boss tile")
        boss_tile = (-1,-1)

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
            if position in tiles_with_items:
                new_tile["special"] = 3
            if position == boss_tile:
                new_tile["special"] = 4
            out.append(new_tile)

    with open("BranchingOutput.json", "w") as file:
        json.dump(out, file, indent=2)

    print(f"Execution time: {(time.time() - start_time)}s")
    print(f"{frames} iterations through generate()")
    print("Done")