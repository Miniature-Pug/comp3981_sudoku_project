import sys

from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QMessageBox

import custom_exceptions
import dll
import generatepuzzle
import generatepuzzledialog
import mainwindow
import loadedsudokuwindow
from grid import Grid, GridSize

Global_Window_DLL = dll.DoublyLinkedList()


class MainWindow(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButtonCreatePuzzle.clicked.connect(self.on_click_create)
        self.pushButtonExit.clicked.connect(self.on_click_exit)
        self.actionExit.triggered.connect(self.on_click_exit)

    def on_click_create(self):
        Global_Window_DLL.append(GeneratePuzzleWindow())
        node = Global_Window_DLL.get_node(self)
        node.next.data.show()
        node.data.hide()
        Global_Window_DLL.print()

    def on_click_exit(self):
        node = Global_Window_DLL.get_node(self)
        node.data.close()
        Global_Window_DLL.delete(self)
        Global_Window_DLL.print()
        sys.exit(0)


class GeneratePuzzleWindow(QtWidgets.QMainWindow, generatepuzzle.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.grid = None
        self.pushButtonGeneratePuzzle.clicked.connect(self.on_click_generate)
        self.pushButtonLoadPuzzle.clicked.connect(self.on_click_load)
        self.pushButtonGoBack.clicked.connect(self.on_click_go_back)
        self.incorrect_file_format_dialog = None
        self.generate_puzzle_dialog = None

    def on_click_load(self):
        filename = QtWidgets.QFileDialog.getOpenFileNames(self, caption="Choose a TXT puzzle to load",
                                                          dir="./", filter="Text files (*.txt)")

        """
        # [TODO] Some logic that determines if the file format is correct/data inside the file is correct? If it's not,
        # [TODO] the raised exception is displayed in a dialog box. Set the text of the dialog box by
        """

        if len(filename[0]) != 0:  # make sure user didn't press 'cancel'
            try:
                self.grid = Grid()
                self.grid.load(filename[0][0])
            except custom_exceptions.InvalidFileDataException as e:
                QMessageBox.critical(self, e.__class__.__name__, e.args[0])
            else:
                Global_Window_DLL.append(LoadedSudokuWindow(self.grid))
                node = Global_Window_DLL.get_node(self)
                node.next.data.show()
                node.data.hide()

    def on_click_generate(self):
        self.generate_puzzle_dialog = GeneratePuzzleDialog(self)
        self.generate_puzzle_dialog.exec()

    def on_click_go_back(self):
        node = Global_Window_DLL.get_node(self)
        node.prev.data.show()
        node.data.close()
        Global_Window_DLL.delete(self)


class GeneratePuzzleDialog(generatepuzzledialog.Ui_Dialog, QDialog):
    def __init__(self, parent=None):
        self.parent = parent
        super().__init__(self.parent)
        self.grid = None
        self.setupUi(self)
        self.sudokuSizeSelector.addItems([grid_size.name for grid_size in GridSize])
        self.buttonBox.accepted.connect(self.on_click_ok)

    def on_click_ok(self):
        grid_size = self.sudokuSizeSelector.currentText()
        self.grid = Grid()
        try:
            self.grid.generate(GridSize[str(grid_size)])
        except KeyError as e:
            QMessageBox.critical(self, e.__class__.__name__, "Can't select Empty Grid Size!!")
        else:
            Global_Window_DLL.append(LoadedSudokuWindow(self.grid))
            node = Global_Window_DLL.get_node(self.parent)
            node.next.data.show()
            node.data.hide()


class LoadedSudokuWindow(QtWidgets.QMainWindow, loadedsudokuwindow.Ui_MainWindow):
    def __init__(self, grid):
        super().__init__()
        self.grid = grid
        self.setupUi(self)
        self.pushButtonBack.clicked.connect(self.on_click_go_back)
        self.pushButtonExit.clicked.connect(self.on_click_exit)

    def on_click_go_back(self):
        node = Global_Window_DLL.get_node(self)
        node.prev.data.show()
        node.data.close()
        Global_Window_DLL.delete(self)

    def on_click_exit(self):
        node = Global_Window_DLL.get_node(self)
        temp = node
        while temp.prev is not None:
            temp.data.close()
            temp = temp.prev
            Global_Window_DLL.delete(temp.next.data)
        temp.data.close()
        Global_Window_DLL.delete(temp.data)


class Driver:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)

        main_window = MainWindow()
        Global_Window_DLL.append(main_window)
        main_window.show()

        self.app.exec()


d = Driver()
