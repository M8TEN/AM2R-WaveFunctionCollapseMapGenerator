def valid_connection_tile(group: list, position: tuple, tile_pos_dict: dict) -> bool:
    if not position in tile_pos_dict:
        return False
    tile = tile_pos_dict[position]
    return not tile in group and tile["color"] != 3 and tile["special"] != 1
    

def find_group(group: list, start: dict, checked: list, tile_pos_dict: dict, wall_type: int = 2) -> None:
    if start in group or start in checked:
        return

    group.append(start)
    checked.append(start)
    if start["wallR"] == wall_type:
        new_position = (start["x"] + 1, start["y"])
        if new_position in tile_pos_dict:
            find_group(group, tile_pos_dict[new_position], checked, tile_pos_dict, wall_type)
    if start["wallU"] == wall_type:
        new_position = (start["x"], start["y"] - 1)
        if new_position in tile_pos_dict:
            find_group(group, tile_pos_dict[new_position], checked, tile_pos_dict, wall_type)
    if start["wallL"] == wall_type:
        new_position = (start["x"] - 1, start["y"])
        if new_position in tile_pos_dict:
            find_group(group, tile_pos_dict[new_position], checked, tile_pos_dict, wall_type)
    if start["wallD"] == wall_type:
        new_position = (start["x"], start["y"] + 1)
        if new_position in tile_pos_dict:
            find_group(group, tile_pos_dict[new_position], checked, tile_pos_dict, wall_type)
        

def create_tile_pos_dict(tile_data: list) -> dict:
    tile_pos_dict = {}
    for t in range(len(tile_data)):
        tile = tile_data[t]
        position = (tile["x"], tile["y"])
        tile_pos_dict[position] = tile
    
    return tile_pos_dict

def connect_areas(tile_pos_dict: dict, original_data: list) -> None:
    num_connected = 0
    run = 0

    while len(original_data) != num_connected:
        run += 1
        checked = []
        new_group = []
        print(f"Searching connections (Run {run})", end="\r")
        find_group(new_group, original_data[0], checked, tile_pos_dict)
        for tile in new_group:
            tile_position = (tile["x"], tile["y"])
            left_position = (tile_position[0] - 1, tile_position[1])
            right_position = (tile_position[0] + 1, tile_position[1])
            top_position = (tile_position[0], tile_position[1] - 1)
            bottom_position = (tile_position[0], tile_position[1] + 1)
            if valid_connection_tile(new_group, left_position, tile_pos_dict):
                tile["wallL"] = 2
                tile_pos_dict[left_position]["wallR"] = 2
                break
            if valid_connection_tile(new_group, top_position, tile_pos_dict):
                tile["wallU"] = 2
                tile_pos_dict[top_position]["wallD"] = 2
                break
            if valid_connection_tile(new_group, right_position, tile_pos_dict):
                tile["wallR"] = 2
                tile_pos_dict[right_position]["wallL"] = 2
                break
            if valid_connection_tile(new_group, bottom_position, tile_pos_dict):
                tile["wallD"] = 2
                tile_pos_dict[bottom_position]["wallU"] = 2
                break
        num_connected = len(new_group)

if __name__ == "__main__":
    import json
    with open("WFC_Output.json", "r") as file:
        wfc_data: list = json.load(file)
    tile_pos_dict: dict = create_tile_pos_dict(wfc_data)
    connect_areas(tile_pos_dict, wfc_data)
    out_path: str = "GroupedOutput.json"
    with open(out_path, "w") as file:
        json.dump(list(tile_pos_dict.values()), file, indent=2)
    print(f"Wrote new map data to {out_path}")