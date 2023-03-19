import math
import random
import time

SOLVE_TIME_LIMIT = 5


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __str__(self):
        return f'({self.row}, {self.col})'


class SudokuSolver:
    def solve(self, board: list, start_time):
        raise NotImplemented


class CSPSolver(SudokuSolver):
    def __init__(self):
        self._board = []
        self._size = 0
        self._empty_cells = []
        self._domains = {}
        self._empty_cells_in_rows = {}
        self._empty_cells_in_cols = {}
        self._empty_cells_in_grids = {}
        self._assignment = {}
        self._start_time = None

    def solve(self, board: list, start_time):
        self._board = board
        self._size = len(self._board)
        self._find_empty_cells()
        self._get_initial_domains()
        self._start_time = time.time()
        # return self._fill_cell()

    def _find_empty_cells(self):
        self._empty_cells_in_rows = {row: [] for row in range(self._size)}
        self._empty_cells_in_cols = {col: [] for col in range(self._size)}
        self._empty_cells_in_grids = {grid: [] for grid in range(self._size)}
        subgrid_row = math.floor(self._size ** 0.5)
        subgrid_col = self._size // subgrid_row
        for row in range(self._size):
            for col in range(self._size):
                if self._board[row][col] == 0:
                    grid_index = col // subgrid_col + row // subgrid_row * (self._size // subgrid_col)
                    cell = Cell(row, col)
                    self._empty_cells.append(cell)
                    self._empty_cells_in_rows[row].append(cell)
                    self._empty_cells_in_cols[col].append(cell)
                    self._empty_cells_in_grids[grid_index].append(cell)
                    self._assignment[cell] = 0

    def _get_initial_domains(self):
        for cell in self._empty_cells:
            row = cell.row
            col = cell.col
            self._domains[cell] = set(range(1, n + 1)) - set(self._board[row]) - \
                                  set([row[col] for row in self._board]) - set(self.get_subgrid(row, col))

    def _fill_cell(self):
        if time.time() - self._start_time > SOLVE_TIME_LIMIT:
            return False
        return self._board

    def get_subgrid(self, row, col):
        subgrid_row = math.floor(self._size ** 0.5)
        subgrid_col = self._size // subgrid_row
        row_start = (row // subgrid_row) * subgrid_row
        col_start = (col // subgrid_col) * subgrid_col
        return [self._board[i][j] for i in range(row_start, row_start + subgrid_row) for j in
                range(col_start, col_start + subgrid_col)]


class BruteForceSolver(SudokuSolver):
    def solve(self, board, start_time):
        if time.time() - start_time > SOLVE_TIME_LIMIT:
            return False
        n = len(board)
        #
        empty = self.find_empty(board)
        if not empty:
            return board
            # return True
        row, col = empty
        for num in self.get_choices(board, row, col):
            if self.is_valid(board, row, col, num):
                board[row][col] = num
                if self.solve(board, start_time):
                    return board
                    # return True
                board[row][col] = 0
        return False

    def fill_naked_single(self, board):
        changed = False
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] == 0:
                    choices = self.get_choices(board, row, col)
                    print(choices)
                    if len(choices) == 1:
                        board[row][col] = choices[0]
                        changed = True
                        print(row, col, choices)
        return changed

    def find_empty(self, board):
        n = len(board)
        min_choices = n + 1
        min_row, min_col = None, None
        for row in range(n):
            for col in range(n):
                if board[row][col] == 0:
                    choices = self.get_choices(board, row, col)
                    num_choices = len(choices)
                    # if num_choices == 0:
                    #     return None
                    if num_choices < min_choices:
                        min_choices = num_choices
                        min_row, min_col = row, col
        if min_row is None and min_col is None:
            return None
        return min_row, min_col

    def get_choices(self, board, row, col):
        n = len(board)
        choices = set(range(1, n + 1)) - set(self.get_row(board, row)) - set(self.get_col(board, col)) - set(
            self.get_subgrid(board, row, col))
        choices = list(choices)
        random.shuffle(choices)
        return choices

    def get_row(self, board, row):
        return board[row]

    def get_col(self, board, col):
        return [board[row][col] for row in range(len(board))]

    def is_valid(self, board, row, col, num):
        n = len(board)
        # Check row and column
        for i in range(n):
            if board[row][i] == num or board[i][col] == num:
                return False
        # Check subgrid
        subgrid_size = int(n ** 0.5)
        row_start = (row // subgrid_size) * subgrid_size
        col_start = (col // subgrid_size) * subgrid_size
        for i in range(row_start, row_start + subgrid_size):
            for j in range(col_start, col_start + subgrid_size):
                if board[i][j] == num:
                    return False
        return True

    def get_subgrid(self, board, row, col):
        subgrid_size = int(len(board) ** 0.5)
        row_start = (row // subgrid_size) * subgrid_size
        col_start = (col // subgrid_size) * subgrid_size
        return [board[i][j] for i in range(row_start, row_start + subgrid_size) for j in
                range(col_start, col_start + subgrid_size)]

