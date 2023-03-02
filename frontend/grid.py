import enum
from dataclasses import dataclass
from math import sqrt, floor
from typing import TextIO

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFrame

from custom_exceptions import InvalidFileDataException


@dataclass
class GridSize(enum.Enum):
    __order__ = "NINE TWELVE SIXTEEN TWENTY_FIVE HUNDRED"
    NINE = {"blocks": 9, "block_rows": 3, "block_cols": 3}
    TWELVE = {"blocks": 12, "block_rows": 3, "block_cols": 4}
    SIXTEEN = {"blocks": 16, "block_rows": 4, "block_cols": 4}
    TWENTY_FIVE = {"blocks": 25, "block_rows": 5, "block_cols": 5}
    HUNDRED = {"blocks": 100, "block_rows": 10, "block_cols": 10}


class Cell:
    def __init__(self, row, col, block_row, block_col, value):
        self.value = value
        self.row = row
        self.col = col
        self.block_row = block_row
        self.block_col = block_col
        self.label_widget = QLabel(str(self.value))
        self.label_widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        if self.value is None:
            self.label_widget.setStyleSheet("background-color:#F5F5F5;")
        else:
            self.label_widget.setStyleSheet("background-color:#989898;")
        self.label_widget.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.label_widget.wordWrap()


class Block:
    def __init__(self, grid_size, block_num):
        self.block_num = block_num
        self.cells = []
        self.grid_size = grid_size
        self.row = int(block_num / (self.grid_size["block_cols"]))
        self.col = block_num % (self.grid_size["block_cols"])

    def generate(self):
        for i in range(self.row * self.grid_size["block_rows"],
                       self.row * self.grid_size["block_rows"] + self.grid_size["block_rows"]):
            for j in range(self.col * self.grid_size["block_cols"],
                           self.col * self.grid_size["block_cols"] + self.grid_size["block_cols"]):
                # [TODO] Put generate puzzle logic here and assign values to cells
                self.cells.append(Cell(row=i,
                                       col=j,
                                       block_row=i - (self.row * self.grid_size["block_rows"]),
                                       block_col=j - (self.col * self.grid_size["block_cols"]),
                                       value=(i, j)))

    def load(self, sudoku_line: str):
        """
        Load a single sudoku puzzle to a block of cells.

        :param sudoku_line: sudoku puzzle
        """
        line_index = 0
        for i in range(self.row * self.grid_size["block_rows"],
                       self.row * self.grid_size["block_rows"] + self.grid_size["block_rows"]):
            for j in range(self.col * self.grid_size["block_cols"],
                           self.col * self.grid_size["block_cols"] + self.grid_size["block_cols"]):
                self.cells.append(Cell(row=i,
                                       col=j,
                                       block_row=i - (self.row * self.grid_size["block_rows"]),
                                       block_col=j - (self.col * self.grid_size["block_cols"]),
                                       value=self.__get_value(sudoku_line[line_index])))
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
    def __init__(self):
        self.blocks = []
        self.grid_size = None

    def generate(self, grid_size):
        self.grid_size = grid_size.value
        for i in range(0, self.grid_size["blocks"]):
            block = Block(self.grid_size, i)
            block.generate()
            self.blocks.append(block)

        # for block in self.blocks:
        #     print(f"Block {block.block_num}: {block.row}, {block.col}")
        #     for cell in block.cells:
        #         print(f"{cell.row}, {cell.col}")

    def load(self, filename):
        """
        Load all the sudoku puzzles in the given file if it's valid

        :param filename: valid filepath
        :raises: InvalidFileDataException if the given file can't be used to parse sudoku puzzles
        """
        with open(filename, "r", encoding="utf-8") as sudoku_grids:
            line = sudoku_grids.readline()
            if line == "":
                raise InvalidFileDataException(filename)
            try:
                if '.' in line:
                    self.__load_linearly(sudoku_grids, line)
                else:
                    self.__load_column_by_row(sudoku_grids, line)
            except IndexError:
                raise InvalidFileDataException(filename)

    def __load_linearly(self, file_content: TextIO, first_line: str):
        """
        Load sudoku puzzles from a file in the linear form of "4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......".

        :param file_content: TextIO
        :param first_line: str
        """
        grid_size = len(first_line.strip('\n'))
        side = floor(sqrt(grid_size))
        self.grid_size = {"blocks": grid_size, "block_rows": side, "block_cols": side}
        first_block = Block(self.grid_size, 0)
        first_block.load(first_line)
        self.blocks.append(first_block)
        for block_number, line in enumerate(file_content, start=1):
            block = Block({"blocks": grid_size, "block_rows": side, "block_cols": side}, block_number)
            block.load(line.strip('\n'))
            self.blocks.append(block)

    def __load_column_by_row(self, file_content: TextIO, first_line):
        """
        Load sudoku puzzles from a file in the linear form of
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
        line = file_content.readline()
        block_number = 0
        while line != "":
            while line != "" and '=' not in line:
                first_line += line.strip('\n')
                line = file_content.readline()
            block = Block(self.grid_size, block_number)
            block.load(first_line)
            self.blocks.append(block)
            first_line = ""
            line = file_content.readline()
            block_number += 1
