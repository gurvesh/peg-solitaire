from tkinter import *
from tkinter import ttk
from window import Window
from board import Board
import numpy as np

DTYPE = np.dtype("i")

root = Tk()
Window(root)

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
#mainframe['padding'] = 5

# ttk.Label(mainframe, text="Something")\
#    .grid(column=1, row=1, sticky=W)

board = Board(np.array([
    [8, 8, 1, 1, 1, 8, 8],
    [8, 8, 1, 1, 1, 8, 8],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [8, 8, 1, 1, 1, 8, 8],
    [8, 8, 1, 1, 1, 8, 8]    
], DTYPE), static=False, parent=mainframe)

empty_board = Board(np.array([
    [8, 8, 1, 1, 1, 8, 8],
    [8, 8, 1, 1, 1, 8, 8],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1],
    [8, 8, 1, 1, 1, 8, 8],
    [8, 8, 1, 1, 1, 8, 8]    
], DTYPE), static=True, parent=mainframe)

empty_board.draw_grid()
board.draw_grid()


board.solve(1)

root.mainloop()

