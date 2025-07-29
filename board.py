import numpy as np
from tkinter import messagebox
from tkinter import *
from tkinter import ttk

DTYPE = np.dtype("i")

class Board():
    def __init__(self, grid, static:bool, parent:Frame):
        # Data below is for board management and solving
        self.initial_grid = grid
        self.grid = grid
        self.solver_history = []
        self.player_history = []
        self.boards_seen = set()
        self.moves = 0

        # Data below is for drawing the board
        self.parent = parent
        self.grid_size = 100
        self.static = static
        self.selected_peg = [0, 0]
        self.available_locs = {}
        self.widget_map = {}
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._game_over = False

    # Let's define a way to reset the grid, if we want to start again
    def reset(self):
        self.grid = self.initial_grid
        self.solver_history = []
        self.boards_seen = set()
        self.moves = 0
    
    def __find_moves(self) -> list:
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
                        results.append(Board(new_grid, static=self.static, parent=self.parent))
                    if (c+2 < cols) and (self.grid[r][c+1] == 1) and (self.grid[r][c+2] == 0):
                        new_grid = self.grid.copy()
                        new_grid[r][c] = 0
                        new_grid[r][c+1] = 0
                        new_grid[r][c+2] = 1
                        results.append(Board(new_grid, static=self.static, parent=self.parent))
                    if (r+2 < rows) and (self.grid[r+1][c] == 1) and (self.grid[r+2][c] == 0):
                        new_grid = self.grid.copy()
                        new_grid[r][c] = 0
                        new_grid[r+1][c] = 0
                        new_grid[r+2][c] = 1
                        results.append(Board(new_grid, static=self.static, parent=self.parent))
                    if (c-2 >= 0) and (self.grid[r][c-1] == 1) and (self.grid[r][c-2] == 0):
                        new_grid = self.grid.copy()
                        new_grid[r][c] = 0
                        new_grid[r][c-1] = 0
                        new_grid[r][c-2] = 1
                        results.append(Board(new_grid, static=self.static, parent=self.parent))
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
        
    def solve(self, npegs: int) -> list:
        if self.__solve_r([self], npegs):
            print("Solution found. No. of moves made to find this: ", self.moves)
            solution = self.solver_history.copy()
        else:
            print("No solution found")
            solution = []
        self.reset()
        return solution

    # We use DFS to solve the board. 
    def __solve_r(self, history: list, npegs: int) -> bool:
        for new_board in history[-1].__find_moves():
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
    
    # Methods below are for drawing and updating the board
    def make_draggable(self, widget):
        """Makes a widget draggable."""
        widget.bind("<Button-1>", self.drag_start)
        widget.bind("<B1-Motion>", self.drag_motion)
        widget.bind("<ButtonRelease-1>", self.drag_end)

    def drag_start(self, event):
        widget = event.widget
        Misc.lift(widget)
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        x = widget.winfo_x() - self._drag_start_x + event.x
        y = widget.winfo_y() - self._drag_start_y + event.y
        
        self.selected_peg = [
            round(y / (self.grid_size)),
            round(x / (self.grid_size))
        ]
        self.find_available_locs()
        # print(self.available_locs)
        
    def drag_motion(self, event):
        widget = event.widget
        x = widget.winfo_x() - self._drag_start_x + event.x
        y = widget.winfo_y() - self._drag_start_y + event.y
        widget.place(x=x, y=y)

    # Drag_end has to do a lot of work:
    # 1/ Figure out where the dragging has ended
    # 2/ See if that's a valid location. If it is, then update the grid, and do the peg removals
    # 3/ If not a valid location, return the peg to its starting location
    # 4/ Check if the game is over
    def drag_end(self, event):
        widget = event.widget
        x = widget.winfo_x() - self._drag_start_x + event.x
        y = widget.winfo_y() - self._drag_start_y + event.y

        final_r = round(y / (self.grid_size))
        final_c = round(x / (self.grid_size))

        # print(f"moving to: {final_r, final_c}")

        [r, c] = self.selected_peg
        if (final_r, final_c) in self.available_locs:
            # Update the grid to reflect the move
            new_grid = self.grid.copy()
            (to_remove_r, to_remove_c) = self.available_locs[(final_r, final_c)]
            new_grid[final_r, final_c] = 1
            new_grid[to_remove_r, to_remove_c] = 0
            new_grid[r, c] = 0
            self.player_history.append(self.grid)
            self.grid = new_grid
            # Remove the jump peg (easy because we kept track)
            self.widget_map[(to_remove_r, to_remove_c)].destroy()
        else:
            (final_r, final_c) = (r, c)

        # Now - to get perfect alignment, we destroy the peg, and recreate it at the final_loc.
        # If the jump didn't succeed, then the final loc is the same as the starting loc
        widget.destroy()
        new_widget = Canvas(self.parent, height=self.grid_size, width=self.grid_size)
        new_widget.create_oval(5, 5, self.grid_size-5, self.grid_size-5, fill="teal")
        self.make_draggable(new_widget)
        new_widget.grid(row=final_r, column=final_c, padx=0, pady=0)
        self.widget_map[(final_r, final_c)] = new_widget

        # The below should ensure this message only pops up once
        if not self._game_over:
            self.check_game_end()
    
    def draw_grid(self):
        for r, row_data in enumerate(self.grid):
            for c, cell_data in enumerate(row_data):
                if cell_data == 1:
                    # We'll create a new widget for each circle
                    widget = Canvas(self.parent, height=self.grid_size, width=self.grid_size)
                    if self.static:
                        widget.create_oval(10, 10, self.grid_size-10, self.grid_size-10) # The hole for the peg
                    else:
                        widget.create_oval(5, 5, self.grid_size-5, self.grid_size-5, fill="teal")
                        self.make_draggable(widget)
                        self.widget_map[(r, c)] = widget # To help select and destroy it later
                    # Place the widget in the grid at the specified row and column
                    widget.grid(row=r, column=c, padx=0, pady=0)
    
    # We find only the available locs for the selected_peg
    # Each available loc will "point to" the jump peg to be removed. 
    # This should enable easy removal/destruction and placement of the peg
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

    def check_game_end(self):
        if not self.__find_moves():
            npegs = np.sum(self.grid == 1)
            messagebox.showinfo(message=f"Game Over!\nNumber of pegs left: {npegs}")
            self._game_over = True
