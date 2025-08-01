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
        self.board = Board(SOLITAIRE)
        self.board.static = False # The pegs can be dragged
        self.empty_board = Board(EMPTY_BOARD)
        self.empty_board.static = True # This will remain the same throughout
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.widget_map = {}
        self.game_over = False
        self.init_board()

    def init_board(self):
        self.root.title("Solitaire game")
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.draw_grid(self.empty_board)
        self.draw_grid(self.board)
        solution = self.board.solve(npegs=1)
        self.animate_solution(solution)
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
            # Locate the jump peg (easy because we kept track)
            (to_remove_r, to_remove_c) = self.board.available_locs[(final_r, final_c)]
            new_grid[final_r, final_c] = 1
            new_grid[to_remove_r, to_remove_c] = 0
            new_grid[r, c] = 0
            self.board.player_history.append(self.board.grid)
            self.board.grid = new_grid
            self.widget_map[(to_remove_r, to_remove_c)].destroy()
        else:
            (final_r, final_c) = (r, c)

        # Now - to get perfect alignment, we destroy the peg, and recreate it at the final_loc.
        # If the jump didn't succeed, then the final loc is the same as the starting loc
        widget.destroy()
        self.make_peg(final_r, final_c, self.board.static)
        # The below should ensure "Game over" message only pops up once
        if not self.game_over:
            self.check_game_end()

    def draw_grid(self, board:Board):
        for r, row_data in enumerate(board.grid):
            for c, cell_data in enumerate(row_data):
                if cell_data == 1:
                    self.make_peg(r, c, board.static)

    def make_peg(self, row, col, static:bool):
        # We'll create a new widget for each circle
        widget = Canvas(self.mainframe, height=GRID_SIZE, width=GRID_SIZE)
        if static:
            widget.create_oval(10, 10, GRID_SIZE-10, GRID_SIZE-10) # The hole for the peg
        else:
            widget.create_oval(5, 5, GRID_SIZE-5, GRID_SIZE-5, fill="teal")
            self.make_draggable(widget)
            self.widget_map[(row, col)] = widget # To help select and destroy it later
        widget.grid(row=row, column=col, padx=0, pady=0)
        # print(widget.winfo_x(), widget.winfo_y())

    def check_game_end(self):
        if not self.board.find_moves():
            npegs = np.sum(self.board.grid == 1)
            messagebox.showinfo(message=f"Game Over!\nNumber of pegs left: {npegs}")
            self.game_over = True

    def animate_solution(self, solution, idx=0):
        if idx >= len(solution) - 1:
            return
        init_board = solution[idx]
        final_board = solution[idx + 1]
        self.animate_move_with_callback(init_board, final_board, lambda: self.animate_solution(solution, idx + 1))
    
    def animate_move_with_callback(self, init_board, final_board, callback):
        init_grid, final_grid = init_board.grid, final_board.grid
        delta_grid = final_grid - init_grid
        final_loc = np.nonzero(delta_grid == 1)
        final_peg = (int(final_loc[0][0]), int(final_loc[1][0])) # Note this location is empty
        # Let's create a final_peg, and hide it - makes it easier to move
        print(final_peg)
        self.make_peg(final_peg[0], final_peg[1], False)
        final_widget = self.widget_map[final_peg]
        Misc.lower(final_widget)

        # This is required - to ensure the peg actually gets drawn... took help from Gemini
        self.mainframe.update_idletasks()

        removed_indices = np.nonzero(delta_grid == -1)
        # print(removed_indices)
        ind1_r, ind1_c = int(removed_indices[0][0]), int(removed_indices[1][0])
        ind2_r, ind2_c = int(removed_indices[0][1]), int(removed_indices[1][1])

        dist_ind1_final_loc = abs(ind1_r-final_peg[0]) + abs(ind1_c-final_peg[1])
        jump_peg = (ind1_r, ind1_c) if dist_ind1_final_loc == 1 else (ind2_r, ind2_c)
        init_peg = (ind1_r, ind1_c) if dist_ind1_final_loc == 2 else (ind2_r, ind2_c)
        
        # Now we need to move the init_peg to the final_peg
        # Then remove the init peg, jump peg, and re-create the final peg
        init_widget = self.widget_map[init_peg]
        jump_widget = self.widget_map[jump_peg]
        self.animate_widget_with_callback(init_widget, jump_widget, final_widget, callback)

    def animate_widget_with_callback(self, init_widget, jump_widget, final_widget, callback, speed=5, after_id=None):
        Misc.lift(init_widget)
        current_x = init_widget.winfo_x()
        current_y = init_widget.winfo_y()

        target_x = final_widget.winfo_x()
        target_y = final_widget.winfo_y()

        dx = target_x - current_x
        dy = target_y - current_y
        distance = (dx**2 + dy**2)**0.5

        if distance < speed:
            # Cancel any pending after callback before destroying
            if after_id is not None:
                init_widget.after_cancel(after_id)
            init_widget.destroy()
            jump_widget.destroy()
            Misc.lift(final_widget)
            if callback:
                final_widget.after(200, callback)  # Call the callback after a short delay
            return
        
        # Calculate the next step's position
        # Move 'speed' pixels in the direction of the target
        next_x = current_x + (dx / distance) * speed
        next_y = current_y + (dy / distance) * speed
        
        # Move the widget to the next position
        init_widget.place(x=next_x, y=next_y)

        # Schedule the next frame of the animation after a short delay (e.g., 15ms)
        def next_frame():
            self.animate_widget_with_callback(
                init_widget, jump_widget, final_widget, callback, speed, after_id=new_after_id
            )
        new_after_id = init_widget.after(15, next_frame)