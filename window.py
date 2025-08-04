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
        # Adding support for history, to enable moving through it using the arrow keys
        self.history = [self.board.grid.copy()]
        self.future = [] # This will be used to store future moves, if we go back in history
        self.draw_grid(self.empty_board)
        self.draw_grid(self.board)
        # self.animation_finished = True  # To track if any animation is in progress

    def reset_board(self, grid=None, reset_history=False):
        grid = SOLITAIRE if grid is None else grid
        self.board = Board(grid)
        self.board.static = False
        for peg in self.widget_map:
            if self.widget_map[peg]:
                self.widget_map[peg].destroy()
        self.widget_map = {}
        # Also reset the history and future if needed
        if reset_history:
            self.history = [self.board.grid.copy()]
            self.future = []
        self.draw_grid(self.board)

    def init_controls(self):
        controls = ttk.Frame(self.mainframe)
        controls.grid(column=1, row=0, sticky=(N, W, E, S))
        reset_button = ttk.Button(controls, text="Reset", command=lambda: self.reset_board(reset_history=True))
        reset_button.grid(column=0, row=0, padx=5, pady=5)
        solve_button = ttk.Button(controls, text="Solve", command=self.solve_board)
        solve_button.grid(column=0, row=1, padx=5, pady=5)
        hint_button = ttk.Button(controls, text="Hint", command=lambda: self.solve_board(hint=True))
        hint_button.grid(column=0, row=2, padx=5, pady=5)
        self.root.bind("<Left>", self.prev_move)
        self.root.bind("<Right>", self.next_move)

    def prev_move(self, _event=None):
        if len(self.history) <= 1:
            messagebox.showinfo(message="No previous moves to go back to!")
            return
        # Pop the last move from history, and push it to future
        last_move = self.history.pop()
        self.future.append(last_move)
        # Now set the board to the last move in history
        self.board.grid = self.history[-1]
        init_peg, jump_peg, final_peg = self.get_pegs(self.board.grid, last_move)
        # Destroy / Recreate the pegs at the correct locations
        # Since there is no animation, destroying the final peg is ok. 
        final_widget = self.widget_map[final_peg]
        final_widget.destroy()
        self.widget_map[final_peg] = None  # Remove the final peg from the widget map
        self.make_peg(init_peg[0], init_peg[1], self.board.static)
        self.make_peg(jump_peg[0], jump_peg[1], self.board.static)
        self.root.update_idletasks() 

    def next_move(self, _event=None):
        if not self.future:
            messagebox.showinfo(message="No future moves to go to!")
            return
        # Pop the last move from future, and push it to history
        next_move = self.future.pop()
        self.history.append(next_move)

        self.animation_wrapper([self.board.grid, next_move])

    def solve_board(self, hint=False):
        if np.sum(self.board.grid == 1) == 1:
            messagebox.showinfo(message="Game already solved!")
            return
        # - This was the Python solution...
        # solution = self.board.solve() 
        # Instead, let's use Julia to make the solver Fasterrrrr

        # Warn the user that solving is in progress, and take control away..         
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

        # Convert the board to a Julia matrix
        jl_matrix = juliacall.convert(jl.Matrix[jl.Int64], self.board.grid)
        # And get Julia to solve it. The function being used (solver) is defined in the Julia package SolSolver
        solution = jl.solve(jl_matrix)

        # Now we can close the solving dialog
        loading_dialog.destroy()
        
        # Convert the solution (Julia list of Julia matrices) to a Python list of numpy arrays
        # And send it to be animated
        if solution:
            py_solution = []
            for solution_step in solution:
                py_solution.append(solution_step.to_numpy())
            if hint:
                # If this is a "hint" call, we only want to highlight the pegs to be moved.
                py_solution = py_solution[0:2]
            self.animation_wrapper(py_solution)
            self.history += py_solution[1:]
            if hint:
                self.future = []
                self.root.after(ANIMATION_SPEED * 50, self.prev_move)  # Reset the board after a delay
                
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
            self.board.grid = new_grid
            self.history.append(self.board.grid)  # Update the history with the new grid
            self.future = []  # Clear the future moves, as we have a new move
            # print(self.history)
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

    def animation_wrapper(self, solution):
        # This method first takes away control from the window to prevent user interaction during animation
        # Then it starts the animation
        controller_widget = tk.Toplevel(self.root)
        controller_widget.grab_set()  # Prevent interaction with the main window during animation
        # controller_widget.lift()  # Keep the controller widget on top
        Misc.lower(controller_widget)  # Lower it to avoid focus issues
        self.animate_solution(solution, controller_widget=controller_widget)

    def animate_solution(self, solution, controller_widget, idx=0):
        # print(idx)
        if idx >= len(solution) - 1:
            self.root.after(ANIMATION_SPEED * 10, lambda: controller_widget.destroy())
            return
        init_grid = solution[idx]
        final_grid = solution[idx + 1]
        self.animate_move_with_callback(init_grid, final_grid, lambda: self.animate_solution(solution, controller_widget, idx + 1))
        self.board.grid = final_grid
        # if self.animation_finished:
        #     controller_widget.destroy()
    
    def animate_move_with_callback(self, init_grid, final_grid, callback):
        init_peg, jump_peg, final_peg = self.get_pegs(init_grid, final_grid)
        self.make_peg(final_peg[0], final_peg[1], False)
        final_widget = self.widget_map[final_peg]
        Misc.lower(final_widget)

        # This is required - to ensure the peg actually gets drawn... took help from Gemini
        self.boardframe.update_idletasks()
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
            # This removes some weird Tcl bugs with the animation, due to callbacks being called after the widget is destroyed
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
        
    def get_pegs(self, init_grid, final_grid):
        delta_grid = final_grid - init_grid
        final_loc = np.nonzero(delta_grid == 1)
        final_peg = final_loc[0][0], final_loc[1][0]

        removed_indices = np.nonzero(delta_grid == -1)
        ind1_r, ind1_c = removed_indices[0][0], removed_indices[1][0]
        ind2_r, ind2_c = removed_indices[0][1], removed_indices[1][1]

        dist_ind1_final_loc = abs(ind1_r-final_peg[0]) + abs(ind1_c-final_peg[1])
        jump_peg = (ind1_r, ind1_c) if dist_ind1_final_loc == 1 else (ind2_r, ind2_c)
        init_peg = (ind1_r, ind1_c) if dist_ind1_final_loc == 2 else (ind2_r, ind2_c)
        return init_peg, jump_peg, final_peg