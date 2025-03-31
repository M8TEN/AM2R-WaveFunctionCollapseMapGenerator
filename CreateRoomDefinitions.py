import json
from functools import reduce
from GroupTiles import create_tile_pos_dict, find_group

def top_left_corner(room: list) -> tuple:
    origin_tile = room[0]
    origin_pos = (origin_tile["x"], origin_tile["y"])
    for tile in room:
        tile_pos = (tile["x"], tile["y"])
        if tile_pos[1] < origin_pos[1] or (tile_pos[1] == origin_pos[1] and tile_pos[0] < origin_pos[0]):
            origin_tile = tile
            origin_pos = tile_pos
    return origin_pos

with open("Inputs/ThisMightBreak.json", "r") as file:
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

out = []
room_idx = 0

for room in rooms:
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
    num_of_doors = 0
    for tile in room:
        key = f"{tile['x']-top_left[0]},{tile['y']-top_left[1]}"
        value = [tile["wallR"], tile["wallU"], tile["wallL"], tile["wallD"], False, []]
        if tile["wallR"] == 2:
            num_of_doors += 1
        if tile["wallU"] == 2:
            num_of_doors += 1
        if tile["wallL"] == 2:
            num_of_doors += 1
        if tile["wallD"] == 2:
            num_of_doors += 1
        layout[key] = value
    room_as_dict["Layout"] = layout
    room_as_dict["IsDeadEnd"] = num_of_doors <= 1
    room_as_dict["Weight"] = 0 if (num_of_doors <= 1) else 1
    out.append(room_as_dict)
    room_idx += 1

with open("Test.json", "w") as file:
    json.dump(out, file, indent=2)