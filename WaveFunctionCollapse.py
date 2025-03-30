import json
import time
import traceback
from functools import partial
from random import randint, seed
from copy import deepcopy
from Cell import Cell
from GroupTiles import *

START = (3,3) # Coordinate of the top left cell. Is (3,3) because of the AM2R Mapping Tool
DIMENSIONS = 57 # Length of the map square to generate in in tiles. Mapping Tool can handle up to 57
EMPTY_CELL = 15 # Index of the 'empty' tile. Tiles with this index will not be written to the final output
MAX_DEPTH = 10 # Maximum Recursion depth for reducing possibilities in cells

# Custom Exception in case the algorithm stumbles across a tile with no option left
class OptionConflict(Exception):
    def __init__(self, message):
        super().__init__(message)

# Since the List of all tiles is 1 dimensional, convert from 2D coordinate to 1D list index
def pos_to_index(pos):
    return pos[0] + pos[1] * DIMENSIONS

# Locks a cell into a single option for the rest of the algorithm
def collapse_cell(cell):
    cell.collapsed = True
    cell.options = [cell.options[randint(0, len(cell.options)-1)]]

# Main function containing the algorithm. Keeps going until every cell is collapsed
def wfc(grid, rules):
    wfc_runs = 0 # Only relevant for printing purposes
    '''Every iteration, we pull the cells from the grid that are not marked as collapsed,
       sort them and pick the one with the lowest entropy, then collapse it and propagate
       the consequences of that through the neighboring cells'''
    non_collapsed = [c for c in grid if not c.collapsed]
    while len(non_collapsed) > 0:
        wfc_runs += 1
        print(f"{wfc_runs} passes through WFC Loop", end="\r")
        for cell in non_collapsed:
            cell.calculate_entropy()
        
        non_collapsed = sorted(non_collapsed, key=lambda a: a.entropy)
        next_cell = non_collapsed[0]
        if len(next_cell.options) == 0:
            raise OptionConflict(f"Cell at {next_cell.position} has no option")
        collapse_cell(next_cell)
        reduce_options(grid, next_cell, rules, [])
        non_collapsed = [c for c in grid if not c.collapsed]
    print("")

# Recursive funtion to reduce the possible options for every tile
def reduce_options(grid, collapsed_cell, rules, checked_cells, depth=0):
    if depth >= MAX_DEPTH or collapsed_cell in checked_cells:
        return
    middle = collapsed_cell.position
    '''We go right, left, up and down from the cell we just reduced to the neighbor cell
       where we reduce the options further and repeat recursively until we hit MAX_DEPTH or
       until we hit a cell that was already checked.
       If blocks make sure we don't try reducing cells outside of the grid'''
    if middle[0] + 1 < DIMENSIONS:
        right_cell = grid[pos_to_index((middle[0]+1, middle[1]))]
        # Bind the relevant parameters to valid_options so we can use the built-in filter function
        bound = partial(valid_options, collapsed_cell, rules, 0)
        right_cell.options = list(filter(bound, right_cell.options))
        checked_cells.append(right_cell)
        reduce_options(grid, right_cell, rules, checked_cells, depth+1)
    if middle[0] - 1 >= 0:
        left_cell = grid[pos_to_index((middle[0]-1, middle[1]))]
        # Bind the relevant parameters to valid_options so we can use the built-in filter function
        bound = partial(valid_options, collapsed_cell, rules, 2)
        left_cell.options = list(filter(bound, left_cell.options))
        checked_cells.append(left_cell)
        reduce_options(grid, left_cell, rules, checked_cells, depth+1)
    if middle[1] - 1 >= 0:
        top_cell = grid[pos_to_index((middle[0], middle[1]-1))]
        # Bind the relevant parameters to valid_options so we can use the built-in filter function
        bound = partial(valid_options, collapsed_cell, rules, 1)
        top_cell.options = list(filter(bound, top_cell.options))
        checked_cells.append(top_cell)
        reduce_options(grid, top_cell, rules, checked_cells, depth+1)
    if middle[1] + 1 < DIMENSIONS:
        bottom_cell = grid[pos_to_index((middle[0], middle[1]+1))]
        # Bind the relevant parameters to valid_options so we can use the built-in filter function
        bound = partial(valid_options, collapsed_cell, rules, 3)
        bottom_cell.options = list(filter(bound, bottom_cell.options))
        checked_cells.append(bottom_cell)
        reduce_options(grid, bottom_cell, rules, checked_cells, depth+1)

# An option is valid if it can go next to any other possibility of the reduced cell
def valid_options(reduced_cell, rules, direction, option):
    for o in reduced_cell.options:
        if not option in rules[o][direction]:
            return False
    
    return True

# Debug function to print the entire grid every iteration step of wfc. Drastically diminished performance when called every iteration.
def show_grid(grid):
    printed_cells = 0
    for c in grid:
        if printed_cells == DIMENSIONS-1:
            print(f"{str(c.options):<8}", end="\n")
            printed_cells = 0
        else:
            print(f"{str(c.options):<8}", end=" ")
            printed_cells += 1
    print("")


# START OF MAIN PROGRAM
start_time = time.time() # Store the time we started with the code's execution
# seed(100) (Optionally set the seed of the random module to a set seed for debugging)

# Read in all possible tile combinations
with open("Inputs/Tile_Varients.json", "r") as file:
    all_tiles = json.load(file) # List containing all Tile Dicts

# Read in all rules for every tile, generated beforehand in GenerateRules.py
with open("Inputs/Ruleset.json", "r") as file:
    rules = json.load(file) # List containing lists of all rules for every tile

original_grid = []

# Populate the grid with cells that have every option available to them
for y in range(DIMENSIONS):
    for x in range(DIMENSIONS):
        cell = Cell((x,y), len(all_tiles))
        original_grid.append(cell)

# Define which tiles can NOT go on the outer edges of our map square
impossible_left = []
impossible_right = []
impossible_top = []
impossible_bottom = []

for t in range(len(all_tiles)):
    tile = all_tiles[t]
    if tile["wallL"] == 2:
        impossible_left.append(t)
    if tile["wallR"] == 2:
        impossible_right.append(t)
    if tile["wallU"] == 2:
        impossible_top.append(t)
    if tile["wallD"] == 2:
        impossible_bottom.append(t)

# Clear the edge tiles of impossible tiles
for y in range(DIMENSIONS):
    left_cell = original_grid[pos_to_index((0, y))]
    right_cell = original_grid[pos_to_index((DIMENSIONS-1, y))]
    left_cell.options = [o for o in left_cell.options if not o in impossible_left]
    right_cell.options = [o for o in right_cell.options if not o in impossible_right]

for x in range(DIMENSIONS):
    top_cell = original_grid[pos_to_index((x, 0))]
    bottom_cell = original_grid[pos_to_index((x, DIMENSIONS-1))]
    top_cell.options = [o for o in top_cell.options if not o in impossible_top]
    bottom_cell.options = [o for o in bottom_cell.options if not o in impossible_bottom]

grid = original_grid # Might be unnecessary since this only creates a shallow copy

# Pick a random tile to be the spawn for the players
valid_start = False
# Define what tiles are valid for placing the player's spawn in
possible_start_indicies = []
for t in range(len(all_tiles)-1):
    tile = all_tiles [t]
    if tile["wallU"] == 1 and tile["wallD"] == 1:
        possible_start_indicies.append(t)

# Roll a new tile until we have a valid one
while not valid_start:
    start_pos = (randint(0, DIMENSIONS-1), randint(0, DIMENSIONS-1))
    start_cell = grid[pos_to_index(start_pos)]
    overlap = [o for o in start_cell.options if o in possible_start_indicies]
    if len(overlap) > 0:
        valid_start = True
        start_cell.options = overlap

# Collapse the first cell
start_room = start_cell.options[randint(0, len(start_cell.options)-1)]
start_cell.options = [start_room]
start_cell.collapsed = True
reduce_options(grid, start_cell, rules, [])
setup_grid = deepcopy(grid) # Copy the grid after it finished the setup so the setup does not have to repeat in case of an error
# If we run into an error in the generation step, we start from the beginning again, hoping that the error resolved due to the randomness
no_error = False
while not no_error:
    try:
        wfc(grid, rules)
        no_error = True
    except Exception as e:
        traceback.print_exc()
        print("Rerolling...")
        grid = deepcopy(setup_grid)

# Choose a tile in the generated grid that will be marked as containing the boss
boss_tile = (randint(0, DIMENSIONS-1), randint(0, DIMENSIONS-1))
while boss_tile == start_cell.position or not grid[pos_to_index(boss_tile)].options[0] in possible_start_indicies:
    boss_tile = (randint(0, DIMENSIONS-1), randint(0, DIMENSIONS-1))

# Compile tile data into valid JSON format for AM2R Mapping Tool
out_tiles = []
for cell in grid:
    if cell.options[0] == EMPTY_CELL:
        continue
    tile = deepcopy(all_tiles[cell.options[0]])
    if cell == start_cell:
        tile["special"] = 1
    if cell.position == boss_tile:
        tile["color"] = 3
    tile["x"] = START[0] + cell.position[0]
    tile["y"] = START[1] + cell.position[1]
    out_tiles.append(tile)

print(f"Generated {len(out_tiles)} tiles")
print(f"Max Recursion Depth: {MAX_DEPTH}\nExecution time for WFC: {(time.time() - start_time)} s")

'''The WFC implementation in this code does produce valid floor in the sense that every cell in the map
   has only 1 option and that these tiles follow the rules set previously. However, the floors are invalid
   in the sense that it is not guaranteed that a player could reach every tile from every other tile. To fix this,
   we go into what I call the "grouping step". This step will see if self contained areas formed and will connect them
   to form a fully connected map'''

grouping_start_time = time.time() # Store the time at the beginning of the grouping process

# Connect all tiles
tile_pos_dict = create_tile_pos_dict(out_tiles)
connect_areas(tile_pos_dict, out_tiles)

# Print runtime information
print(f"Execution time for grouping step: {(time.time() - grouping_start_time)} s")
print(f"Execution time total: {(time.time() - start_time)} s")

out_path = "GroupedOutput.json"

with open(out_path, "w") as file:
    json.dump(list(tile_pos_dict.values()), file, indent=2)

print(f"Wrote new map to {out_path}")