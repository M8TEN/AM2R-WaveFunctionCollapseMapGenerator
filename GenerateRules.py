import json

'''This code expects the data format the AM2R Mapping Tool uses in a JSON file as input to
   perform the rule generation'''

DOORS = ["wallR", "wallU", "wallL", "wallD"] # Keys into the tile dicts

with open("Inputs/Tile_Varients.json", "r") as file:
    tile_data = json.load(file)

rules = [] # List of all rules for every tile

for tile in tile_data:
    current_rule = [[], [], [], []] # The current tile. Each inner list represents the possible other tiles for the given direction
    for t in range(len(tile_data)): # Use 't' as the index into the tile array so we only store the index reference
        for i in range(len(DOORS)):
            door_dir = DOORS[i]
            opposite = DOORS[(i + 2) % len(DOORS)]
            other = tile_data[t]
            # If the current tile has a door to a direction and the other tile has a door in the opposite direction, they can go next to each other
            if tile[door_dir] == other[opposite]:
                current_rule[i].append(t)
    rules.append(current_rule)

with open("Inputs/Ruleset.json", "w") as file:
    json.dump(rules, file, indent=2)