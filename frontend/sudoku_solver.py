import math
import random
import time
from collections import deque, Counter

from frontend.sudoku_generator import SudokuGenerator

SOLVE_TIME_LIMIT = 3


class Cell:
    def __init__(self, row, col, grid):
        self.row = row
        self.col = col
        self.grid = grid

    def __str__(self):
        return f'({self.row}, {self.col})'


class SudokuSolver:
    def solve(self, board: list, start_time):
        raise NotImplemented


class CSPSolver(SudokuSolver):
    def __init__(self):
        self._board = []
        self._size = 0
        self._empty_cells = set()
        self._domains = {}
        self._empty_cells_in_rows = {}
        self._empty_cells_in_cols = {}
        self._empty_cells_in_grids = {}
        self._related_cells = {}
        self._assignment = {}
        self._start_time = None

    def solve(self, board: list, start_time):
        self._reset()
        self._board = board
        self._size = len(self._board)
        self._find_empty_cells()
        self._find_related_cells()
        self._get_initial_domains()
        self._start_time = time.time()
        return self._fill_cell()

    def _find_empty_cells(self):
        self._empty_cells_in_rows = {row: set() for row in range(self._size)}
        self._empty_cells_in_cols = {col: set() for col in range(self._size)}
        self._empty_cells_in_grids = {grid: set() for grid in range(self._size)}
        subgrid_row = math.floor(self._size ** 0.5)
        subgrid_col = self._size // subgrid_row
        for row in range(self._size):
            for col in range(self._size):
                if self._board[row][col] == 0:
                    grid_index = col // subgrid_col + row // subgrid_row * (self._size // subgrid_col)
                    cell = Cell(row, col, grid_index)
                    self._empty_cells.add(cell)
                    self._empty_cells_in_rows[row].add(cell)
                    self._empty_cells_in_cols[col].add(cell)
                    self._empty_cells_in_grids[grid_index].add(cell)
                    self._assignment[cell] = 0

    def _get_initial_domains(self):
        for cell in self._empty_cells:
            row = cell.row
            col = cell.col
            self._domains[cell] = set(range(1, self._size + 1)) - set(self._board[row]) - \
                                  set([row[col] for row in self._board]) - set(self._get_subgrid(row, col))

    def _fill_cell(self):
        if time.time() - self._start_time > SOLVE_TIME_LIMIT:
            return False
        if len(self._empty_cells) == 0:
            return self._board
        cell = self._mrv()
        self._empty_cells.remove(cell)
        original_domains = {cell: domain.copy() for cell, domain in self._domains.items()}
        for value in self._arrange_value(cell):
            self._assignment[cell] = value
            self._domains[cell] = set()
            if self._ac_3(cell):
                if self._fill_cell():
                    self._board[cell.row][cell.col] = value
                    return self._board
            self._assignment[cell] = 0
            self._domains = original_domains
        self._empty_cells.add(cell)
        return False

    def _get_subgrid(self, row, col):
        subgrid_row = math.floor(self._size ** 0.5)
        subgrid_col = self._size // subgrid_row
        row_start = (row // subgrid_row) * subgrid_row
        col_start = (col // subgrid_col) * subgrid_col
        return [self._board[i][j] for i in range(row_start, row_start + subgrid_row) for j in
                range(col_start, col_start + subgrid_col)]

    def _mrv(self):
        mrv = set()
        min_domain_size = self._size
        for cell in self._empty_cells:
            domain_size = len(self._domains[cell])
            if domain_size == min_domain_size:
                mrv.add(cell)
            elif domain_size < min_domain_size:
                min_domain_size = domain_size
                mrv = {cell}
        if len(mrv) == 1:
            selected = next(iter(mrv))
            return selected

        return self._degree_heuristic(mrv)

    def _degree_heuristic(self, mrv):
        highest_degree = 0
        selected_cell = next(iter(mrv))
        for cell in mrv:
            degree = 0
            for related_cell in self._related_cells[cell]:
                if self._assignment[related_cell] == 0:
                    degree += 1
            if degree > highest_degree:
                highest_degree = degree
                selected_cell = cell
        return selected_cell

    def _arrange_value(self, cell):
        domains = self._domains[cell]
        if len(domains) == 1:
            return domains

        domain_count = Counter()
        domain_count.update(self._domains[cell])
        for related_cell in self._related_cells[cell]:
            domain_count.update(self._domains[related_cell])
        sorted_domains = sorted(domain_count.keys(), key=lambda key: domain_count[key])
        domains = [domain for domain in sorted_domains if domain in self._domains[cell]]
        return domains

    def _ac_3(self, cell):
        arcs = deque()
        for related_cell in self._related_cells[cell]:
            if self._assignment[related_cell] == 0:
                arcs.append((related_cell, cell))
        while arcs:
            arc = arcs.popleft()
            cell_i = arc[0]
            cell_j = arc[1]
            if self._revise(cell_i, cell_j):
                if not self._domains[cell_i]:
                    return False
                for related_cell in self._related_cells[cell_i]:
                    if self._assignment[related_cell] != cell_j:
                        arcs.append((related_cell, cell_i))
        return True

    def _revise(self, cell_i, cell_j):
        i_domains = self._domains[cell_i]
        j_domains = self._domains[cell_j]
        if not j_domains:
            j_assignment = self._assignment[cell_j]
            if j_assignment in i_domains:
                i_domains.remove(j_assignment)
                return True

        if len(j_domains) == 1 and len(i_domains) == 1:
            i_domain = next(iter(i_domains))
            if i_domain in j_domains:
                self._domains[cell_i].clear()
                return True
        return False

    def _find_related_cells(self):
        self._related_cells = {cell: set() for cell in self._empty_cells}
        for cell in self._empty_cells:
            self._related_cells[cell] = (self._empty_cells_in_rows[cell.row] | self._empty_cells_in_cols[cell.col] |
                                         self._empty_cells_in_grids[cell.grid])
            self._related_cells[cell].remove(cell)

    def _reset(self):
        self._board = []
        self._size = 0
        self._empty_cells = set()
        self._domains = {}
        self._empty_cells_in_rows = {}
        self._empty_cells_in_cols = {}
        self._empty_cells_in_grids = {}
        self._related_cells = {}
        self._assignment = {}
        self._start_time = None


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


def print_board(board):
    for row in board:
        for num in row:
            print(num, end=" ")
        print()


size_16_puzzle = [[0, 0, 0, 5, 0, 0, 1, 12, 0, 0, 0, 8, 0, 0, 15, 0],
                  [0, 0, 0, 0, 0, 0, 16, 0, 0, 0, 15, 0, 0, 5, 0, 0],
                  [0, 1, 9, 6, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 14],
                  [0, 0, 0, 0, 7, 0, 0, 0, 0, 1, 5, 0, 0, 0, 0, 0],
                  [10, 0, 6, 0, 0, 13, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0],
                  [0, 9, 0, 0, 0, 3, 0, 0, 0, 0, 0, 13, 14, 0, 1, 0],
                  [0, 0, 0, 15, 11, 1, 0, 0, 0, 3, 0, 9, 0, 0, 0, 0],
                  [1, 0, 13, 0, 0, 0, 0, 14, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0, 0, 0],
                  [0, 16, 0, 0, 10, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
                  [6, 0, 0, 11, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 9, 0],
                  [0, 0, 15, 0, 4, 12, 0, 0, 0, 0, 0, 0, 16, 2, 0, 1],
                  [15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 7, 11, 0, 0, 0, 0],
                  [0, 0, 0, 10, 12, 0, 14, 0, 9, 0, 0, 5, 0, 11, 0, 0],
                  [16, 5, 11, 0, 0, 0, 6, 7, 0, 0, 0, 1, 0, 0, 0, 0]]

size_25_puzzle_1 = [[0, 15, 0, 2, 1, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 14, 24, 0, 11, 0, 23, 1, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 12, 0, 2, 0, 0],
                    [0, 0, 7, 10, 0, 0, 0, 22, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 8, 9, 0, 0, 0, 0, 0],
                    [12, 0, 0, 0, 0, 0, 6, 0, 0, 0, 14, 0, 21, 24, 0, 1, 0, 0, 0, 0, 0, 0, 8, 0, 23],
                    [0, 0, 0, 0, 0, 16, 0, 0, 9, 0, 0, 0, 13, 18, 0, 0, 0, 0, 24, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 17, 0, 0, 0, 15, 0, 25, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 25, 0, 0, 0, 0, 0, 0, 0, 16, 0, 0, 0, 0, 0, 3, 0, 7, 0, 0],
                    [0, 0, 20, 0, 0, 0, 0, 0, 0, 0, 13, 0, 10, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 23, 0, 0, 24, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 20, 0, 0, 0, 6, 0, 0],
                    [0, 9, 24, 25, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 17, 12, 0],
                    [0, 0, 0, 3, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13, 0, 0],
                    [0, 0, 0, 11, 0, 20, 1, 0, 18, 3, 0, 0, 0, 7, 0, 24, 13, 25, 0, 0, 0, 2, 0, 0, 0],
                    [0, 0, 0, 18, 0, 2, 0, 0, 15, 6, 0, 10, 1, 0, 0, 0, 0, 0, 0, 11, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 6, 23, 11, 0, 0, 0, 18, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 12],
                    [23, 0, 0, 16, 0, 10, 0, 0, 0, 14, 0, 0, 0, 0, 15, 20, 4, 0, 18, 21, 0, 0, 0, 0, 3],
                    [0, 0, 0, 0, 3, 0, 0, 0, 0, 16, 23, 0, 0, 0, 0, 0, 0, 18, 13, 15, 22, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 20, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 24, 14, 0, 0, 15, 0],
                    [0, 0, 11, 13, 0, 21, 23, 0, 0, 18, 0, 0, 12, 22, 24, 0, 0, 6, 1, 0, 0, 0, 0, 0, 20],
                    [0, 5, 0, 0, 9, 0, 0, 0, 17, 0, 0, 0, 20, 0, 21, 14, 3, 11, 10, 0, 0, 0, 0, 0, 0],
                    [3, 22, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 20, 0, 0, 0, 0, 0],
                    [17, 0, 0, 0, 0, 0, 0, 0, 2, 1, 0, 16, 0, 0, 0, 0, 22, 0, 0, 0, 6, 0, 20, 3, 7],
                    [14, 0, 0, 0, 0, 17, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 12, 0, 0, 0, 21, 0, 0, 0, 0],
                    [8, 0, 0, 0, 7, 13, 0, 0, 0, 0, 0, 14, 0, 0, 0, 0, 0, 0, 0, 1, 0, 12, 11, 0, 2],
                    [0, 16, 0, 0, 0, 0, 0, 10, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 23, 5, 0]]

size_25_puzzle_2 = [[0, 0, 0, 0, 0, 9, 22, 0, 10, 4, 12, 11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 21, 0],
                    [0, 0, 0, 0, 0, 16, 17, 0, 18, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 11, 0, 0, 0, 0],
                    [14, 0, 0, 0, 0, 1, 0, 3, 5, 0, 0, 0, 0, 0, 0, 0, 0, 11, 0, 0, 0, 0, 0, 0, 17],
                    [0, 0, 0, 0, 0, 0, 0, 0, 21, 23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [11, 12, 0, 0, 23, 0, 0, 0, 0, 0, 0, 17, 0, 0, 0, 4, 0, 0, 0, 0, 0, 2, 0, 22, 25],
                    [2, 0, 0, 0, 4, 0, 18, 22, 0, 19, 0, 0, 0, 0, 7, 13, 0, 0, 0, 0, 20, 0, 0, 0, 8],
                    [0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 15, 0, 0, 0, 20, 0, 0, 0, 0, 21, 10, 11],
                    [0, 0, 0, 0, 0, 0, 0, 0, 23, 0, 0, 0, 9, 8, 0, 11, 0, 0, 0, 19, 0, 17, 0, 3, 12],
                    [7, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 22, 0, 0, 0, 3, 0, 0, 0, 19, 0, 0, 0],
                    [0, 0, 0, 0, 18, 0, 0, 8, 0, 0, 0, 0, 19, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0],
                    [9, 0, 0, 1, 3, 0, 0, 0, 14, 13, 25, 0, 0, 0, 6, 0, 0, 21, 0, 0, 0, 0, 0, 0, 5],
                    [0, 0, 0, 0, 0, 0, 23, 2, 3, 16, 0, 14, 0, 20, 0, 0, 0, 0, 13, 0, 0, 0, 0, 0, 7],
                    [0, 0, 0, 12, 0, 0, 0, 0, 0, 7, 0, 15, 0, 0, 13, 0, 17, 25, 0, 0, 18, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 20, 0, 6, 0, 0, 0, 1, 0, 0, 0, 15, 0, 0, 11, 16, 0, 0, 0, 19, 9],
                    [0, 14, 23, 0, 0, 0, 10, 0, 0, 0, 5, 7, 0, 17, 0, 0, 3, 0, 20, 0, 0, 0, 0, 13, 16],
                    [0, 0, 0, 2, 0, 0, 0, 0, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 0, 0],
                    [0, 0, 19, 0, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 21, 0, 0, 6],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25, 0, 19, 0, 0, 0, 22, 0, 0, 18],
                    [15, 24, 0, 5, 0, 0, 0, 7, 17, 0, 14, 0, 0, 0, 0, 0, 21, 0, 0, 0, 0, 13, 11, 25, 20],
                    [0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 17, 0, 5, 13, 0, 0, 6, 14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 18, 0, 0],
                    [13, 0, 11, 0, 0, 0, 0, 0, 24, 2, 0, 19, 0, 0, 0, 0, 0, 0, 0, 0, 0, 14, 0, 0, 22],
                    [0, 0, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0, 24, 0, 2, 0, 25, 0, 0, 0, 10, 0, 0, 0, 0],
                    [0, 0, 0, 16, 0, 0, 4, 0, 0, 0, 0, 18, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0],
                    [23, 18, 0, 0, 12, 0, 0, 10, 0, 0, 0, 0, 0, 0, 0, 9, 0, 13, 0, 0, 0, 0, 0, 0, 2]]

size_25_puzzle_3 = [[0, 0, 0, 22, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25, 0, 0, 0, 20, 0, 5, 0, 0, 0],
                    [0, 0, 0, 0, 20, 0, 0, 17, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25],
                    [0, 0, 0, 0, 0, 0, 0, 0, 23, 0, 0, 0, 0, 0, 11, 0, 0, 0, 0, 3, 0, 10, 0, 0, 0],
                    [0, 14, 0, 23, 24, 25, 0, 6, 0, 0, 0, 0, 0, 4, 0, 2, 0, 0, 21, 0, 11, 0, 0, 8, 0],
                    [0, 8, 0, 0, 12, 0, 0, 13, 14, 0, 25, 0, 0, 0, 21, 0, 5, 0, 0, 24, 0, 0, 0, 0, 20],
                    [0, 0, 0, 0, 0, 6, 0, 0, 0, 4, 0, 0, 0, 20, 5, 0, 0, 0, 0, 0, 21, 0, 0, 0, 0],
                    [0, 0, 9, 0, 6, 0, 0, 8, 3, 0, 0, 25, 0, 0, 0, 15, 0, 0, 0, 5, 19, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 17, 0, 0, 0],
                    [4, 22, 8, 0, 0, 20, 24, 5, 0, 0, 16, 3, 0, 0, 0, 0, 0, 0, 0, 6, 0, 23, 0, 25, 0],
                    [18, 25, 0, 0, 0, 0, 7, 0, 19, 14, 0, 0, 0, 0, 0, 3, 0, 0, 9, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 17, 0, 0, 3, 0, 0, 0, 15, 0, 22, 0, 0, 4, 0, 16, 0, 0, 0, 0],
                    [12, 7, 16, 5, 0, 2, 18, 1, 9, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 25, 19, 0, 0],
                    [0, 0, 0, 0, 0, 7, 0, 0, 8, 5, 0, 6, 0, 12, 0, 13, 0, 0, 0, 0, 0, 0, 0, 0, 15],
                    [0, 0, 0, 0, 0, 24, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 20, 0],
                    [0, 15, 19, 0, 0, 11, 0, 0, 0, 0, 0, 0, 0, 25, 0, 0, 0, 9, 0, 0, 24, 0, 0, 0, 0],
                    [0, 23, 0, 0, 0, 14, 0, 0, 0, 0, 0, 0, 0, 0, 10, 7, 0, 20, 0, 0, 0, 0, 0, 0, 16],
                    [0, 0, 0, 12, 0, 0, 8, 20, 0, 2, 0, 0, 0, 7, 23, 0, 0, 0, 0, 0, 0, 3, 0, 0, 5],
                    [0, 9, 0, 0, 0, 0, 25, 0, 0, 17, 0, 0, 0, 0, 0, 16, 0, 0, 8, 15, 0, 0, 0, 12, 0],
                    [0, 17, 5, 0, 0, 9, 0, 0, 0, 0, 0, 18, 0, 0, 0, 0, 23, 0, 0, 0, 0, 0, 0, 21, 0],
                    [0, 0, 15, 0, 0, 21, 5, 0, 24, 23, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 22, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13, 0, 0, 0, 21],
                    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 16, 0, 0, 0, 0, 0, 0, 4],
                    [0, 12, 23, 0, 0, 0, 0, 0, 20, 25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 10, 0, 0],
                    [0, 21, 0, 25, 0, 8, 0, 0, 0, 22, 4, 11, 0, 0, 0, 0, 0, 0, 0, 1, 12, 0, 7, 0, 0],
                    [0, 0, 0, 0, 18, 0, 0, 4, 5, 7, 0, 0, 9, 0, 0, 0, 22, 6, 0, 0, 0, 0, 0, 0, 0]]

if __name__ == "__main__":
    solver1 = BruteForceSolver()
    solver2 = CSPSolver()
    attempts = 100
    for solver in [solver1, solver2]:
        success = 0
        total_time = 0
        for n in range(attempts):
            generator = SudokuGenerator(16)
            # puzzle = [row[:] for row in size_16_puzzle]
            puzzle = generator.generate()
            current_time = time.time()
            solution = solver.solve(puzzle, current_time)
            if solution:
                time_elapsed = time.time() - current_time
                total_time += time_elapsed
                success += 1
                solver.recursion_count = 0
                # print(puzzle)
                print("SUCCESS!!!")
            else:
                print("FAIL!!!")
                # print(puzzle)
        print(f"Success rate: {success / attempts}")
        print(f"Average time: {total_time / success}")
