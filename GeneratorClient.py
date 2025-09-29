import asyncio
import json
import random
import sys
from random import randint
from BranchingGeneratorAsClass import Tile, FloorGenerator

PORT = 64196
exit = False
seed = -1

def generate_package(gen: FloorGenerator) -> dict:
    full_data = {}
    try:
        boss_tile = gen.placed_dead_ends[randint(0, len(gen.placed_dead_ends)-1)]
        boss_tile_obj: Tile = gen.grid[boss_tile]
        if not boss_tile_obj.room_id in [406, 407, 408, 409]:
            if boss_tile_obj.d == 2: # If tile has door down
                boss_tile_obj.room_id = 406
            elif boss_tile_obj.l == 2:
                boss_tile_obj.room_id = 407
            elif boss_tile_obj.u == 2:
                boss_tile_obj.room_id = 408
            elif boss_tile_obj.r == 2:
                boss_tile_obj.room_id = 409
    except:
        print("Error: No dead end for boss placement, not setting boss tile")
        boss_tile = (-1,-1)
    
    transition_data, room_data = gen.get_room_and_transition_data()
    map_init_strings = [gen.width, gen.height]

    for coord in gen.grid:
        if gen.grid[coord] != None:
            map_string = f"{gen.grid[coord].u}{gen.grid[coord].r}{gen.grid[coord].d}{gen.grid[coord].l}1"
            if coord == gen.start_pos:
                map_string += "1"
            elif coord in gen.tiles_with_items:
                map_string += "3"
            elif coord == boss_tile:
                # Set tile color to purple
                map_string = f"{gen.grid[coord].u}{gen.grid[coord].r}{gen.grid[coord].d}{gen.grid[coord].l}4"
                map_string += "4"
            else:
                map_string += "0"
            map_string += "0"
            map_init_strings.append(map_string)
        else:
            map_init_strings.append("0")
    
    full_data["RoomData"] = room_data
    full_data["TransitionData"] = transition_data
    full_data["MapData"] = map_init_strings
    full_data["ItemData"] = gen.item_data
    full_data["BossData"] = gen.grid[boss_tile].layout_id

    return full_data

def merge_bytes_to_int(a: int, b: int) -> int:
    return (a << 8) + b

async def main():
    global exit, seed
    reader, writer = await asyncio.open_connection("127.0.0.1", PORT)
    print("Connected to Server")
    while not exit:
        try:
            command = await reader.readuntil(b"#")
            command_type = command[0]
        except asyncio.IncompleteReadError:
            print("Server closed, exiting")
            command = ""
            command_type = 2
        match command_type:
            case 1: # Generate Floor
                start_inventory = []
                i = 3
                while i < len(command)-2:
                    start_inventory.append(merge_bytes_to_int(command[i+1], command[i]))
                    i += 2
                if seed != -1:
                    random.seed(seed)
                print(f"Start Inventory = {start_inventory}")
                generator = FloorGenerator(int(command[1]), int(command[2]), "Original_EL_Sorted_Test.json", start_inventory)
                success = False
                while not success:
                    success = generator.generate_floor()
                package = generate_package(generator)
                package_string = json.dumps(package)
                writer.write(package_string.encode())
                await writer.drain()
                print("\nWrote Package Data to Server")
            case 2:
                exit = True
            case _:
                print(f"Received unknown command_type {command_type}")
        print(f"Command = ", end="")
        for b in command:
            print(b, end=" ")
        print("")
    
    writer.close()
    await writer.wait_closed()
    print("Socket closed")

try:
    seed = int(sys.argv[1])
except ValueError:
    print(f"Could not convert '{sys.argv[1]}' to integer, using random seed")
    seed = -1
except:
    seed = -1

asyncio.run(main())