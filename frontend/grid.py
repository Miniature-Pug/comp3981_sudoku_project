import enum
from dataclasses import dataclass

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

    def load(self, filename):
        # [TODO] Do something with the file, read it, and extract value for each cell
        for i in range(self.row * self.grid_size["block_rows"],
                       self.row * self.grid_size["block_rows"] + self.grid_size["block_rows"]):
            for j in range(self.col * self.grid_size["block_cols"],
                           self.col * self.grid_size["block_cols"] + self.grid_size["block_cols"]):
                # [TODO] Put load puzzle logic here and assign values to cells
                self.cells.append(Cell(row=i,
                                       col=j,
                                       block_row=i - (self.row * self.grid_size["block_rows"]),
                                       block_col=j - (self.col * self.grid_size["block_cols"]),
                                       value=(i, j)))


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
        # [TODO] Do something with the file such that we can get the gridSize. For ex: 9, 12, 25, 100
        # based on this number, we can find the relevant enum
        n = 25  # set as constant for now until there's file handling logic

        for gs in GridSize:
            if gs.value["blocks"] == n:
                self.grid_size = gs.value
                break

        if self.grid_size is None:
            raise InvalidFileDataException(filename)
        else:
            for i in range(0, self.grid_size["blocks"]):
                block = Block(self.grid_size, i)
                block.load(filename)
                self.blocks.append(block)

            # for block in self.blocks:
            #     print(f"Block {block.block_num}: {block.row}, {block.col}")
            #     for cell in block.cells:
            #         print(f"{cell.row}, {cell.col}")
