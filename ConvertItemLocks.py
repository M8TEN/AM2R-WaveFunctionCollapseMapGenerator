import os
import json

def convert_locks_to_int(locks: list) -> int:
    lock_int: int = 0
    for lock_id in locks:
        lock_int |= (1 << lock_id)
    
    return lock_int

for file_name in os.listdir("RoomSets"):
    full_path: str = os.path.join("RoomSets", file_name)
    with open(full_path) as file:
        room_set = json.load(file)
    
    for room in room_set["AllRooms"]:
        if len(room["Lock"]) == 0: continue
        room["Lock"] = [convert_locks_to_int(room["Lock"])]
        for key in room["Layout"]:
            if len(room["Layout"][key][5]) == 0: continue
            room["Layout"][key][5] = [convert_locks_to_int(room["Layout"][key][5])]

    with open(full_path, "w") as out_file:
        json.dump(room_set, out_file, indent=2)