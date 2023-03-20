import math
import random
import time
from collections import deque

from frontend.sudoku_generator import SudokuGenerator

SOLVE_TIME_LIMIT = 5


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
        self._empty_cells = []
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
                    self._empty_cells.append(cell)
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
        if not self._empty_cells:
            return self._board
        cell = self._mrv()
        self._empty_cells.remove(cell)
        for value in self._arrange_value(cell):
            self._assignment[cell] = value
            # TODO: Optimize this
            original_domains = {cell: set() | domain for cell, domain in self._domains.items()}
            self._domains[cell] = set()
            if self._ac_3(cell):
                if self._fill_cell():
                    self._board[cell.row][cell.col] = value
                    return self._board
            self._assignment[cell] = 0
            self._domains = original_domains
        self._empty_cells.append(cell)
        return False

    def _get_subgrid(self, row, col):
        subgrid_row = math.floor(self._size ** 0.5)
        subgrid_col = self._size // subgrid_row
        row_start = (row // subgrid_row) * subgrid_row
        col_start = (col // subgrid_col) * subgrid_col
        return [self._board[i][j] for i in range(row_start, row_start + subgrid_row) for j in
                range(col_start, col_start + subgrid_col)]

    def _mrv(self):
        mrv = [self._empty_cells[0]]
        min_domain_size = len(self._domains[self._empty_cells[0]])
        for cell in self._empty_cells:
            domain_size = len(self._domains[cell])
            if domain_size == min_domain_size:
                mrv.append(cell)
            elif domain_size < min_domain_size:
                min_domain_size = domain_size
                mrv = [cell]
        return self._degree_heuristic(mrv)

    def _degree_heuristic(self, mrv):
        highest_degree = 0
        selected_cell = None
        for cell in mrv:
            degree = 0
            for related_cell in self._related_cells[cell]:
                if self._assignment[related_cell] == 0:
                    continue
                degree += 1
            if degree >= highest_degree:
                highest_degree = degree
                selected_cell = cell
        return selected_cell

    def _arrange_value(self, cell):
        return self._domains[cell]
        # domain_count = {domain: 0 for domain in self._domains[cell]}
        # domains_set = self._domains[cell]
        # for related_cell in self._related_cells[cell]:
        #     for domain in domains_set:
        #         if domain in self._domains[related_cell]:
        #             domain_count[domain] += 1
        # counts = sorted(domain_count.keys(), key=lambda key: domain_count[key])
        # return counts

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
            i_domain = iter(i_domains)
            if i_domain in j_domains:
                self._domains[cell_i] = set()
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
        self._empty_cells = []
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


size_9_puzzle = [[0, 0, 0, 5, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0, 0],
                 [8, 0, 0, 0, 2, 4, 5, 0, 1],
                 [0, 0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 7, 8, 0, 0, 0],
                 [9, 0, 8, 4, 0, 0, 0, 0, 0],
                 [0, 0, 0, 8, 0, 0, 7, 1, 9],
                 [1, 0, 0, 0, 0, 9, 4, 0, 0],
                 [0, 0, 0, 7, 4, 0, 0, 0, 0]]

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

size_25_puzzle = [[0, 0, 0, 0, 0, 9, 22, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 17, 1, 0, 23, 0, 20, 0, 0],
                  [0, 2, 4, 9, 0, 0, 0, 0, 18, 0, 0, 0, 0, 0, 0, 0, 0, 23, 0, 0, 0, 0, 0, 14, 15],
                  [14, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 23, 0, 0, 7, 0, 0, 0, 0, 0, 9, 0, 0, 17],
                  [0, 17, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 6, 0, 15, 18, 0, 0, 0, 0, 0, 0],
                  [11, 0, 0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 0, 0, 20, 0, 0, 0, 0, 5, 1, 0, 0, 0, 0],
                  [2, 16, 0, 0, 0, 0, 0, 0, 0, 19, 11, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 23, 15, 0, 0],
                  [0, 0, 17, 14, 0, 0, 0, 0, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 0, 21, 0, 0],
                  [0, 0, 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 24, 0, 0, 19, 0, 17, 22, 0, 0],
                  [0, 0, 0, 0, 0, 25, 0, 0, 0, 0, 10, 20, 17, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 13],
                  [12, 0, 0, 0, 0, 0, 11, 8, 0, 0, 0, 0, 0, 3, 24, 0, 0, 0, 0, 22, 2, 0, 0, 0, 14],
                  [0, 4, 0, 0, 0, 18, 0, 0, 14, 13, 25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 12, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 24, 0, 2, 11, 0, 19, 17, 0, 0, 0, 18, 3, 0, 0, 10],
                  [0, 0, 0, 0, 17, 0, 0, 0, 22, 0, 0, 1, 0, 0, 4, 0, 0, 0, 0, 0, 0, 8, 0, 0, 9],
                  [0, 14, 0, 0, 0, 0, 10, 0, 0, 0, 0, 7, 12, 0, 0, 0, 3, 0, 20, 4, 0, 0, 2, 0, 0],
                  [3, 0, 0, 0, 0, 0, 20, 16, 0, 10, 0, 25, 0, 6, 0, 14, 0, 0, 0, 0, 0, 15, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                  [4, 23, 0, 0, 0, 0, 0, 15, 0, 0, 0, 0, 0, 0, 0, 25, 0, 19, 8, 10, 17, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 13, 0, 0, 0],
                  [0, 0, 0, 0, 0, 23, 0, 0, 0, 0, 7, 8, 15, 0, 0, 0, 0, 4, 0, 11, 0, 0, 0, 2, 0],
                  [0, 1, 0, 0, 2, 17, 15, 0, 0, 0, 0, 0, 0, 0, 11, 0, 0, 8, 10, 0, 0, 0, 0, 0, 0],
                  [0, 25, 0, 10, 0, 0, 0, 12, 0, 0, 0, 19, 0, 23, 0, 0, 0, 7, 0, 1, 9, 0, 0, 4, 0],
                  [0, 0, 0, 20, 0, 0, 14, 0, 0, 0, 0, 13, 24, 0, 0, 17, 0, 0, 0, 12, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 21, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0],
                  [0, 0, 15, 0, 0, 21, 0, 10, 20, 0, 0, 0, 0, 0, 0, 9, 0, 13, 0, 0, 0, 0, 19, 5, 2]]

if __name__ == "__main__":
    solver1 = BruteForceSolver()
    solver2 = CSPSolver()
    attempts = 1000
    for solver in [solver1, solver2]:
        success = 0
        total_time = 0
        for n in range(attempts):
            generator = SudokuGenerator(9)
            puzzle = generator.generate()
            puzzle = [row[:] for row in puzzle]
            current_time = time.time()
            solution = solver.solve(puzzle, current_time)
            if solution:
                time_elapsed = time.time() - current_time
                total_time += time_elapsed
                success += 1
                solver.recursion_count = 0
                # print_board(solution)
                # print("SUCCESS!!!")
            else:
                # print("FAIL!!!")
                print(puzzle)
        print(f"Success rate: {success / attempts}")
        print(f"Average time: {total_time / success}")
