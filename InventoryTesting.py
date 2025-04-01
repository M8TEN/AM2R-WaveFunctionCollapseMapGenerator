from BranchingFloorGenerator import inventory_to_lock_states

inv = [0]*21

print(f"Possible Room Lock states\n{sorted(inventory_to_lock_states(inv))}")