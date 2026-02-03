import json
import time
import traceback
from copy import deepcopy
from random import randint, uniform, seed, shuffle
import sys

frames = 0
max_recursion_depth_reached = 0

# Lock bit positions
BOMB_LOCK: int =                                 0b1
MISSILE_LOCK: int =                             0b10
SUPER_MISSILE_LOCK: int =                      0b100
SPEED_LOCK: int =                             0b1000
BALLSPARK_LOCK: int =                        0b10000
SCREW_LOCK: int =                           0b100000
POWER_BOMB_LOCK: int =                     0b1000000
CRUMBLE_BLOCK_LOCK: int =                 0b10000000
CRUMBLE_TUNNEL_LOCK: int =               0b100000000
HIJUMP_WALL_LOCK: int =                 0b1000000000
HIJUMP_PLATFORM_LOCK: int =            0b10000000000
AIRJUMP_LOCK: int =                   0b100000000000
GRAVITY_HAZARD_LOCK: int =           0b1000000000000
VARIA_HAZARD_LOCK: int =            0b10000000000000
MOVE_EMP_BALL_LOCK: int =          0b100000000000000
MOVE_EMP_BALL_WALL_LOCK: int =    0b1000000000000000
MEBOID_BARRIER_LOCK: int =       0b10000000000000000
MULTIPLAYER_LOCK_2P: int =      0b100000000000000000
MULTIPLAYER_LOCK: int =        0b1000000000000000000

UNIQUE_ROOMS = False
START = (3,3) # Coordinate of the top-left corner in the output space
BOSS_KEY: int = 1000
# Names of the Major items. Used for printing item placements
ITEM_NAME_MAPPING = {
    450: "Bombs",
    452: "Spider Ball",
    453: "Spring Ball",
    454: "Hi Jump",
    455: "Varia Suit",
    456: "Space Jump",
    457: "Speed Booster",
    458: "Screw Attack",
    459: "Gravity Suit",
    461: "Ice Beam",
    925: "Missile Tank",
    926: "Super Missile Tank",
    927: "Power Bomb Tank",
    BOSS_KEY: "Master Teleporter Key"
}

# Door directions
RIGHT: int = 0
UP: int = 1
LEFT: int = 2
DOWN: int = 3
BACK: int = 4

# Wall types
NO_WALL: int = 0
WALL: int = 1
DOOR: int = 2

# Data Container class to hold information about a tile in the grid
class Tile:
    def __init__(self, r: int, u: int, l: int, d: int, room_id: int, layout_id: int, bounding_box_offset: tuple):
        self.r = r
        self.u = u
        self.l = l
        self.d = d
        self.room_id = room_id
        self.layout_id = layout_id
        self.bounding_box_offset = bounding_box_offset

class FloorGenerator:
    def __init__(self, width: int, height: int, room_data_file_path: str, start_inventory: list):
        self.width: int = width
        self.height: int = height
        self.room_data: list = []
        self.right_door_rooms: list = []
        self.up_door_rooms: list = []
        self.left_door_rooms: list = []
        self.down_door_rooms: list = []
        self.read_room_data(room_data_file_path)
        self.grid: dict = self.create_grid(width, height)
        self.dead_ends: list = self.get_dead_ends(self.room_data)
        self.placed_dead_ends: list = []
        self.inv: list = start_inventory
        self.possible_majors: list = [m for m in ITEM_NAME_MAPPING.keys() if not m in self.inv and m != BOSS_KEY]
        self.tiles_with_items: list = []
        self.possible_lock_states: int = self.inventory_to_lock_states(self.inv)
        self.start_pos: tuple = (0,0)
        self.layout_id: int = 1
        self.transition_data: dict = {}
        self.placed_doors: list = []
        self.item_data: dict = {}
        self.keys_to_place: int = 0
        self.potential_key_places: set = set()
        self.boss_tile: tuple = None
        self.teleporter_transitions: dict = {}
    
    def read_room_data(self, file_path: str) -> None:
        try:
            with open(file_path, "r") as file:
                full_dict: dict = json.load(file)
            
            self.room_data = full_dict["AllRooms"]
            self.right_door_rooms = full_dict["RightDoorRooms"]
            self.up_door_rooms = full_dict["UpDoorRooms"]
            self.left_door_rooms = full_dict["LeftDoorRooms"]
            self.down_door_rooms = full_dict["DownDoorRooms"]
        except FileNotFoundError:
            print(f"Could not find file '{file_path}'")
            exit(1)

    def first_room(self) -> Tile:
        start_pos = (randint(0, self.width-1), randint(0, self.height-1))
        self.start_pos = start_pos
        if start_pos[0] == 0:
            possible_start_tiles = [Tile(DOOR, WALL, WALL, WALL, 409, 0, (0,0))]
        elif start_pos[0] == self.width-1:
            possible_start_tiles = [Tile(WALL, WALL, DOOR, WALL, 407, 0, (0,0))]
        else:
            possible_start_tiles = [
            Tile(DOOR, WALL, WALL, WALL, 409, 0, (0,0)),
            Tile(WALL, WALL, DOOR, WALL, 407, 0, (0,0)),
        ]

        start_tile = possible_start_tiles[randint(0, len(possible_start_tiles)-1)]
        self.grid[start_pos] = start_tile
        if start_tile.l == DOOR:
            self.placed_doors.append((start_pos, LEFT))
        else:
            self.placed_doors.append((start_pos, RIGHT))

        return (start_pos, start_tile)

    def generate_floor(self, boss_keys: int = 0) -> bool:
        self.keys_to_place = boss_keys
        next_pos = (0,0)
        direction = 0
        start_pos, start_tile = self.first_room()
        if start_tile.r == DOOR:
            next_pos = (start_pos[0] + 1, start_pos[1])
            direction = LEFT
        elif start_tile.l == DOOR:
            next_pos = (start_pos[0] - 1, start_pos[1])
            direction = RIGHT
        else:
            next_pos = start_pos
            direction = 0

        self.generate(self.grid, next_pos, direction, 0)
        correct_keys: bool = self.place_remaining_boss_keys()
        placed_dead_ends = [e for e in self.placed_dead_ends if not e in self.tiles_with_items]
        successful_generation: bool = (len(placed_dead_ends) != 0) and correct_keys
        if not successful_generation:
            return False
        
        self.boss_tile = placed_dead_ends.pop(randint(0, len(placed_dead_ends)-1))
        self.place_dead_end_teleporters(placed_dead_ends)
        return successful_generation

# Returns a dict where coordinate tuples are the key and None is the value
    def create_grid(self, w: int, h: int) -> dict:
        return {(x,y): None for y in range(h) for x in range(w)}

    # Returns a list of all rooms with only 1 door
    def get_dead_ends(self, data: list) -> list:
        return [r for r in data if r["IsDeadEnd"]]

    # Returns true if the room has a door that points in the direction of door_dir. door_dir is an index into the layout tile's data
    def has_door(self, door_tiles_arr: list, door_dir: int) -> bool:
        return len(door_tiles_arr[door_dir]) > 0

    # Returns a list of rooms filtered by their probability (weight) and if they have a door in the direction given
    def get_possible_rooms(self, door_dir: int, depth: int) -> list:
        if door_dir == RIGHT:
            examine_list = self.right_door_rooms
        elif door_dir == UP:
            examine_list = self.up_door_rooms
        elif door_dir == LEFT:
            examine_list = self.left_door_rooms
        elif door_dir == DOWN:
            examine_list = self.down_door_rooms
        # Remove rooms from consideration if the room has a weight of 0
        possible_rooms = [r for r in examine_list if (self.room_weight(self.room_data[r], depth) > 0)]
        possible_rooms = list(map(lambda x: self.room_data[x], possible_rooms))
        idx = 0
        while idx < len(possible_rooms):
            room = possible_rooms[idx]
            # Check if the player needs specific items to traverse the room
            is_locked = not self.is_location_open(room["Lock"])
            # Remove room from possibilities if it does not have a door in the correct direction or if it is locked behind an item
            if is_locked:
                del possible_rooms[idx]
                continue
            else:
                idx += 1
        
        return possible_rooms


    # Returns a list of local coordinate keys with tiles that have doors in the given door direction
    def start_positions(self, layout: dict, door_dir: int) -> list:
        return [k for k in layout if layout[k][door_dir] == DOOR]

    # Bounding box is [origin_x, origin_y, size_x, size_y]
    def is_bounding_box_inside(self, origin_x: int, origin_y: int, size_x: int, size_y: int) -> bool:
        return origin_x >= 0 and origin_y >= 0 and (origin_x + size_x) < self.width and (origin_y + size_y) < self.height

    # Checks if a room can go next to another room
    def validate_room_position(self, grid: dict, global_start_pos: tuple, relative_key: str, room: dict) -> bool:
        layout = room["Layout"]
        bounding_box = room["BoundingBox"]
        # Convert the key in the layout dict to a coordinate tuple
        relative_door_position = tuple(map(int, relative_key.split(",")))
        # The position where the room's relative origin tile is located globally
        draw_begin = (global_start_pos[0] - relative_door_position[0], global_start_pos[1] - relative_door_position[1])
        if not self.is_bounding_box_inside(draw_begin[0] + bounding_box[0], draw_begin[1] + bounding_box[1], bounding_box[2], bounding_box[3]):
            return False
        
        for key in layout:
            # Convert tile's relative offset into global position
            relative_tile_pos = tuple(map(int, key.split(",")))
            global_tile_pos = (draw_begin[0] + relative_tile_pos[0], draw_begin[1] + relative_tile_pos[1])
            # Room is invalid if it has tile out of bounds or if it overlaps another room or if it's on the edge and has a transition pointing out of bounds
            if grid[global_tile_pos] != None or\
                (global_tile_pos[0] == 0 and layout[key][LEFT] == DOOR) or (global_tile_pos[0] == self.width-1 and layout[key][RIGHT] == DOOR) or\
                (global_tile_pos[1] == 0 and layout[key][UP] == DOOR) or (global_tile_pos[1] == self.height-1 and layout[key][DOWN] == DOOR):
                return False
        
            right_pos = (global_tile_pos[0] + 1, global_tile_pos[1])
            top_pos = (global_tile_pos[0], global_tile_pos[1] - 1)
            left_pos = (global_tile_pos[0] - 1, global_tile_pos[1])
            bottom_pos = (global_tile_pos[0], global_tile_pos[1] + 1)

            # Invalidate rooms if they have a transition into a wall
            if ((right_pos[0] >= self.width or (grid[right_pos] and grid[right_pos].l == WALL)) and layout[key][RIGHT] == DOOR)\
                or ((top_pos[1] < 0 or (grid[top_pos] and grid[top_pos].d == WALL)) and layout[key][UP] == DOOR)\
                or ((left_pos[0] < 0 or (grid[left_pos] and grid[left_pos].r == WALL)) and layout[key][LEFT] == DOOR)\
                or ((bottom_pos[1] >= self.height or (grid[bottom_pos] and grid[bottom_pos].u == WALL)) and layout[key][DOWN] == DOOR):
                return False

            if right_pos[0] < self.width:
                if (grid[right_pos] and grid[right_pos].l == DOOR) and layout[key][RIGHT] == WALL:
                    return False
            if top_pos[1] > 0:
                if (grid[top_pos] and grid[top_pos].d == DOOR) and layout[key][UP] == WALL:
                    return False
            if left_pos[0] > 0:
                if (grid[left_pos] and grid[left_pos].r == DOOR) and layout[key][LEFT] == WALL:
                    return False
            if bottom_pos[1] < self.height:
                if (grid[bottom_pos] and grid[bottom_pos].u == DOOR) and layout[key][DOWN] == WALL:
                    return False

        return True

    def place_item(self, item_id: int, layout_id: int, bounding_box_offset: tuple, grid_pos: tuple) -> None:
        debug_message: str = f"Placed {ITEM_NAME_MAPPING[item_id]} (ID {item_id}) in Tile {grid_pos}"
        if (item_id != BOSS_KEY):
            self.inv.append(item_id)
            # Consider the item to be collected for the rest of the generation
            self.possible_lock_states = self.inventory_to_lock_states(self.inv)
        else:
            debug_message += f". {self.keys_to_place} Keys remaining."
        self.tiles_with_items.append(grid_pos)
        item_key: str = f"{layout_id}_{bounding_box_offset[0]}_{bounding_box_offset[1]}"
        self.item_data[item_key] = item_id
        print(debug_message)

    # Writes the tile data into the grid
    def draw_room(self, draw_begin: tuple, room: dict, open_connections: list):
        layout = room["Layout"]
        bounding_box_origin = (room["BoundingBox"][0], room["BoundingBox"][1])
        placed_key_item: bool = False
        for key in layout:
            tile_pos = tuple(map(int, key.split(",")))
            bounding_box_offset = (tile_pos[0] - bounding_box_origin[0], tile_pos[1] - bounding_box_origin[1])
            grid_pos = (draw_begin[0] + tile_pos[0], draw_begin[1] + tile_pos[1])
            tile_data = layout[key]
            self.grid[grid_pos] = Tile(tile_data[0], tile_data[1], tile_data[2], tile_data[3], room["RoomID"], self.layout_id, bounding_box_offset)
            if tile_data[RIGHT] == DOOR:
                self.placed_doors.append((grid_pos, RIGHT))
                if not self.grid[(grid_pos[0] + 1, grid_pos[1])]:
                    open_connections.append([(grid_pos[0] + 1, grid_pos[1]), LEFT])
            if tile_data[UP] == DOOR:
                self.placed_doors.append((grid_pos, UP))
                if not self.grid[(grid_pos[0], grid_pos[1] - 1)]:
                    open_connections.append([(grid_pos[0], grid_pos[1] - 1), DOWN])
            if tile_data[LEFT] == DOOR:
                self.placed_doors.append((grid_pos, LEFT))
                if not self.grid[(grid_pos[0] - 1, grid_pos[1])]:
                    open_connections.append([(grid_pos[0] - 1, grid_pos[1]), RIGHT])
            if tile_data[DOWN] == DOOR:
                self.placed_doors.append((grid_pos, DOWN))
                if not self.grid[(grid_pos[0], grid_pos[1] + 1)]:
                    open_connections.append([(grid_pos[0], grid_pos[1] + 1), UP])
            # Chance to place an item onto the tile. If the tile can't have an item or if it can hold an item but the location is locked
            # or there are no more major items to place, chance will be 0
            can_tile_have_item: bool = layout[key][4]
            locks_unlocked: bool = self.is_location_open(layout[key][5]) # Check if item location locks are a subset of opened locks
            chance = uniform(0,1) * int(can_tile_have_item) * int(locks_unlocked)
            if chance >= 0.9 and (len(self.possible_majors) > 0):
                # Select a random major item to be placed at the tile
                major = self.possible_majors.pop(randint(0, len(self.possible_majors)-1))
                self.place_item(major, self.layout_id, bounding_box_offset, grid_pos)
                placed_key_item = True
            # elif chance >= 0.8 and self.keys_to_place > 0:
            #     # Place a boss key at the tile
            #     self.keys_to_place -= 1
            #     self.place_item(BOSS_KEY, self.layout_id, bounding_box_offset, grid_pos)
            #     placed_key_item = True
            elif self.keys_to_place > 0 and can_tile_have_item and locks_unlocked:
                # No item or key was placed
                tile_info: tuple = (self.layout_id, bounding_box_offset[0], bounding_box_offset[1], grid_pos)
                self.potential_key_places.add(tile_info)
        
        # Mark the room as a single tile big dead end if it is one for boss placement later
        if (len(layout)) == 1:
            pass
        if len(layout) == 1 and (int(self.has_door(room["DoorTiles"], RIGHT)) + int(self.has_door(room["DoorTiles"], UP)) + int(self.has_door(room["DoorTiles"], LEFT)) + int(self.has_door(room["DoorTiles"], DOWN)) == 1) and not placed_key_item:
            self.placed_dead_ends.append(draw_begin)
        
        self.layout_id += 1

    # Recursively creates branches of rooms until the grid is fully populated or no more room can be placed
    def generate(self, grid: dict, next_tile: tuple, door_dir: int, depth: int = 0):
        global frames, max_recursion_depth_reached
        open_connections = [[next_tile, door_dir]]
        open_depths = [depth]
        while len(open_connections) > 0:
            frames += 1
            current_connection = open_connections.pop(0)
            next_tile = current_connection[0]
            door_dir = current_connection[1]
            depth = open_depths.pop(0)
            max_recursion_depth_reached = max(max_recursion_depth_reached, depth)
            possible_rooms = self.get_possible_rooms(door_dir, depth)
            possible_connections = []

            for room in possible_rooms:
                connection_points = room["DoorTiles"][door_dir]
                # Iterate over every transition in the room. If the transition fits next to the one we are at and the room is valid, add it to the possibilities
                allowed_connections = []
                for connection in connection_points:
                    if self.validate_room_position(grid, next_tile, connection, room):
                        allowed_connections.append(connection)
                possible_connections.append(allowed_connections)
            
            possible_rooms = [r for r in possible_rooms if len(possible_connections[possible_rooms.index(r)]) > 0]
            possible_connections = [c for c in possible_connections if len(c) > 0]
            # If no room fits, try fitting a dead end next to it to complete the branch
            if len(possible_rooms) == 0:
                if grid[next_tile]:
                    continue
                ends = [e for e in self.dead_ends if self.has_door(e["DoorTiles"], door_dir)]
                valid_connections = []
                for e in ends:
                    end_connections = []
                    entrances = e["DoorTiles"][door_dir]
                    for connection in entrances:
                        if self.validate_room_position(grid, next_tile, connection, e):
                            end_connections.append(connection)
                    valid_connections.append(end_connections)
                
                ends = [e for e in ends if len(valid_connections[ends.index(e)]) > 0]
                valid_connections = [c for c in valid_connections if len(c) > 0]
                end_to_place_idx = randint(0, len(ends)-1) if len(ends) >= 1 else 0
                end_chosen = ends[end_to_place_idx]
                end_offset_str = valid_connections[end_to_place_idx][randint(0, len(valid_connections[end_to_place_idx])-1)]
                end_offset = tuple(map(int, end_offset_str.split(",")))
                draw_begin = (next_tile[0] - end_offset[0], next_tile[1] - end_offset[1])
                self.draw_room(draw_begin, end_chosen, [])
            else:
                # Choose a random room from the list of possible rooms considering their respective weights
                total_weights: float = 0.0
                for room in possible_rooms:
                    total_weights += self.room_weight(room, depth)
                choice = uniform(0, total_weights)
                room_to_place_idx = 0
                while (choice > 0):
                    choice -= self.room_weight(possible_rooms[room_to_place_idx], depth)
                    room_to_place_idx += 1
                room_to_place_idx -= 1
                room_chosen = possible_rooms[room_to_place_idx]
                room_offset_str = possible_connections[room_to_place_idx][randint(0, len(possible_connections[room_to_place_idx])-1)]
                room_offset = tuple(map(int, room_offset_str.split(",")))
                draw_begin = (next_tile[0] - room_offset[0], next_tile[1] - room_offset[1])
                new_connections = []
                # Place the room in the grid
                self.draw_room(draw_begin, room_chosen, new_connections)

                # If the setting UNIQUE_ROOMS is on, prevent the room from ever being placed again in this generation
                if UNIQUE_ROOMS and not room_chosen in self.dead_ends:
                    room_chosen["Scaling"] = 0
                    room_chosen["Weight"] = 0
                
                # Repeat the same function for every transition without corresponding connection
                open_connections = new_connections + open_connections
                open_depths = [depth+1]*len(new_connections) + open_depths

    def move_pos_in_direction(self, pos: tuple, direction: int, units: int = 1) -> tuple:
        if direction == RIGHT:
            return (pos[0] + units, pos[1])
        elif direction == UP:
            return (pos[0], pos[1] - units)
        elif direction == LEFT:
            return (pos[0] - units, pos[1])
        elif direction == DOWN:
            return (pos[0], pos[1] + units)
        else:
            return pos

    # Calculates the weight of the room, scaling with distance (in rooms) to the start location
    def room_weight(self, room: dict, depth: int) -> float:
        if depth < room["Scaling Min"]:
            scale_amount = 0.0
        elif depth < room["Scaling Max"] or room["Scaling Max"] == -1:
            scale_amount = depth
        else:
            scale_amount = room["Scaling Max"]
        return room["Weight"] + room["Scaling"] * scale_amount

    # Returns list of item lock states that are unlocked by item_id
    def unlocked_states(self, item_id: int, inventory: list) -> int:
        match item_id:
            case 450: #Bombs
                return (BOMB_LOCK | MOVE_EMP_BALL_LOCK)
            case 452: #Spider ball
                return (CRUMBLE_BLOCK_LOCK | CRUMBLE_TUNNEL_LOCK | HIJUMP_WALL_LOCK)
            case 453: #Spring ball
                if 457 in inventory: # If speedbooster in inventory
                    return BALLSPARK_LOCK
                else:
                    return 0
            case 454: #Hi-Jump
                return (HIJUMP_WALL_LOCK | HIJUMP_PLATFORM_LOCK)
            case 455: #Varia
                return VARIA_HAZARD_LOCK
            case 456: #Space Jump
                return (HIJUMP_WALL_LOCK | HIJUMP_PLATFORM_LOCK | AIRJUMP_LOCK)
            case 457: #Speedbooster
                return SPEED_LOCK
            case 458: #Screw Attack
                return SCREW_LOCK
            case 459: #Gravity
                return GRAVITY_HAZARD_LOCK
            case 461: #Ice Beam
                return MEBOID_BARRIER_LOCK
            case 925: #Missile Tank
                return (MISSILE_LOCK | MOVE_EMP_BALL_LOCK | MOVE_EMP_BALL_WALL_LOCK)
            case 926: #Super Missile Tank
                return (MISSILE_LOCK | SUPER_MISSILE_LOCK | MOVE_EMP_BALL_LOCK | MOVE_EMP_BALL_WALL_LOCK)
            case 927: #Power Bomb Tank
                return (BOMB_LOCK | POWER_BOMB_LOCK)
            case _:
                return 0

    # Maps an inventory loadout to possible room lock states        
    def inventory_to_lock_states(self, inventory: list) -> int:
        states = 0
        for unlocked_item_id in inventory:
            states |= self.unlocked_states(unlocked_item_id, inventory)
        
        return states
    
    def is_location_open(self, locks: list) -> bool:
        if len(locks) == 0: return True
        return any(((self.possible_lock_states & lock) == lock) for lock in locks)

    def get_room_and_transition_data(self) -> dict:
        transition_data = {}
        room_data = []

        for grid_coord, direction in self.placed_doors:
            tile: Tile = self.grid[grid_coord]
            outer_key: str = str(tile.layout_id)
            inner_key: str = f"{tile.bounding_box_offset[0]}_{tile.bounding_box_offset[1]}_{direction}"
            target_tile_coord: tuple = self.move_pos_in_direction(grid_coord, direction)
            target_tile: Tile = self.grid[target_tile_coord]
            value: list = [target_tile.layout_id, target_tile.bounding_box_offset[0], target_tile.bounding_box_offset[1]]

            if not outer_key in transition_data:
                transition_data[outer_key] = {}
            transition_data[outer_key][inner_key] = value

            if tile.layout_id >= len(room_data):
                global_bounding_box_coords = (grid_coord[0] - tile.bounding_box_offset[0], grid_coord[1] - tile.bounding_box_offset[1])
                room_data.append([tile.room_id, global_bounding_box_coords[0], global_bounding_box_coords[1]])

        for dead_end in self.teleporter_transitions:
            tile_at_coord: Tile = self.grid[dead_end]
            outer_key: str = str(tile_at_coord.layout_id)
            inner_key: str = f"{tile_at_coord.bounding_box_offset[0]}_{tile_at_coord.bounding_box_offset[1]}_{BACK}"
            target_tile: Tile = self.grid[self.teleporter_transitions[dead_end]]
            value: list = [target_tile.layout_id, target_tile.bounding_box_offset[0], target_tile.bounding_box_offset[1]]

            if not outer_key in transition_data:
                transition_data[outer_key] = {}
            transition_data[outer_key][inner_key] = value

            # Way back
            outer_key: str = str(target_tile.layout_id)
            inner_key: str = f"{target_tile.bounding_box_offset[0]}_{target_tile.bounding_box_offset[1]}_{BACK}"
            value: list = [tile_at_coord.layout_id, tile_at_coord.bounding_box_offset[0], tile_at_coord.bounding_box_offset[1]]

            if not outer_key in transition_data:
                transition_data[outer_key] = {}
            transition_data[outer_key][inner_key] = value

        room_data.insert(0, [])
        return transition_data, room_data
    
    def place_remaining_boss_keys(self) -> bool:
        if self.keys_to_place == 0: return True # Already placed all keys
        remaining_places = list(self.potential_key_places)
        shuffle(remaining_places)
        while self.keys_to_place > 0 and len(remaining_places) > 0:
            item_tile: tuple = remaining_places.pop(0)
            bb_offset: tuple = (item_tile[1], item_tile[2])
            self.keys_to_place -= 1
            self.place_item(BOSS_KEY, item_tile[0], bb_offset, item_tile[3])
        
        return (self.keys_to_place <= 0)
    
    def place_dead_end_teleporters(self, dead_ends: list) -> None:
        TELEPORT_CHANCE: float = 0.50
        while len(dead_ends) >= 2:
            examine_end: tuple = dead_ends.pop(0)
            furthest_dist: float = 0
            closest_end_idx: int = 0
            for i in range(len(dead_ends)):
                other_end: tuple = dead_ends[i]
                dist: float = abs(examine_end[0] - other_end[0]) + abs(examine_end[1] - other_end[1])
                if dist > furthest_dist:
                    closest_end_idx = i
                    furthest_dist = dist
            other_end: tuple = dead_ends.pop(closest_end_idx)
            if uniform(0.0,1.0) < TELEPORT_CHANCE:
                self.teleporter_transitions[examine_end] = other_end
                print(f"Connected Dead-End at {examine_end} and {other_end} with a Teleporter")
            
    
# START OF MAIN PROGRAM
if __name__ == "__main__":
    try:
        WIDTH = min(74, abs(int(input("How many tiles wide should the map be? ")))) # Width of the map to generate. Maximum is 74
        HEIGHT = min(57, abs(int(input("How many tiles high should the map be? ")))) # Height of the map to generate. Maximum is 57
    except ValueError:
        print("Input must be single integer")
        exit(1)
    start_time = time.time()
    if len(sys.argv) > 1:
        try:
            seed(int(sys.argv[1]))
        except ValueError:
            print(f"Cannot convert '{sys.argv[1]}' to int, using random seed")
        except IndexError:
            print(f"No seed given, generating with random seed")


    # If we broke out of the generation because of an Exception, repeat until we got a valid floor
    success = False
    KEYS_TO_PLACE: int = int(round(WIDTH/4 - 1))
    while not success:
        frames = 0
        max_recursion_depth_reached = 0
        generator = FloorGenerator(WIDTH, HEIGHT, "RoomSets/A2_RoomSet.json", [])
        try:
            success = generator.generate_floor(KEYS_TO_PLACE)
        except KeyboardInterrupt:
            exit(1)
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

    map_init_strings = [WIDTH, HEIGHT]
    out = []
    try:
        boss_tile = generator.boss_tile
    except:
        print("Error: No dead end for boss placement, not setting boss tile")
        boss_tile = (-1,-1)

    transition_data, room_data = generator.get_room_and_transition_data()
    tiles_with_teleporters = list(generator.teleporter_transitions.keys()) + list(generator.teleporter_transitions.values())
    grid = generator.grid
    for position in grid:
        if grid[position] != None:
            map_string = f"{grid[position].u}{grid[position].r}{grid[position].d}{grid[position].l}1"
            new_tile = deepcopy(prototype_tile)
            new_tile["wallL"] = grid[position].l
            new_tile["wallU"] = grid[position].u
            new_tile["wallD"] = grid[position].d
            new_tile["wallR"] = grid[position].r
            new_tile["x"] = position[0] + START[0]
            new_tile["y"] = position[1] + START[1]
            if position == generator.start_pos:
                new_tile["special"] = 1
                map_string += "1"
            elif position in generator.tiles_with_items:
                new_tile["special"] = 3
                map_string += "3"
            elif position in tiles_with_teleporters:
                new_tile["color"] = 1
                new_tile["special"] = 7
                map_string = f"{grid[position].u}{grid[position].r}{grid[position].d}{grid[position].l}2"
                map_string += "7"
            elif position == boss_tile:
                new_tile["special"] = 4
                # Set tile color to purple
                new_tile["color"] = 3
                map_string = f"{grid[position].u}{grid[position].r}{grid[position].d}{grid[position].l}4"
                map_string += "4"
            else:
                map_string += "0"
            map_string += "0"
            assert len(map_string) == 7
            out.append(new_tile)
            map_init_strings.append(map_string)
        else:
            map_init_strings.append("0")

    package = {
        "RoomData": room_data,
        "TransitionData": transition_data,
        "MapData": map_init_strings,
        "ItemData": generator.item_data,
        "BossData": grid[boss_tile].layout_id
    }

    with open("PackageTest.json", "w") as file:
        json.dump(package, file)

    with open("BranchingOutput.json", "w") as file:
        json.dump(out, file, indent=2)

    # with open("MapDataTest.json", "w") as file:
    #     json.dump(map_init_strings, file)
    
    # with open("TransitionDataTest.json", "w") as file:
    #     json.dump(transition_data, file, indent=2)

    print(f"Execution time: {(time.time() - start_time)}s")
    print(f"{frames} iterations through generate()")
    print(f"Maximum Recursion Depth reached: {max_recursion_depth_reached}")
    print("Done")