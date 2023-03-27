import enum
from dataclasses import dataclass
from math import sqrt, floor
from typing import TextIO, Dict, Union

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFrame
from typing import List

from custom_exceptions import InvalidFileDataException
# from frontend.sudoku_generator import SudokuGenerator
from sudoku_generator import SudokuGenerator

from textwrap import wrap


@dataclass
class GridSize(enum.Enum):
    __order__ = "_9X9 _12X12 _16X16 _25X25 _100X100"
    _9X9 = {"blocks": 9, "block_rows": 3, "block_cols": 3, "description": "9 X 9"}
    _12X12 = {"blocks": 12, "block_rows": 3, "block_cols": 4, "description": "12 X 12"}
    _16X16 = {"blocks": 16, "block_rows": 4, "block_cols": 4, "description": "16 X 16"}
    _25X25 = {"blocks": 25, "block_rows": 5, "block_cols": 5, "description": "25 X 25"}
    _100X100 = {"blocks": 100, "block_rows": 10, "block_cols": 10, "description": "100 X 100"}


class Cell:
    def __init__(self, row, col, block_row, block_col, value):
        self.value = value
        self.row = row
        self.col = col
        self.block_row = block_row
        self.block_col = block_col
        self.label_widget = QLabel(str(self.value))
        self.label_widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        if self.value == "":
            self.label_widget.setStyleSheet("background-color:#F5F5F5;")
        else:
            self.label_widget.setStyleSheet("background-color:#989898;")
        self.label_widget.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.label_widget.wordWrap()

    def __str__(self):
        result = f"Cell(Value={self.value}, Row={self.row}, Column={self.col})\n"
        return result


class Block:
    cells: List[Cell]

    def __init__(self, grid_size, block_num):
        self.block_num = block_num
        self.cells = []
        self.grid_size = grid_size
        self.row = int(block_num / (self.grid_size["block_rows"]))
        self.col = block_num % (self.grid_size["block_rows"])

    def __str__(self):
        result = f"Block(Row={self.row}, Column={self.col})\n"
        for cell in self.cells:
            result += cell.__str__()
        return result

    def generate(self, puzzle):
        for i in range(self.row * self.grid_size["block_rows"],
                       self.row * self.grid_size["block_rows"] + self.grid_size["block_rows"]):
            for j in range(self.col * self.grid_size["block_cols"],
                           self.col * self.grid_size["block_cols"] + self.grid_size["block_cols"]):
                # [TODO] Put generate puzzle logic here and assign values to cells
                self.cells.append(Cell(row=i,
                                       col=j,
                                       block_row=i - (self.row * self.grid_size["block_rows"]),
                                       block_col=j - (self.col * self.grid_size["block_cols"]),
                                       value=puzzle[i][j] if puzzle[i][j] != 0 else ""))

    def load(self, sudoku_line, puzzle):
        """
        Load a single sudoku puzzle to a block of cells.

        :param puzzle: updating the list inside this method cuz otherwise would need to rework the entire logic
        :param sudoku_line: str or list[str]
        """
        line_index = 0
        for i in range(self.row * self.grid_size["block_rows"],
                       self.row * self.grid_size["block_rows"] + self.grid_size["block_rows"]):
            for j in range(self.col * self.grid_size["block_cols"],
                           self.col * self.grid_size["block_cols"] + self.grid_size["block_cols"]):
                val = self.__get_value(sudoku_line[line_index])
                puzzle[self.block_num][j] = 0 if val == "" else int(val)
                self.cells.append(Cell(row=i,
                                       col=j,
                                       block_row=i - (self.row * self.grid_size["block_rows"]),
                                       block_col=j - (self.col * self.grid_size["block_cols"]),
                                       value=val))
                line_index += 1

    @staticmethod
    def __get_value(character: str) -> str:
        """
        Return a numeric str if the given string is valid sudoku cell value, else empty str.

        :param character: str
        :return: str
        """
        if character == '.' or character == '0':
            return ""
        else:
            return character


class Grid:
    blocks: List[Block]
    puzzle: list
    # grid_size: GridSize
    grid_size: Dict[str, int]

    def __init__(self, grid_size: Union[GridSize, Dict[str, int], None], puzzle=None):
        self.blocks = []
        if isinstance(grid_size, GridSize):
            self.grid_size = grid_size.value
        else:
            self.grid_size = grid_size
        if puzzle is None and self.grid_size is not None:
            puzzle_generator = SudokuGenerator(self.grid_size["blocks"])
            self.puzzle = puzzle_generator.generate()
        else:
            self.puzzle = puzzle

    def __str__(self):
        result = "Grid\n"
        for block in self.blocks:
            result += block.__str__() + "\n"
        return result

    def clone(self, puzzle=None):
        if puzzle is None:
            puzzle = [row[:] for row in self.puzzle]

        if self.grid_size is None:
            raise ValueError("Error - Grid Size is none can't copy this grid")
        new_grid = Grid(self.grid_size, puzzle)
        new_grid.generate()
        return new_grid

    def generate(self):
        for i in range(0, self.grid_size["blocks"]):
            block = Block(self.grid_size, i)
            block.generate(self.puzzle)
            self.blocks.append(block)

        # for block in self.blocks:
        #     print(f"Block {block.block_num}: {block.row}, {block.col}")
        #     for cell in block.cells:
        #         print(f"{cell.row}, {cell.col}")

    def load(self, filename):
        """
        Load all sudoku puzzles in the given file if it's valid

        :param filename: valid filepath
        :raises: InvalidFileDataException if the given file can't be used to parse sudoku puzzles
        """
        with open(filename, "r", encoding="utf-8") as sudoku_grids:
            line = sudoku_grids.readline()
            if line == "":
                raise InvalidFileDataException(filename)
            try:
                if ',' in line:
                    self.__load_with_commas(sudoku_grids, line)
                elif '.' in line:
                    self.__load_linearly(sudoku_grids, line)
                else:
                    self.__load_column_by_row(sudoku_grids, line)
            except IndexError:
                raise InvalidFileDataException(filename)

    def __load_with_commas(self, file_content: TextIO, first_line: str):
        """

        :param file_content: TextIO
        :param first_line: str
        """
        side = len(first_line.strip('\n').replace(',', ''))
        grid_size = side * side
        first_line_values = first_line.strip('\n').split(',')
        self.grid_size = {"blocks": grid_size, "block_rows": side, "block_cols": side}
        self.puzzle = [[0] * side for _ in range(side)]
        line = file_content.readline()
        while line != "" and '=' not in line:
            first_line_values += line.strip('\n').split(',')
            line = file_content.readline()
        block = Block(self.grid_size, 0)
        block.load(first_line_values, self.puzzle)
        self.blocks.append(block)

    def __load_linearly(self, file_content: TextIO, first_line: str):
        """
        Load sudoku puzzles from a file written in the linear form
        "4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......".

        :param file_content: TextIO
        :param first_line: str
        """
        grid_size = len(first_line.strip('\n'))
        side = floor(sqrt(grid_size))
        self.grid_size = {"blocks": grid_size, "block_rows": side, "block_cols": side}
        self.puzzle = [[0] * side for _ in range(side)]
        first_block = Block(self.grid_size, 0)
        first_block.load(first_line, self.puzzle)
        self.blocks.append(first_block)

    def __load_column_by_row(self, file_content: TextIO, first_line):
        """
        Load sudoku puzzles from a file in the linear form.
        "
        003020600
        900305001
        001806400
        008102900
        700000008
        006708200
        002609500
        800203009
        005010300
        ========
        "

        :param file_content: TextIO
        :param first_line: str
        """
        first_line = first_line.strip('\n')
        side = len(first_line)
        grid_size = side * side
        self.grid_size = {"blocks": grid_size, "block_rows": side, "block_cols": side}
        self.puzzle = [[0] * side for _ in range(side)]
        line = file_content.readline()
        while line != "" and '=' not in line:
            first_line += line.strip('\n')
            line = file_content.readline()
        block = Block(self.grid_size, 0)
        block.load(first_line, self.puzzle)
        self.blocks.append(block)
