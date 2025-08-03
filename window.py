from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from board import Board
import numpy as np
from constants import SOLITAIRE, EMPTY_BOARD, GRID_SIZE, ANIMATION_SPEED
import juliacall
from juliacall import Main as jl
from juliacall import Pkg as jlPkg

jlPkg.activate("./SolSolver")
jl.seval("using SolSolver")

class Window():
    def __init__(self, root):
        self.root = root
        self.root.title("Solitaire game")
        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.game_over = False
        self.init_board()
        self.init_controls()
        self.root.mainloop()

    def init_board(self):
        self.boardframe = ttk.Frame(self.mainframe)
        self.boardframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.board = Board(SOLITAIRE)
        self.board.static = False # The pegs can be dragged
        self.empty_board = Board(EMPTY_BOARD)
        self.empty_board.static = True # This will remain the same throughout
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.widget_map = {}
        self.draw_grid(self.empty_board)
        self.draw_grid(self.board)

    def reset_board(self):
        self.board = Board(SOLITAIRE)
        self.board.static = False
        for peg in self.widget_map:
            if self.widget_map[peg]:
                self.widget_map[peg].destroy()
        self.widget_map = {}
        self.draw_grid(self.board)

    def init_controls(self):
        self.controls = ttk.Frame(self.mainframe)
        self.controls.grid(column=1, row=0, sticky=(N, W, E, S))
        self.reset_button = ttk.Button(self.controls, text="Reset", command=self.reset_board)
        self.reset_button.grid(column=0, row=0, padx=5, pady=5)
        self.solve_button = ttk.Button(self.controls, text="Solve", command=self.solve_board)
        self.solve_button.grid(column=0, row=1, padx=5, pady=5)
        self.hint_button = ttk.Button(self.controls, text="Hint", command=None)
        self.hint_button.grid(column=0, row=2, padx=5, pady=5)

    def solve_board(self):
        if np.sum(self.board.grid == 1) == 1:
            messagebox.showinfo(message="Game already solved!")
            return
        # print(self.board.grid)
        # Let's use Julia to make the solver Fasterrrrr
        jl_matrix = juliacall.convert(jl.Matrix[jl.Int64], self.board.grid)
        # solution = self.board.solve()
        
        loading_dialog = tk.Toplevel(self.root)
        loading_dialog.title("Solving")
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        dialog_w = 250
        dialog_h = 100
        pos_x = root_x + (root_w // 2) - (dialog_w // 2)
        pos_y = root_y + (root_h // 2) - (dialog_h // 2)
        loading_dialog.geometry(f"{dialog_w}x{dialog_h}+{pos_x}+{pos_y}")
        loading_dialog.transient(self.root)
        loading_dialog.grab_set()
        loading_dialog.resizable(False, False)

        tk.Label(
            loading_dialog,
            text="Solving, please wait...",
        ).grid(row=0, column=0, padx=20, pady=20)

        self.root.update_idletasks()

        solution = jl.solve(jl_matrix)

        loading_dialog.destroy()
        
        if solution:
            py_solution = []
            for solution_step in solution:
                py_solution.append(solution_step.to_numpy())
            self.animate_solution(py_solution)

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
        widget = Canvas(self.boardframe, height=GRID_SIZE, width=GRID_SIZE)
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
        init_grid = solution[idx]
        final_grid = solution[idx + 1]
        self.animate_move_with_callback(init_grid, final_grid, lambda: self.animate_solution(solution, idx + 1))
    
    def animate_move_with_callback(self, init_grid, final_grid, callback):
        delta_grid = final_grid - init_grid
        final_loc = np.nonzero(delta_grid == 1)
        final_peg = final_loc[0][0], final_loc[1][0] # Note this location is empty
        # Let's create a final_peg, and hide it - makes it easier to move
        # print(final_peg)
        self.make_peg(final_peg[0], final_peg[1], False)
        final_widget = self.widget_map[final_peg]
        Misc.lower(final_widget)

        # This is required - to ensure the peg actually gets drawn... took help from Gemini
        self.boardframe.update_idletasks()

        removed_indices = np.nonzero(delta_grid == -1)
        # print(removed_indices)
        ind1_r, ind1_c = removed_indices[0][0], removed_indices[1][0]
        ind2_r, ind2_c = removed_indices[0][1], removed_indices[1][1]

        dist_ind1_final_loc = abs(ind1_r-final_peg[0]) + abs(ind1_c-final_peg[1])
        jump_peg = (ind1_r, ind1_c) if dist_ind1_final_loc == 1 else (ind2_r, ind2_c)
        init_peg = (ind1_r, ind1_c) if dist_ind1_final_loc == 2 else (ind2_r, ind2_c)
        
        # Now we need to move the init_peg to the final_peg
        # Then remove the init peg, jump peg, and re-create the final peg
        init_widget = self.widget_map[init_peg]
        jump_widget = self.widget_map[jump_peg]
        self.animate_widget_with_callback(init_widget, jump_widget, final_widget, callback)
        self.widget_map[init_peg] = None
        self.widget_map[jump_peg] = None

    def animate_widget_with_callback(self, init_widget, jump_widget, final_widget, callback, speed=ANIMATION_SPEED):
        Misc.lift(init_widget)
        current_x = init_widget.winfo_x()
        current_y = init_widget.winfo_y()

        target_x = final_widget.winfo_x()
        target_y = final_widget.winfo_y()

        dx = target_x - current_x
        dy = target_y - current_y
        distance = (dx**2 + dy**2)**0.5

        if distance < speed:
            # Instead of using widget.destroy(), we will hide the widgets, and remove them from the widget_map
            # This removes some weird Tcl bugs with the animation
            Misc.lower(init_widget)
            Misc.lower(jump_widget)
            Misc.lift(final_widget)
            if callback:
                final_widget.after(500 // ANIMATION_SPEED, callback)  # Call the callback after a short delay
            return
        
        # Calculate the next step's position
        # Move 'speed' pixels in the direction of the target
        next_x = current_x + (dx / distance) * speed
        next_y = current_y + (dy / distance) * speed
        
        init_widget.place(x=next_x, y=next_y)

        # Schedule the next frame of the animation after a short delay
        init_widget.after(15, lambda: self.animate_widget_with_callback(
            init_widget, jump_widget, final_widget, callback, speed))