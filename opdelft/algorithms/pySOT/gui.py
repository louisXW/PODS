"""
.. module:: gui
  :synopsis: A Graphical User Interface for pySOT

.. moduleauthor:: David Eriksson <dme65@cornell.edu>

:Module: gui
:Author: David Eriksson <dme65@cornell.edu>

"""

import sys

import ntpath
import imp
import os
import numpy as np
import importlib
from poap.controller import *
from poap.strategy import *
import time
from pySOT.sot_sync_strategies import *
from pySOT.experimental_design import *
from pySOT.rs_wrappers import RSCapped
from pySOT.adaptive_sampling import *
from pySOT.ensemble_surrogate import *
from pySOT.rbf import *
from pySOT.utils import check_opt_prob\

try:
    from pySOT.mars_interpolant import MARSInterpolant
except ImportError as err:
    pass

import logging
ntpath.basename("a/b/c")

from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class TimerThread(QtCore.QThread):
    time_elapsed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(TimerThread, self).__init__(parent)
        self.time_start = None

    def start(self, time_start):
        self.time_start = time_start

        return super(TimerThread, self).start()

    def run(self):
        while self.parent().isRunning():
            self.time_elapsed.emit(time.time() - self.time_start)
            time.sleep(1)


class MyThread(QtCore.QThread):
    time_elapsed = QtCore.pyqtSignal(int)
    run_timer = False

    def __init__(self, parent=None):
        super(MyThread, self).__init__(parent)

        self.timer_thread = TimerThread(self)
        self.timer_thread.time_elapsed.connect(self.time_elapsed.emit)

    def run(self):
        self.timer_thread.start(time.time())

        while self.run_timer:
            time.sleep(1)

# ======================= Dynamic Plot Update =======================


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=6, height=4, dpi=200):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.figure.add_subplot(111)
        self.pts = None
        self.lines = None
        self.min_x = None
        self.max_x = None

        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)

        FigureCanvas.updateGeometry(self)

    def on_launch(self, min_x, max_x):
        self.pts, = self.ax.plot([], [], 'bo', markersize=3)  # Points
        self.lines, = self.ax.plot([], [], 'r-', linewidth=2.0)  # Lines
        self.ax.set_xlim(min_x, max_x)
        self.ax.grid()
        self.min_x = min_x
        self.max_x = max_x
        self.draw()

    def on_running(self, xdata, ydata):
        self.lines.set_xdata(xdata)
        ycummin = np.minimum.accumulate(ydata)
        self.lines.set_ydata(ycummin)
        ymin = np.amin(ycummin)
        ymax = np.amax(ycummin)
        if ymin == ymax:
            ymax += 1
        self.ax.set_ylim(ymin - 0.1*(ymax - ymin), ymax + 0.1*(ymax - ymin))
        self.pts.set_xdata(xdata)
        self.pts.set_ydata(ydata)
        self.ax.relim()
        self.ax.autoscale_view()
        self.draw()


class DynamicPlot(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.title = 'Progress plot'
        self.width = 600
        self.height = 400
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.m = PlotCanvas(self, width=6, height=4)
        self.m.move(0, 0)
        self.show()

    # We don't want the user accidentally to close this window
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# ============================= Helpers =============================


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def path_head(path):
    head, tail = ntpath.split(path)
    return head


def get_object(module_name, object_name):
    """return method object or class object given their names"""
    module = importlib.import_module(module_name)
    obj = getattr(module, object_name)
    return obj


def isfloat(value):
    try:
        float(value)
        return True
    except:
        return False

# ========== Manage communication with the strategy and the GUI ============


class Manager(InputStrategy):

    def __init__(self, controller, maxeval, feasible_merit, plot_progress):
        strategy = controller.strategy
        InputStrategy.__init__(self, controller, strategy)
        self.controller.strategy = self
        self.GUI = None
        self.numeval = 0
        self.killed = 0
        self.plot_progress = plot_progress
        self.feasible_merit = feasible_merit
        if self.plot_progress:
            self.dynamic_plot = DynamicPlot()
            self.dynamic_plot.m.on_launch(0, maxeval)
            self.xdata = np.arange(0, maxeval)
            self.ydata = np.nan * np.ones(maxeval,)

    def notify(self, msg):
        pass

    def on_complete(self, rec):
        self.numeval += 1
        rec.value = self.feasible_merit(rec)
        self.GUI.update(rec.params[0], rec.value, self.numeval, self.killed)
        print('Evaluation: {0}'.format(self.numeval))
        print('\tParams: {0}'.format(np.array_str(rec.params[0], max_line_width=np.inf,
                                                  precision=5, suppress_small=True)))
        print('\tValue: {0}'.format(rec.value))

        # Plot
        if self.plot_progress:
            self.ydata[self.numeval-1] = self.feasible_merit(rec)
            self.dynamic_plot.m.on_running(self.xdata[:self.numeval], self.ydata[:self.numeval])

    def on_kill(self, rec):
        self.killed += 1

    def on_terminate(self, rec):
        self.GUI.printMessage("Optimization finished\n", "green")

    def run(self, GUI):
        self.GUI = GUI
        result = self.controller.run(merit=self.feasible_merit)
        if result is None:
            self.GUI.printMessage("No result", "red")
        else:
            self.GUI.printMessage("Best value: " + str(result.value) + "\n", "blue")
            self.GUI.printMessage('Best solution: {0}\n'.format(
                np.array_str(result.params[0], max_line_width=80, precision=5, suppress_small=True)), "blue")

# ================================= GUI ===================================


class myGUI(QtWidgets.QWidget):

    def __init__(self):
        # Constructor
        super(myGUI, self).__init__()

        self.numeval = 0
        self.numfail = 0
        self.objfun = None
        self.external = False

        # Run params
        self.fbest = np.inf
        self.feasible = True
        self.xbest = None

        self.data = None
        self.nthreads = 4
        self.maxeval = 1000
        self.nsample = 4
        self.penalty = None

        self.exp_des = None
        self.con_hand = None
        self.rs = None

        # Input check
        self.datainp = False
        self.threadinp = True
        self.penaltyinp = False
        self.evalinp = True
        self.siminp = True
        self.inevinp = False
        self.search = None

        # Controller
        self.controller = None
        self.manager = None
        self.myThread = MyThread(self)
        self.myThread.time_elapsed.connect(self.on_myThread_timeElapsed)

        # Title
        self.titlelbl = QtWidgets.QLabel("Surrogate Optimization Toolbox (pySOT)", self)
        self.titlelbl.move(300, 10)

        # Plot checkbox
        self.plotprogcb = QtWidgets.QCheckBox("Plot progress", self)
        self.plotprogcb.move(680, 10)
        self.plotprogcb.toggle()

        # Default options
        self.defaultopts = QtWidgets.QPushButton('Default Options', self)
        self.defaultopts.clicked.connect(self.defaultOpts)
        self.defaultopts.move(10, 5)
        self.defaultopts.resize(140, 20)

        """ Log text area """
        self.log = QtWidgets.QTextEdit("", self)
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        font = self.log.font()
        font.setFamily("Courier")
        font.setPointSize(10)
        self.log.move(200, 420)
        self.log.resize(595, 166)
        self.log.show()
        self.printMessage("Log file initiated at: ./pySOT_GUI.log\n")
        self.printMessage("Please import your optimization problem\n")

        """ File dialog """
        self.inputDlgBtn = QtWidgets.QPushButton("Optimization problem", self)
        self.importBtn = QtWidgets.QPushButton("Import", self)
        self.inputDlgBtn.clicked.connect(self.openInputDialog)
        self.importBtn.clicked.connect(self.importAction)
        self.inputline = QtWidgets.QLineEdit("", self)
        self.inputDlgBtn.move(0, 25)
        self.importBtn.move(710, 25)
        self.inputline.setFixedWidth(540)
        self.inputline.move(170, 30)
        self.inputDlgBtn.show()
        self.importBtn.show()

        """ Info lines """
        self.info1 = QtWidgets.QLabel(self)
        self.info1.move(570, 65)
        self.info2 = QtWidgets.QLabel(self)
        self.info2.move(570, 85)
        self.info3 = QtWidgets.QLabel(self)
        self.info3.move(570, 105)
        self.info4 = QtWidgets.QLabel(self)
        self.info4.move(570, 125)
        self.info5 = QtWidgets.QLabel(self)
        self.info5.move(570, 145)

        """ Input lines """

        # Number of threads
        self.threadlbl = QtWidgets.QLabel("Number of threads", self)
        self.threaderr = QtWidgets.QLabel(self)
        self.threadline = QtWidgets.QLineEdit("4", self)
        self.threadline.setFixedWidth(60)
        self.threadline.move(150, 60)
        self.threadlbl.move(5, 65)
        self.threaderr.move(240, 65)
        self.threadline.textChanged[str].connect(self.threadChange)
        self.threadline.show()

        # Number of evaluations
        self.evallbl = QtWidgets.QLabel("Maximum evaluations", self)
        self.evalerr = QtWidgets.QLabel(self)
        self.evalline = QtWidgets.QLineEdit("500", self)
        self.evalline.setFixedWidth(60)
        self.evalline.move(150, 90)
        self.evallbl.move(5, 95)
        self.evalerr.move(240, 95)
        self.evalline.textChanged[str].connect(self.evalChange)
        self.evalline.show()

        # Simultaneous evaluations
        self.simlbl = QtWidgets.QLabel("Simultaneous evaluations", self)
        self.simerr = QtWidgets.QLabel(self)
        self.simline = QtWidgets.QLineEdit("4", self)
        self.simline.setFixedWidth(60)
        self.simline.move(420, 60)
        self.simlbl.move(250, 65)
        self.simerr.move(480, 65)
        self.simline.textChanged[str].connect(self.simChange)
        self.simline.show()

        """ Drop-down lists """

        # Asynchronous
        self.synchlbl = QtWidgets.QLabel("Asynchronous", self)
        self.synchlist = QtWidgets.QComboBox(self)
        self.synchlist.addItem("Yes")
        self.synchlist.addItem("No")
        self.synchlist.move(420, 90)
        self.synchlist.setFixedWidth(65)
        self.synchlbl.move(250, 95)
        self.synchlist.show()
        self.synchlist.setCurrentIndex(1)
        self.synchlist.setEnabled(False)

        # Experimental design
        self.explbl = QtWidgets.QLabel("Experimental design", self)
        self.explist = QtWidgets.QComboBox(self)
        self.explist.addItem("LatinHypercube")
        self.explist.addItem("SymmetricLatinHypercube")
        self.explist.move(150, 180)
        self.explbl.move(5, 185)
        self.explist.setCurrentIndex(1)
        self.explist.show()
        self.explist.activated[str].connect(self.expActivated)

        # Initial evaluations
        self.inevlbl = QtWidgets.QLabel("Initial evaluations", self)
        self.ineverr = QtWidgets.QLabel(self)
        self.inevline = QtWidgets.QLineEdit("", self)
        self.inevline.setFixedWidth(60)
        self.inevline.move(540, 180)
        self.inevlbl.move(420, 185)
        self.ineverr.move(620, 185)
        self.inevline.textChanged[str].connect(self.inevChange)
        self.inevline.show()

        # Controller
        self.controllerlbl = QtWidgets.QLabel("Controller", self)
        self.controllerlist = QtWidgets.QComboBox(self)
        self.controllerlist.addItem("ThreadController")
        self.controllerlist.addItem("SerialController")
        self.controllerlist.move(150, 120)
        self.controllerlbl.move(5, 125)
        self.controllerlist.activated[str].connect(self.controllerChange)
        self.controllerlist.show()

        # Strategy
        self.stratlbl = QtWidgets.QLabel("Strategy", self)
        self.stratlist = QtWidgets.QComboBox(self)
        self.stratlist.addItem("SyncStrategyNoConstraints")
        self.stratlist.addItem("SyncStrategyPenalty")
        self.stratlist.move(150, 150)
        self.stratlbl.move(5, 155)
        self.stratlist.activated[str].connect(self.stratChange)
        self.stratlist.show()

        # Penalty
        self.penaltylbl = QtWidgets.QLabel("Penalty", self)
        self.penaltyline = QtWidgets.QLineEdit("", self)
        self.penaltyline.setFixedWidth(60)
        self.penaltyline.move(450, 150)
        self.penaltylbl.move(400, 155)
        self.penaltyline.textChanged[str].connect(self.penaltyChange)
        self.penaltyline.setDisabled(True)

        # Search strategy
        self.searchlbl = QtWidgets.QLabel("Sampling Method", self)
        self.searchlist = QtWidgets.QComboBox(self)
        self.searchlist.addItem("CandidateDYCORS")
        self.searchlist.addItem("CandidateDDS")
        self.searchlist.addItem("CandidateSRBF")
        self.searchlist.addItem("CandidateUniform")
        self.searchlist.addItem("GeneticAlgorithm")
        self.searchlist.addItem("MultiStartGradient")
        self.searchlist.move(150, 220)
        self.searchlbl.move(5, 225)
        self.searchlist.show()

        # Response surface
        self.rslbl = QtWidgets.QLabel("Response Surface", self)
        self.rslist = QtWidgets.QComboBox(self)
        self.rslist.addItem("Cubic RBF")
        self.rslist.addItem("Linear RBF")
        self.rslist.addItem("Thin-Plate RBF")
        # Check for Kriging support
        try:
            krig = KrigingInterpolant()
            self.rslist.addItem("Kriging")
        except:
            self.printMessage("WARNING: pyKriging was not found, Kriging is not supported\n")
        # Check for MARS support
        try:
            mars = MARSInterpolant()
            self.rslist.addItem("MARS")
        except:
            self.printMessage("WARNING: py-earth was not found, MARS is not supported\n")
        self.rslist.activated[str].connect(self.rsActivated)
        self.rslist.move(540, 220)
        self.rslbl.move(420, 225)
        self.rslist.show()

        # Tail for RBF
        self.taillbl = QtWidgets.QLabel("Tail function", self)
        self.taillist = QtWidgets.QComboBox(self)
        self.taillist.addItem("LinearTail")
        self.taillist.addItem("ConstantTail")
        self.taillist.move(540, 250)
        self.taillbl.move(420, 255)
        self.taillist.show()

        # Capping
        self.rsclbl = QtWidgets.QLabel("Wrapper", self)
        self.rsclist = QtWidgets.QComboBox(self)
        self.rsclist.addItem("None")
        self.rsclist.addItem("RSCapped")
        self.rsclist.addItem("RSUnitBox")
        self.rsclist.move(540, 280)
        self.rsclbl.move(420, 285)
        self.rsclist.setCurrentIndex(0)
        self.rsclist.show()

        # Optimization button
        self.optimizebtn = QtWidgets.QPushButton('Optimize', self)
        self.optimizebtn.setStyleSheet("background-color: silver")
        self.optimizebtn.clicked.connect(self.optimizeActivated)
        self.optimizebtn.move(10, 420)
        self.optimizebtn.resize(80, 50)

        # Stop button
        self.stopbtn = QtWidgets.QPushButton('Stop', self)
        self.stopbtn.setStyleSheet("background-color: red")
        self.stopbtn.clicked.connect(self.stopActivated)
        self.stopbtn.move(100, 420)
        self.stopbtn.resize(80, 50)
        self.stopbtn.setEnabled(False)

        """ Run information """

        # Number of Evaluations
        temp = QtWidgets.QLabel("Completed Evals: ", self)
        temp.move(5, 480)
        self.nevallbl = QtWidgets.QLabel("", self)
        self.nevallbl.move(120, 480)

        # Number of crashed evaluations
        temp = QtWidgets.QLabel("Failed Evals: ", self)
        temp.move(5, 500)
        self.faillbl = QtWidgets.QLabel("", self)
        self.faillbl.move(120, 500)

        # Best value found
        temp = QtWidgets.QLabel("Best value: ", self)
        temp.move(5, 520)
        self.bestlbl = QtWidgets.QLabel("", self)
        self.bestlbl.move(120, 520)

        # Best solution feasible
        temp = QtWidgets.QLabel("Feasible: ", self)
        temp.move(5, 540)
        self.feaslbl = QtWidgets.QLabel("", self)
        self.feaslbl.move(120, 540)

        # Time
        temp = QtWidgets.QLabel("Time elapsed: ", self)
        temp.move(5, 560)
        self.timelbl = QtWidgets.QLabel("Not running", self)
        self.timelbl.move(120, 560)

        """ Add Tables for Search Strategies and Ensemble Surrogates """

        # Search strategies
        self.searchadd = QtWidgets.QPushButton('Add', self)
        self.searchadd.clicked.connect(self.searchAdd)
        self.searchadd.move(320, 222)
        self.searchadd.resize(70, 20)

        self.searchremove = QtWidgets.QPushButton('Remove', self)
        self.searchremove.clicked.connect(self.searchRemove)
        self.searchremove.move(320, 245)
        self.searchremove.resize(70, 20)
        self.searchremove.setEnabled(False)

        self.searchup = QtWidgets.QPushButton('Move\nUp', self)
        self.searchup.clicked.connect(self.searchUp)
        self.searchup.move(315, 277)
        self.searchup.resize(60, 50)
        self.searchup.setEnabled(False)

        self.searchdown = QtWidgets.QPushButton('Move\nDown', self)
        self.searchdown.clicked.connect(self.searchDown)
        self.searchdown.move(315, 318)
        self.searchdown.resize(60, 50)
        self.searchdown.setEnabled(False)

        self.searchtable = QtWidgets.QTableWidget(0, 1, self)
        self.searchtable.horizontalHeader().setVisible(False)
        self.searchtable.move(10, 250)
        self.searchtable.resize(300, 152)
        self.searchtable.setColumnWidth(0, 275)
        self.searchtable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.searchtable.show()

        # Surrogates
        self.rsadd = QtWidgets.QPushButton('Add', self)
        self.rsadd.clicked.connect(self.rsAdd)
        self.rsadd.move(705, 252)
        self.rsadd.resize(50, 20)

        self.rsremove = QtWidgets.QPushButton('Remove', self)
        self.rsremove.clicked.connect(self.rsRemove)
        self.rsremove.move(685, 282)
        self.rsremove.resize(90, 20)
        self.rsremove.setEnabled(False)

        self.rsup = QtWidgets.QPushButton('Move\nUp', self)
        self.rsup.clicked.connect(self.rsUp)
        self.rsup.move(720, 310)
        self.rsup.resize(60, 50)
        self.rsup.setEnabled(False)

        self.rsdown = QtWidgets.QPushButton('Move\nDown', self)
        self.rsdown.clicked.connect(self.rsDown)
        self.rsdown.move(720, 350)
        self.rsdown.resize(60, 50)
        self.rsdown.setEnabled(False)

        self.rstable = QtWidgets.QTableWidget(0, 1, self)
        self.rstable.horizontalHeader().setVisible(False)
        self.rstable.move(420, 310)
        self.rstable.resize(300, 92)
        self.rstable.setColumnWidth(0, 275)
        self.rstable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.rstable.show()

    def defaultOpts(self):
        self.printMessage("Not yet activated\n", "red")

    def searchAdd(self):
        row = self.searchtable.rowCount()
        self.searchtable.insertRow(row)
        self.searchtable.setItem(row, 0, QtWidgets.QTableWidgetItem(self.searchlist.currentText()))
        self.searchremove.setEnabled(True)
        if self.searchtable.rowCount() > 1:
            self.searchup.setEnabled(True)
            self.searchdown.setEnabled(True)

    def searchRemove(self):
        if self.searchtable.rowCount() > 0:
            row = self.searchtable.currentRow()
            self.searchtable.removeRow(row)
            if self.searchtable.rowCount() < 2:
                self.searchup.setEnabled(False)
                self.searchdown.setEnabled(False)
                if self.searchtable.rowCount() == 0:
                    self.searchremove.setEnabled(False)

    def searchDown(self):
        row = self.searchtable.currentRow()
        if row < self.searchtable.rowCount()-1:
            self.searchtable.insertRow(row+2)
            self.searchtable.setItem(row+2, 0, self.searchtable.takeItem(row, 0))
            self.searchtable.setCurrentCell(row+2, 0)
            self.searchtable.removeRow(row)

    def searchUp(self):
        row = self.searchtable.currentRow()
        if row > 0:
            self.searchtable.insertRow(row-1)
            self.searchtable.setItem(row-1, 0, self.searchtable.takeItem(row+1, 0))
            self.searchtable.setCurrentCell(row-1, 0)
            self.searchtable.removeRow(row+1)

    def rsAdd(self):
        row = self.rstable.rowCount()
        str = ""
        if self.rslist.currentText() == "Kriging" or self.rslist.currentText() == "MARS":
            str = self.rslist.currentText()
        else:
            str = self.rslist.currentText() + ", "
            str += self.taillist.currentText()
            if self.rsclist.currentText() == "RSCapped":
                str += ", Median Cap"
            elif self.rsclist.currentText() == "RSUnitBox":
                str += ", Unit Box"

        # Check if string already exists
        for r in range(self.rstable.rowCount()):
            if str == self.rstable.item(r, 0).text():
                return

        self.rstable.insertRow(row)
        self.rstable.setItem(row, 0, QtWidgets.QTableWidgetItem(str))
        self.rsremove.setEnabled(True)
        if self.rstable.rowCount() > 1:
            self.rsup.setEnabled(True)
            self.rsdown.setEnabled(True)

    def rsRemove(self):
        if self.rstable.rowCount() > 0:
            row = self.rstable.currentRow()
            self.rstable.removeRow(row)
            if self.rstable.rowCount() < 2:
                self.rsup.setEnabled(False)
                self.rsdown.setEnabled(False)
                if self.rstable.rowCount() == 0:
                    self.rsremove.setEnabled(False)

    def rsDown(self):
        row = self.rstable.currentRow()
        if row < self.rstable.rowCount()-1:
            self.rstable.insertRow(row+2)
            self.rstable.setItem(row+2, 0, self.rstable.takeItem(row, 0))
            self.rstable.setCurrentCell(row+2, 0)
            self.rstable.removeRow(row)

    def rsUp(self):
        row = self.rstable.currentRow()
        if row > 0:
            self.rstable.insertRow(row-1)
            self.rstable.setItem(row-1, 0, self.rstable.takeItem(row+1, 0))
            self.rstable.setCurrentCell(row-1, 0)
            self.rstable.removeRow(row+1)

    def printMessage(self, text, color="blue"):
        self.log.moveCursor(QtGui.QTextCursor.End)
        #self.log.setTextColor(color)
        self.log.insertPlainText(text)
        sb = self.log.verticalScrollBar()
        sb.setValue(sb.maximum())

    """ Triggers """

    def rsActivated(self, text):
        if (text == "Kriging") or (text == "MARS"):
            self.rsclist.setCurrentIndex(1)
            self.rsclist.setEnabled(False)
            self.taillist.setCurrentIndex(0)
            self.taillist.setEnabled(False)
        else:
            self.rsclist.setEnabled(True)
            self.taillist.setEnabled(True)

    def expActivated(self, text):
        self.inevChange(self.inevline.text())

    def controllerChange(self, text):
        if text == "SerialController":
            self.threadline.setText("1")
            self.threadline.setDisabled(True)
            self.simline.setText("1")
            self.simline.setDisabled(True)
        else:
            self.threadline.setDisabled(False)
            self.simline.setDisabled(False)

    def stratChange(self, text):
        if text == "SyncStrategyNoConstraints":
            self.penaltyline.setDisabled(True)
            self.penaltyline.setText("")
        elif text == "SyncStrategyPenalty":
            self.penaltyline.setDisabled(False)
            self.penaltyline.setText("1e6")

    def stopActivated(self):
        self.printMessage("Optimization aborted\n", "red")
        self.manager.terminate()

    def threadChange(self, text):
        if text.isdigit() and int(text) > 0:
            self.threadinp = True
        else:
            self.threadinp = False
        self.simChange(self.simline.text())

    def penaltyChange(self, text):
        if isfloat(text) and float(text) > 0:
            self.penaltyinp = True
        else:
            self.penaltyinp = False

    def evalChange(self, text):
        if text.isdigit() and int(text) > 0:
            self.evalinp = True
        else:
            self.evalinp = False

    def simChange(self, text):
        if not text.isdigit():
            self.simerr.setText("Invalid input!")
            self.simerr.adjustSize()
            self.siminp = False
        elif (not self.threadline.text().isdigit()) or int(text) > int(self.threadline.text()):
            #self.simerr.setText("Must be less than\nnumber of threads!")
            self.simerr.adjustSize()
            self.siminp = False
        else:
            self.simerr.setText("")
            self.simerr.adjustSize()
            self.siminp = True

    def inevChange(self, text):
        if self.data is None:
            self.ineverr.setText("Need data object!")
            self.inevinp = False
        elif text.isdigit() and int(text) > 0:
            if self.explist.currentText() == "LatinHypercube":
                minpts = self.data.dim + 1  # FIXME, for now
            else:
                minpts = 2*self.data.dim + 1  # FIXME, for now
            if int(text) >= minpts:
                self.ineverr.setText("")
                self.inevinp = True
            else:
                self.ineverr.setText("Need at least " + str(minpts)+" evals")
                self.inevinp = False
        else:
            self.ineverr.setText("Invalid input!")
            self.inevinp = False
        self.ineverr.adjustSize()

    def openInputDialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", os.getcwd())
        self.inputline.setText(path)
        self.inputline.adjustSize()

    def importAction(self):
        try:
            sys.path.append(os.path.dirname(self.inputline.text()))
            mod = imp.load_source(os.path.splitext(path_leaf(self.inputline.text()))[0],
                                  self.inputline.text())  # Load module
            class_ = None
            try:
                class_ = getattr(mod, os.path.splitext(path_leaf(self.inputline.text()))[0])
            except:
                self.printMessage("Import failed: Expected class named " +
                                  os.path.splitext(path_leaf(self.inputline.text()))[0] +
                                  " containing the optimization problem\n", "red")
                return None

            self.data = class_()
            check_opt_prob(self.data)
            # Check if the objective function is external
            if not hasattr(self.data, "objfunction"):
                self.external = True
                self.objfun = getattr(mod, "objfunction")
            else:
                self.external = False
                self.objfun = None
            self.printMessage("Import successful\n", "green")
            self.datainp = True
            self.inevChange(self.inevline.text())
            # Print info
            self.info1.setText(str("Problem name: " + os.path.splitext(path_leaf(self.inputline.text()))[0]))
            self.info1.adjustSize()
            self.info2.setText(str(self.data.dim) + " dimensions")
            self.info2.adjustSize()
            self.info3.setText(str(len(self.data.integer)) + " integer variables")
            self.info3.adjustSize()
            self.info4.setText("Non-box constraints: " + str(hasattr(self.data, 'eval_ineq_constraints')))
            self.info4.adjustSize()
            if self.external:
                self.info5.setText("External objective function")
            else:
                self.info5.setText("Python objective function")
            self.info5.adjustSize()

        except Exception as err:
            self.printMessage("Import failed: " + err.args[0] + "\n", "red")
            self.data = None
            self.datainp = False
            self.external = False
            self.objfun = None
            # Reset info
            self.info1.setText("")
            self.info1.adjustSize()
            self.info2.setText("")
            self.info2.adjustSize()
            self.info3.setText("")
            self.info3.adjustSize()
            self.info4.setText("")
            self.info4.adjustSize()
            self.info5.setText("")
            self.info5.adjustSize()

    def update(self, xnew, fnew, numeval, numfail):
        # Process new information
        x = xnew.reshape((1, xnew.shape[0]))

        if fnew < self.fbest:
            self.fbest = fnew
            self.xbest = xnew
            if hasattr(self.data, 'eval_ineq_constraints') and \
                       np.max(self.data.eval_ineq_constraints(x)) > 0.0:
                self.feasible = False
            else:
                self.feasible = True

        self.numeval = numeval
        self.numfail = numfail

        # Update GUI
        self.nevallbl.setText(str(self.numeval))
        self.nevallbl.adjustSize()
        self.bestlbl.setText("{:4.4f}".format(self.fbest))
        self.bestlbl.adjustSize()
        self.feaslbl.setText(str(self.feasible))
        self.feaslbl.adjustSize()
        self.faillbl.setText(str(self.numfail))
        self.faillbl.adjustSize()

        # Force redraw
        QtWidgets.QApplication.processEvents()

    def paintEvent(self, event):

        qp = QtGui.QPainter()
        qp.begin(self)
        # Data info
        qp.drawLine(530, 60, 530, 170)
        qp.drawLine(530, 60, 795, 60)
        qp.drawLine(795, 60, 795, 170)
        qp.drawLine(530, 170, 795, 170)
        # Run info
        qp.drawLine(2, 475, 2, 585)
        qp.drawLine(2, 475, 195, 475)
        qp.drawLine(195, 475, 195, 585)
        qp.drawLine(2, 585, 195, 585)
        # Search box and RS box
        qp.drawLine(3, 210, 3, 410)
        qp.drawLine(3, 210, 795, 210)
        qp.drawLine(400, 210, 400, 410)
        qp.drawLine(3, 410, 795, 410)
        qp.drawLine(795, 210, 795, 410)
        qp.end()

    #@QtCore.Slot()
    def on_timer_activated(self):
        self.myThread.start()

    #@QtCore.Slot(int)
    def on_myThread_timeElapsed(self, seconds):
        self.timelbl.setText("{0} seconds".format(seconds))
        self.timelbl.adjustSize()

        # Force redraw
        QtWidgets.QApplication.processEvents()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# ==============================================================================

    def turnActionsOff(self):
        self.optimizebtn.setEnabled(False)
        self.searchadd.setEnabled(False)
        self.searchremove.setEnabled(False)
        self.searchup.setEnabled(False)
        self.searchdown.setEnabled(False)
        self.rsadd.setEnabled(False)
        self.rsremove.setEnabled(False)
        self.rsup.setEnabled(False)
        self.rsdown.setEnabled(False)
        self.importBtn.setEnabled(False)
        self.inputDlgBtn.setEnabled(False)
        self.inputline.setEnabled(False)
        self.threadline.setEnabled(False)
        self.simline.setEnabled(False)
        self.evalline.setEnabled(False)
        self.synchlist.setEnabled(False)
        self.controllerlist.setEnabled(False)
        self.stratlist.setEnabled(False)
        self.explist.setEnabled(False)
        self.searchlist.setEnabled(False)
        self.inevline.setEnabled(False)
        self.rslist.setEnabled(False)
        self.taillist.setEnabled(False)
        self.rsclist.setEnabled(False)

    def turnActionsOn(self):
        self.stopbtn.setEnabled(False)
        self.optimizebtn.setEnabled(True)
        self.searchadd.setEnabled(True)
        self.searchremove.setEnabled(True)
        if self.searchtable.rowCount() > 1:
            self.searchup.setEnabled(True)
            self.searchdown.setEnabled(True)
        self.rsadd.setEnabled(True)
        self.rsremove.setEnabled(True)
        if self.rstable.rowCount() > 1:
            self.rsup.setEnabled(True)
            self.rsdown.setEnabled(True)
        self.importBtn.setEnabled(True)
        self.inputDlgBtn.setEnabled(True)
        self.inputline.setEnabled(True)
        if not self.controllerlist.currentText() == "SerialController":
            self.threadline.setEnabled(True)
            self.simline.setEnabled(True)
        self.evalline.setEnabled(True)
        self.controllerlist.setEnabled(True)
        self.stratlist.setEnabled(True)
        self.explist.setEnabled(True)
        self.searchlist.setEnabled(True)
        self.inevline.setEnabled(True)
        self.rslist.setEnabled(True)
        if not (self.rslist.currentText() == "Kriging" or self.rslist.currentText() == "MARS"):
            self.taillist.setEnabled(True)
            self.rsclist.setEnabled(True)

    def printProblemInfo(self):
        pass

    def optimizeActivated(self):

        # Are we ready for this?
        self.numeval = 0
        self.numfail = 0
        self.xbest = None
        self.fbest = np.inf
        self.feasible = np.NaN

        # Reset parameters from last solution
        self.nevallbl.setText("")
        self.nevallbl.adjustSize()
        self.bestlbl.setText("")
        self.bestlbl.adjustSize()
        self.feaslbl.setText("")
        self.feaslbl.adjustSize()
        self.faillbl.setText("")
        self.faillbl.adjustSize()

        # Timer
        self.timelbl.setText("Not running")
        self.timelbl.adjustSize()

        if not self.datainp:
            self.printMessage("No Optimization problem imported\n", "red")
        elif not self.threadinp:
            self.printMessage("Incorrect number of threads\n", "red")
        elif not self.evalinp:
            self.printMessage("Incorrect number of evaluations\n", "red")
        elif not self.siminp:
            self.printMessage("Incorrect number of simultaneous evaluations\n", "red")
        elif not self.inevinp:
            self.printMessage("Incorrect number of initial evaluations\n", "red")
        elif self.stratlist.currentText() == "SyncStrategyPenalty" and not self.penaltyinp:
            self.printMessage("Incorrect penalty\n", "red")
        else:
            self.turnActionsOff()

            # Extract parameters
            self.nthreads = int(self.threadline.text())
            self.maxeval = int(self.evalline.text())
            self.nsample = int(self.simline.text())

            # Experimental design
            try:
                exp_design_class = globals()[self.explist.currentText()]
                self.exp_des = exp_design_class(dim=self.data.dim, npts=int(self.inevline.text()))
            except Exception as err:
                self.printMessage("Failed to initialize experimental design: " +
                                  err.args[0] + "\n", "red")
                self.turnActionsOn()
                return

            # Search strategy
            try:
                if self.searchtable.rowCount() == 0:
                    raise AssertionError("No search sampling method")
                # Try to parse what strategies we are using
                names = []
                for i in range(self.searchtable.rowCount()):
                    names.append(str(self.searchtable.item(i, 0).text()))
                unique_names = list(set(names))
                if len(unique_names) == 1:
                    if len(names) > 1:
                        self.printMessage("Multiple sampling methods added, but only one unique. "
                                          "Initiating one such instance.\n", "blue")
                    search_strategy_class = globals()[unique_names[0]]
                    self.search = search_strategy_class(data=self.data)
                else:
                    id = range(len(unique_names))
                    weights = []
                    search_strategies = []
                    dictionary = dict(zip(unique_names, id))
                    for name in unique_names:
                        search_strategy_class = globals()[name]
                        search_strategies.append((search_strategy_class(data=self.data)))
                    for i in range(len(names)):
                        weights.append(dictionary[names[i]])
                    self.search = MultiSampling(search_strategies, weights)

            except Exception as err:
                self.printMessage("Failed to initialize sampling method: " +
                                  err.args[0] + "\n", "red")
                self.turnActionsOn()
                return

            try:
                # Check if we need Ensembles or not
                if self.rstable.rowCount() == 0:
                    raise AssertionError("No response surface specified")
                else:
                    # We need to construct en ensemble surrogate
                    rs = []
                    for i in range(self.rstable.rowCount()):
                        # Parse the name of the response surface
                        name = self.rstable.item(i, 0).text().strip().split(",")
                        name = [str(x) for x in name]
                        if len(name) == 1 and name[0] == "Kriging":
                            rs.append(KrigingInterpolant(maxp=self.maxeval))
                        elif len(name) == 1 and name[0] == "MARS":
                            rs.append(MARSInterpolant(maxp=self.maxeval))
                        else:
                            # Kernel
                            kernel_ = None
                            if name[0] == "Linear RBF":
                                kernel_ = LinearKernel
                            elif name[0] == "Cubic RBF":
                                kernel_ = CubicKernel
                            elif name[0] == "Thin-Plate RBF":
                                kernel_ = TPSKernel

                            # DSB: FIXME
                            # Tail
                            tail_ = None
                            if name[1] == " LinearTail":
                                tail_ = LinearTail
                            elif name[1] == " ConstantTail":
                                tail_ = ConstantTail

                            print(name)
                            # Build RBF (with cap if necessary)
                            if len(name) == 3:
                                if name[2] == " Median Cap":
                                    rs.append(
                                        RSCapped(
                                            RBFInterpolant(kernel=kernel_, tail=tail_,
                                                           maxp=self.maxeval)))
                                elif name[2] == " Unit Box":
                                    rs.append(
                                        RSUnitbox(
                                            RBFInterpolant(kernel=kernel_, tail=tail_,
                                                           maxp=self.maxeval), self.data))
                            else:
                                rs.append(
                                    RBFInterpolant(kernel=kernel_, tail=tail_,
                                                   maxp=self.maxeval))

                    # Finally construct the objects
                    if len(rs) == 1:
                        self.rs = rs[0]
                    else:
                        self.rs = EnsembleSurrogate(rs, maxp=self.maxeval)

            except Exception as err:
                self.printMessage("Failed to initialize response surface: " +
                                  err.args[0] + "\n", "red")
                self.turnActionsOn()
                return

            try:
                # Controller
                if self.controllerlist.currentText() == "SerialController":
                    self.controller = SerialController(self.data.objfunction)
                elif self.controllerlist.currentText() == "ThreadController":
                    self.controller = ThreadController()
                # Strategy
                if self.stratlist.currentText() == "SyncStrategyNoConstraints":
                    strat = SyncStrategyNoConstraints(0, self.data, self.rs, self.maxeval,
                                                      self.nsample, self.exp_des, self.search)
                    self.controller.strategy = strat

                elif self.stratlist.currentText() == "SyncStrategyPenalty":
                    self.penalty = float(self.penaltyline.text())
                    strat = SyncStrategyPenalty(0, self.data, self.rs, self.maxeval,
                                                self.nsample, self.exp_des, self.search,
                                                penalty=self.penalty)
                    self.controller.strategy = strat

                self.controller.strategy = CheckWorkerStrategy(self.controller, self.controller.strategy)
                # Threads
                if self.controllerlist.currentText() == "ThreadController":
                    for _ in range(self.nthreads):
                        if self.external:
                            self.controller.launch_worker(self.objfun(self.controller))
                        else:
                            worker = BasicWorkerThread(self.controller, self.data.objfunction)
                            self.controller.launch_worker(worker)
            except Exception as err:
                self.printMessage("Failed to initiate controller/strategy: " +
                                  err.args[0] + "\n", "red")
                self.turnActionsOn()
                return

            # Optimize
            try:
                self.stopbtn.setEnabled(True)

                self.numeval = 0
                self.xbest = None
                self.fbest = np.inf

                if self.stratlist.currentText() == "SyncStrategyPenalty":
                    def feasible_merit(record):
                        xx = np.zeros((1, record.params[0].shape[0]))
                        xx[0, :] = record.params[0]
                        return record.value + strat.penalty_fun(xx)[0, 0]
                else:
                    def feasible_merit(record):
                        return record.value

                self.manager = Manager(self.controller, self.maxeval, feasible_merit, self.plotprogcb.isChecked())

                self.on_timer_activated()
                self.myThread.run_timer = True
                self.printMessage("Optimization initialized\n")
                self.printProblemInfo()  # Print some information to the logfile

                self.manager.run(self)
            except Exception as err:
                self.printMessage("Optimization failed: " +
                                  err.args[0] + "\n", "red")

            self.myThread.run_timer = False
            time.sleep(1)
            self.printMessage("Runtime: " + self.timelbl.text() + "\n", "blue")
            self.timelbl.setText("Not running")
            self.timelbl.adjustSize()
            self.manager = None
            self.turnActionsOn()

            # Force redraw
            QtWidgets.QApplication.processEvents()

def GUI():
    # Use logger
    logging.basicConfig(filename="./pySOT_GUI.log",
                        level=logging.INFO)
    app = QtWidgets.QApplication(sys.argv)
    ex = myGUI()
    qr = ex.frameGeometry()
    cp = QtWidgets.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    ex.move(qr.topLeft())
    ex.setFixedSize(800, 590)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    GUI()