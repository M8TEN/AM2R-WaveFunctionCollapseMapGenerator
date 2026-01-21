import asyncio
import json
import random
import sys
import random
from BranchingGeneratorAsClass import Tile, FloorGenerator
from copy import deepcopy

PORT: int = 64196
exit: bool = False
seed: int = -1

def generate_package(gen: FloorGenerator, n_boss_keys: int = 0) -> dict:
    full_data = {}
    try:
        boss_tile = gen.placed_dead_ends[random.randint(0, len(gen.placed_dead_ends)-1)]
        boss_tile_obj: Tile = gen.grid[boss_tile]
        print(f"Placed boss room in room with ID {boss_tile_obj.room_id}")
        if not boss_tile_obj.room_id in [435, 436, 437, 438]:
            if boss_tile_obj.d == 2: # If tile has door down
                boss_tile_obj.room_id = 435
                print("Changed room ID to 435")
            elif boss_tile_obj.l == 2:
                boss_tile_obj.room_id = 436
                print("Changed room ID to 436")
            elif boss_tile_obj.u == 2:
                boss_tile_obj.room_id = 437
                print("Changed room ID to 437")
            elif boss_tile_obj.r == 2:
                boss_tile_obj.room_id = 438
                print("Changed room ID to 438")
            else:
                print("Room didn't match expected layout, not replacing room ID")
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
    full_data["BossData"] = n_boss_keys

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
            print(f"Command =", end=" ")
            for b in command:
                print(b, end=" ")
            print("")
        except asyncio.IncompleteReadError:
            print("Server closed, exiting")
            command = ""
            command_type = 2
        match command_type:
            case 1: # Generate Floor
                floor_width: int = int(command[1])
                floor_height: int = int(command[2])
                number_of_keys: int = int(command[3])
                start_inventory: list = []
                i: int = 4
                while i < len(command)-2:
                    start_inventory.append(merge_bytes_to_int(command[i+1], command[i]))
                    i += 2
                if seed != -1:
                    random.seed(seed)
                    print(f"Generating with seed {seed}")
                print(f"Start Inventory = {start_inventory}")
                success: bool = False
                generator: FloorGenerator = None
                while not success:
                    generator = FloorGenerator(floor_width, floor_height, "Original_EL_Sorted_Test.json", deepcopy(start_inventory))
                    success = generator.generate_floor(number_of_keys)
                    if not success: print("Floor generation failed, trying again..\n\n")
                package: dict = generate_package(generator, number_of_keys)
                package_string: str = json.dumps(package)
                writer.write(package_string.encode())
                await writer.drain()
                print("\nWrote Package Data to Server")
            case 2:
                exit = True
            case _:
                print(f"Received unknown command_type {command_type}")
    
    writer.close()
    await writer.wait_closed()
    print("Socket closed")

try:
    seed = int(sys.argv[1])
except ValueError:
    print(f"Could not convert '{sys.argv[1]}' to integer, using random seed")
    seed = random.randint(0, sys.maxsize)
except:
    seed = random.randint(0, sys.maxsize)

asyncio.run(main())