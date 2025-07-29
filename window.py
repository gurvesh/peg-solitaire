from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from board import Board
import numpy as np
from constants import SOLITAIRE, EMPTY_BOARD, GRID_SIZE

class Window():
    def __init__(self, root):
        self.root = root
        self.mainframe = ttk.Frame(self.root)
        self.board = Board(SOLITAIRE, static=False)
        self.empty_board = Board(EMPTY_BOARD, static=True)
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.widget_map = {}
        self.game_over = False
        # self.board.solve(npegs=1)
        self.init_board()

    def init_board(self):
        self.root.title("Solitaire game")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.draw_grid(self.empty_board)
        self.draw_grid(self.board)
        self.root.mainloop()

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
        
        self.board.selected_peg = [
            round(y / GRID_SIZE),
            round(x / GRID_SIZE)
        ]
        self.board.find_available_locs()
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
        [r, c] = self.board.selected_peg
        widget = event.widget
        x = widget.winfo_x() - self._drag_start_x + event.x
        y = widget.winfo_y() - self._drag_start_y + event.y

        # Determine the location we're dragging to in grid coords
        final_r = round(y / GRID_SIZE)
        final_c = round(x / GRID_SIZE)
        # print(f"moving to: {final_r, final_c}")
        
        if (final_r, final_c) in self.board.available_locs: # If this is a valid move
            # Update the grid to reflect the move
            new_grid = self.board.grid.copy()
            (to_remove_r, to_remove_c) = self.board.available_locs[(final_r, final_c)]
            new_grid[final_r, final_c] = 1
            new_grid[to_remove_r, to_remove_c] = 0
            new_grid[r, c] = 0
            self.board.player_history.append(self.board.grid)
            self.board.grid = new_grid
            # Remove the jump peg (easy because we kept track)
            self.widget_map[(to_remove_r, to_remove_c)].destroy()
        else:
            (final_r, final_c) = (r, c)

        # Now - to get perfect alignment, we destroy the peg, and recreate it at the final_loc.
        # If the jump didn't succeed, then the final loc is the same as the starting loc
        widget.destroy()
        new_widget = Canvas(self.mainframe, height=GRID_SIZE, width=GRID_SIZE)
        new_widget.create_oval(5, 5, GRID_SIZE-5, GRID_SIZE-5, fill="teal")
        self.make_draggable(new_widget)
        new_widget.grid(row=final_r, column=final_c, padx=0, pady=0)
        self.widget_map[(final_r, final_c)] = new_widget

        # The below should ensure "Game over" message only pops up once
        if not self.game_over:
            self.check_game_end()

    def draw_grid(self, board:Board):
        for r, row_data in enumerate(board.grid):
            for c, cell_data in enumerate(row_data):
                if cell_data == 1:
                    # We'll create a new widget for each circle
                    widget = Canvas(self.mainframe, height=GRID_SIZE, width=GRID_SIZE)
                    if board.static:
                        widget.create_oval(10, 10, GRID_SIZE-10, GRID_SIZE-10) # The hole for the peg
                    else:
                        widget.create_oval(5, 5, GRID_SIZE-5, GRID_SIZE-5, fill="teal")
                        self.make_draggable(widget)
                        self.widget_map[(r, c)] = widget # To help select and destroy it later
                    # Place the widget in the grid at the specified row and column
                    widget.grid(row=r, column=c, padx=0, pady=0)

    def check_game_end(self):
        if not self.board.find_moves():
            npegs = np.sum(self.board.grid == 1)
            messagebox.showinfo(message=f"Game Over!\nNumber of pegs left: {npegs}")
            self.game_over = True
    