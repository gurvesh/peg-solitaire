import numpy as np
DTYPE = np.dtype("i")
import random

class Board():
    def __init__(self, grid):
        # Data below is for board management and solving
        self.initial_grid = grid
        self.grid = grid
        self.solver_history = []
        self.player_history = []
        self.boards_seen = set()
        self.moves = 0
        self.selected_peg = [0, 0]
        self.available_locs = {}

    # Let's define a way to reset the grid, if we want to start again
    def reset(self):
        # self.grid = self.initial_grid
        self.solver_history = []
        self.boards_seen = set()
        self.moves = 0
    
    # find_moves finds all the next boards in 1 move, starting from the current board
    def find_moves(self) -> list:
        (rows, cols) = self.grid.shape
        results = []
        for r in range(rows):
            for c in range (cols):
                if (self.grid[r][c] == 1):
                    if (r-2 >= 0) and (self.grid[r-1][c] == 1) and (self.grid[r-2][c] == 0):
                        new_grid = self.grid.copy()
                        new_grid[r][c] = 0
                        new_grid[r-1][c] = 0
                        new_grid[r-2][c] = 1
                        results.append(Board(new_grid))
                    if (c+2 < cols) and (self.grid[r][c+1] == 1) and (self.grid[r][c+2] == 0):
                        new_grid = self.grid.copy()
                        new_grid[r][c] = 0
                        new_grid[r][c+1] = 0
                        new_grid[r][c+2] = 1
                        results.append(Board(new_grid))
                    if (r+2 < rows) and (self.grid[r+1][c] == 1) and (self.grid[r+2][c] == 0):
                        new_grid = self.grid.copy()
                        new_grid[r][c] = 0
                        new_grid[r+1][c] = 0
                        new_grid[r+2][c] = 1
                        results.append(Board(new_grid))
                    if (c-2 >= 0) and (self.grid[r][c-1] == 1) and (self.grid[r][c-2] == 0):
                        new_grid = self.grid.copy()
                        new_grid[r][c] = 0
                        new_grid[r][c-1] = 0
                        new_grid[r][c-2] = 1
                        results.append(Board(new_grid))
        return results

    # Using numpy allows for easy rotations to check if the board has been seen before
    def __check_similar(self, boards_seen: set) -> bool:
        return (
            self.grid.data.tobytes() in boards_seen or 
            np.rot90(self.grid, 1).data.tobytes() in boards_seen or 
            np.rot90(self.grid, 2).data.tobytes() in boards_seen or
            np.rot90(self.grid, 3).data.tobytes() in boards_seen or 
            np.transpose(self.grid).data.tobytes() in boards_seen or
            np.rot90(np.transpose(self.grid), 1).data.tobytes() in boards_seen or
            np.rot90(np.transpose(self.grid), 2).data.tobytes() in boards_seen or
            np.rot90(np.transpose(self.grid), 3).data.tobytes() in boards_seen
        )
        
    def solve(self) -> list:
        for npegs in range(1, 6):
            self.reset()
            if self.__solve_r([self], npegs):
                print(f"Solution found with {npegs} pegs. No. of moves made to find this: ", self.moves)
                solution = self.solver_history.copy()
                return solution
        print("No solution found")
        return []

    # We use DFS to solve the board. 
    def __solve_r(self, history: list, npegs: int) -> bool:
        for new_board in history[-1].find_moves():
            # print(new_board.grid)
            self.moves += 1
            if np.sum(new_board.grid == 1) == npegs:
                history.append(new_board)
                self.solver_history = history
                return True
            if new_board.__check_similar(self.boards_seen): # seen a similar board, go to next one
                continue
            history_copy = history.copy()
            history_copy.append(new_board) # Keep track of where we are
            self.boards_seen.add(new_board.grid.data.tobytes()) # Add the new board to previously seen boards
            if self.__solve_r(history_copy, npegs):
                return True
        return False
    
    # find_available_locs finds only the available locs for the selected_peg
    # Each available loc will "point to" the jump peg to be removed. 
    # This should enable easy removal and placement of the peg
    # This is a convenience function for updating the grid window representation.
    def find_available_locs(self):
        results = {}
        (rows, cols) = self.grid.shape
        [r, c] = self.selected_peg
        if (r-2 >= 0) and (self.grid[r-1][c] == 1) and (self.grid[r-2][c] == 0):
            results[(r-2, c)] = (r-1, c)
        if (c+2 < cols) and (self.grid[r][c+1] == 1) and (self.grid[r][c+2] == 0):
            results[(r, c+2)] = (r, c+1)
        if (r+2 < rows) and (self.grid[r+1][c] == 1) and (self.grid[r+2][c] == 0):
            results[(r+2, c)] = (r+1, c)
        if (c-2 >= 0) and (self.grid[r][c-1] == 1) and (self.grid[r][c-2] == 0):
            results[(r, c-2)] = (r, c-1)
        self.available_locs = results