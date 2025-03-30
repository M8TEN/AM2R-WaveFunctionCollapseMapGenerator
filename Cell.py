from math import inf, log

'''Basic class holding relevant information about a cell in the main WFC algorithm'''

class Cell:
    def __init__(self, position, num_of_tiles):
        self.position = position
        self.options = list(range(num_of_tiles))
        self.entropy = inf
        self.collapsed = False
    
    def __str__(self):
        return f"Cell {self.position}, Options: {len(self.options)}"

    # Shannon Entropy
    def calculate_entropy(self):
        tile_probability = 1.0/len(self.options)
        l = log(1.0/tile_probability, 2)
        entropy = len(self.options) * tile_probability * l
        self.entropy = entropy
        return entropy