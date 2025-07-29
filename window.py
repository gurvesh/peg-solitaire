from tkinter import *
from tkinter import ttk
from board import Board

class Window():
    def __init__(self, root):
        root.title("Solitaire game")
        

class Grid():
    def __init__(self, grid, static:bool):
        self.grid = grid
        self.grid_size = 30
        self.static = static
        self.selected_peg = [0, 0]
        self.available_locs = []

    def make_draggable(self, widget):
        """Makes a widget draggable."""
        widget.bind("<Button-1>", self.drag_start)
        widget.bind("<B1-Motion>", self.drag_motion)
        widget.bind("<ButtonRelease-1>", self.drag_end)

    def drag_start(self, event):
        widget = event.widget
        Misc.lift(widget)
        widget._drag_start_x = event.x
        widget._drag_start_y = event.y
        x = widget.winfo_x() - widget._drag_start_x + event.x
        y = widget.winfo_y() - widget._drag_start_y + event.y
        
        self.selected_peg = [
            round(x / (self.grid_size)),
            round(y / (self.grid_size))
        ]
        
        self.available_locs = Board(self.grid).find_locs(self.selected_peg)
        
        
    def drag_motion(self, event):
        widget = event.widget
        x = widget.winfo_x() - widget._drag_start_x + event.x
        y = widget.winfo_y() - widget._drag_start_y + event.y
        widget.place(x=x, y=y)

    def drag_end(self, event):
        widget = event.widget
        x = widget.winfo_x() - widget._drag_start_x + event.x
        y = widget.winfo_y() - widget._drag_start_y + event.y

        snapped_x = round(x / (self.grid_size)) * self.grid_size
        snapped_y = round(y / (self.grid_size)) * self.grid_size

        widget.place(x=snapped_x, y=snapped_y)
    
    def draw_grid(self, parent:Frame):
        for r, row_data in enumerate(self.grid):
            for c, cell_data in enumerate(row_data):
                if cell_data == 1:
                    # We'll create a new widget for each circle
                    widget = Canvas(parent, height=30, width=30)
                    if self.static:
                        widget.create_oval(10, 10, 20, 20) # The hole for the marble
                    else:
                        widget.create_oval(5, 5, 25, 25, fill="teal")
                        # 
                        self.make_draggable(widget)
                    # Place the widget in the grid at the specified row and column
                    widget.grid(row=r, column=c, padx=0, pady=0)
                    # widget.place(x=10*self.grid_size, y=10*self.grid_size)
                        

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Line():
    def __init__(self, point1, point2, color="black"):
        self.start = point1
        self.end = point2
        self.color = color

    def draw(self, canvas):
        x1, y1 = self.start.x, self.start.y
        x2, y2 = self.end.x, self.end.y
        canvas.create_line(
            x1, y1, x2, y2, fill=self.color, width=2
        )