import json
import sys
from copy import deepcopy

START = (3,3)

try:
    with open(sys.argv[1]) as file:
        generation_data = json.load(file)
except IndexError:
    print("No input file provided")
    exit(1)
except FileNotFoundError as e:
    print(e)
    exit(1)


map_data = generation_data["MapData"]
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

width = map_data[0] + START[0]
height = map_data[1] + START[1]
i = 2
x = START[0]
y = START[0]

formatted_data_out = []

while (i < len(map_data)):
    map_string = map_data[i]
    if map_string == "0":
        map_string = "0"*7
    tile_info = deepcopy(prototype_tile)
    tile_info["wallU"] = int(map_string[0])
    tile_info["wallR"] = int(map_string[1])
    tile_info["wallD"] = int(map_string[2])
    tile_info["wallL"] = int(map_string[3])
    tile_info["color"] = int(map_string[4]) - 1
    tile_info["special"] = int(map_string[5])
    tile_info["x"] = x
    tile_info["y"] = y
    formatted_data_out.append(tile_info)
    x += 1
    if x >= width:
        x = START[0]
        y += 1
    i += 1

with open("ReconstructedMapData.json", "w") as out_file:
    json.dump(formatted_data_out, out_file, indent=2)

print("Wrote formatted data")