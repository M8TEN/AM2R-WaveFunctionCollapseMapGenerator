import json
from math import inf
from GroupTiles import create_tile_pos_dict, find_group

RIGHT = 0
UP = 1
LEFT = 2
DOWN = 3

def top_left_corner(room: list) -> tuple:
    origin_tile = room[0]
    origin_pos = (origin_tile["x"], origin_tile["y"])
    for tile in room:
        tile_pos = (tile["x"], tile["y"])
        if tile_pos[1] < origin_pos[1] or (tile_pos[1] == origin_pos[1] and tile_pos[0] < origin_pos[0]):
            origin_tile = tile
            origin_pos = tile_pos
    return origin_pos

with open("Inputs/EL_Test.json", "r") as file:
    tile_data = json.load(file)

tile_pos_dict = create_tile_pos_dict(tile_data)
rooms = []

while len(tile_data) > 0:
    new_room = []
    checked = []
    find_group(new_room, tile_data[0], checked, tile_pos_dict, 0)
    rooms.append(new_room)
    tile_data = [t for t in tile_data if not t in new_room]

print(f"Found {len(rooms)} rooms")

out = {
    "AllRooms": [],
    "RightDoorRooms": set(),
    "UpDoorRooms": set(),
    "LeftDoorRooms": set(),
    "DownDoorRooms": set()
    }
num_of_tiles = 0
room_idx = 395

for i in range(len(rooms)):
    room = rooms[i]
    room_as_dict = {
        "RoomID": room_idx,
        "Lock": [],
        "Weight": 1,
        "Scaling": 0,
        "Scaling Min": 4,
        "Scaling Max": -1
    }
    top_left: tuple = top_left_corner(room)
    layout = {}
    door_tiles = [[], [], [], []]
    num_of_doors = 0
    min_x = inf
    max_x = -inf
    min_y = inf
    max_y = -inf
    for tile in room:
        num_of_tiles += 1
        tile_x = tile['x']-top_left[0]
        tile_y = tile['y']-top_left[1]
        min_x = min(min_x, tile_x)
        max_x = max(max_x, tile_x)
        min_y = min(min_y, tile_y)
        max_y = max(max_y, tile_y)
        key = f"{tile_x},{tile_y}"
        value = [tile["wallR"], tile["wallU"], tile["wallL"], tile["wallD"], (tile["special"] == 3 or tile["special"] == 4), []]
        if tile["wallR"] == 2:
            out["RightDoorRooms"].add(i)
            door_tiles[RIGHT].append(key)
            num_of_doors += 1
        if tile["wallU"] == 2:
            out["UpDoorRooms"].add(i)
            door_tiles[UP].append(key)
            num_of_doors += 1
        if tile["wallL"] == 2:
            out["LeftDoorRooms"].add(i)
            door_tiles[LEFT].append(key)
            num_of_doors += 1
        if tile["wallD"] == 2:
            out["DownDoorRooms"].add(i)
            door_tiles[DOWN].append(key)
            num_of_doors += 1
        layout[key] = value
    room_as_dict["Layout"] = layout
    room_as_dict["DoorTiles"] = door_tiles
    room_as_dict["BoundingBox"] = [int(min_x), int(min_y), int(abs(max_x-min_x)), int(abs(max_y-min_y))]
    room_as_dict["IsDeadEnd"] = num_of_doors <= 1
    room_as_dict["Weight"] = 0 if (num_of_doors <= 1) else 1
    if len(layout) == 1 and num_of_doors > 1:
        room_as_dict["Weight"] = 0.01
    elif num_of_doors <= 1:
        room_as_dict["Scaling"] = 0.015
        room_as_dict["Scaling Max"] = 30
    else:
        room_as_dict["Weight"] *= num_of_doors
    out["AllRooms"].append(room_as_dict)
    room_idx += 1

print(f"Processed {num_of_tiles} tiles")

out["RightDoorRooms"] = list(out["RightDoorRooms"])
out["UpDoorRooms"] = list(out["UpDoorRooms"])
out["LeftDoorRooms"] = list(out["LeftDoorRooms"])
out["DownDoorRooms"] = list(out["DownDoorRooms"])

with open("EL_Sorted_Test.json", "w") as file:
    json.dump(out, file, indent=2)