import sys
from PyQt5 import uic, QtCore, QtGui
from board import *
from PyQt5.QtWidgets import *
from graph import *
import platform
import aboutDialog
import fileDialog
import serial.tools.list_ports

# global var
separator = "\\" if platform.system() == "Windows" else "/"  # file system separator
serial_port_connected = dict()  # all serial port connected


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.timer = QtCore.QTimer()

        # GUI loader
        uic.loadUi("..{0}GUI{0}gui.ui".format(separator), self)
        # File browser object
        self.fileManager = fileDialog.FileBrowser()
        # About window dialog
        self.aboutWindow = aboutDialog.AboutDialog()

        self.board = Board()
        self.selected_board_type = None
        self.selected_port = None

        self.singleWaves = None
        self.waveWidget = None
        self.fftWidget = None
        self.ecgWidget = None

        # start GUI in dark mode and Initialize Widgets
        self.hideSessionWidgets()
        self.darkMode()
        self.initBoardType()

    def hideSessionWidgets(self):
        self.waveLabel.hide()
        self.fftLabel.hide()
        self.ecgLabel.hide()
        self.allChannelCheck.hide()
        self.eeg_channels.hide()
        self.ecg_channels.hide()

    def showSessionWidgets(self):
        self.waveLabel.show()
        self.fftLabel.show()
        self.ecgLabel.show()
        self.allChannelCheck.show()
        self.eeg_channels.show()
        self.ecg_channels.show()

    def activatePlaybackMode(self):
        self.liveControlGroup.setEnabled(False)
        self.playbackGroup.setEnabled(True)

    def activateLiveMode(self):
        self.liveControlGroup.setEnabled(True)
        self.playbackGroup.setEnabled(False)

    # Methods for Board Type Input
    def initBoardType(self):
        global type_of_board
        for t in type_of_board.keys():
            self.inputBoard.addItem(t)

    def changeBoardType(self):
        self.selected_board_type = type_of_board.get(self.inputBoard.currentText())

    # Methods for Serial Port List
    def refreshSerialPort(self):
        self.serialPortInput.clear()
        global serial_port_connected
        ports = serial.tools.list_ports.comports()
        for port, description, _ in sorted(ports):
            serial_port_connected.update({description: port})
            self.serialPortInput.addItem(description)

    def connectToSerialPort(self):
        global serial_port_connected
        self.selected_port = serial_port_connected.get(self.serialPortInput.currentText())
        self.initSession()

    # Play the plot
    def start(self):
        self.playButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        self.startLoop(self.update, 1000 // self.board.sampling_rate)

    # Functions that update plot data
    def update(self):
        wave, fft = self.board.read_data()
        if wave is not None and fft is not None:
            self.waveWidget.refresh(wave)
            self.fftWidget.refresh(fft)
            for i, graph in enumerate(self.singleWaves):
                graph.refresh(wave[i])
        else:
            self.stopLoop()

    # some methods of MainWindow
    def showFileManager(self):
        self.fileManager.showFileBrowser()
        self.openedFileLabel.setText(self.fileManager.getFilename())
        self.initSession()

    def initSession(self):
        if self.liveRadioBtn.isChecked():
            self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.WaitCursor))
            output_path = ""
            if not len(self.outputDirectory.text()) == 0:
                output_path = self.outputDirectory.text() + separator
                output_path = output_path.replace("/", separator)
            self.board.begin_capturing(self.selected_board_type, self.selected_port, output_path)
            self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor))
        else:
            input_path = self.fileManager.getPath()
            if input_path == "":
                input_path = None
            self.board.playback(input_path)

        # EEG Single Waves Instructions
        self.singleWaves = []
        for _ in self.board.exg_channels:
            graph = Graph()
            graph.setXRange(-self.board.num_points, 0)
            graph.setYRange(-20000, 20000)
            graph.setLabels("Time (s)", "Amplitude (µV)")
            self.singleWaves.append(graph)
            self.singleWavesLayout.addWidget(graph)

        # Wave Plot Instruction
        self.waveWidget = Graph()
        self.initGraph(self.waveWidget)
        self.waveWidget.setXRange(-self.board.num_points, 0)
        self.waveWidget.setYRange(-20000, 20000)
        self.waveWidget.setLabels("Time (s)", "Amplitude (µV)")
        self.waveContainer.addWidget(self.waveWidget)

        # FFT Plot Instruction
        self.fftWidget = Graph()
        self.initGraph(self.fftWidget)
        self.fftWidget.setXRange(0, 60)
        self.fftWidget.setYRange(0, 10000)
        self.fftWidget.setLabels("Frequency (Hz)", "Amplitude (µV)")
        self.fftContainer.addWidget(self.fftWidget)

        self.ecgWidget = Graph()
        self.initGraph(self.ecgWidget, range(9, 11))
        self.ecgWidget.setLabels("Time (s)", "Amplitude (mV)")
        self.ecgContainer.addWidget(self.ecgWidget)
        if not self.ecgPlotCheckBox.isChecked():
            self.ecgWidget.hide()

        self.showSessionWidgets()
        self.mainViewGroup.setEnabled(True)
        if not self.eeg_ecg_mode.isChecked():
            self.ecgPlotCheckBox.setEnabled(False)
        self.ecg_channels.hide()
        self.ecgLabel.hide()

        if self.darkMode:
            self.darkMode()
        else:
            self.lightMode()

    def openOutputDirManager(self):
        outDir = QFileDialog.getExistingDirectory(self, "Select Directory", options=QFileDialog.ShowDirsOnly)
        self.outputDirectory.setText(outDir)

    def showAbout(self):
        self.aboutWindow.show()

    def initGraph(self, graph, channel_range=None):
        if channel_range is None:
            channel_range = self.board.exg_channels
        for i in channel_range:
            color = self.board.get_channel_color(i)
            graph.addPlot(color)

    # Methods for theme
    def fontMaximize(self):
        self.setStyleSheet(self.styleSheet() + "*{ font-size: 20px; }")

    def fontMinimize(self):
        self.setStyleSheet(self.styleSheet() + "*{ font-size: 13px; }")

    def lightMode(self):
        with open("..{0}css{0}styleLight.css".format(separator), "r") as css:
            myCSS = css.read()
            self.setStyleSheet(myCSS)
            if self.singleWaves is not None:
                for graph in self.singleWaves:
                    graph.lightTheme()
            if self.waveWidget is not None:
                self.waveWidget.lightTheme()
            if self.fftWidget is not None:
                self.fftWidget.lightTheme()

    def darkMode(self):
        with open("..{0}css{0}styleDark.css".format(separator), "r") as css:
            myCSS = css.read()
            self.setStyleSheet(myCSS)
            if self.singleWaves is not None:
                for graph in self.singleWaves:
                    graph.darkTheme()
            if self.waveWidget is not None:
                self.waveWidget.darkTheme()
            if self.fftWidget is not None:
                self.fftWidget.darkTheme()

    def toggledChannel(self, state):
        x = int(self.sender().text())
        if state == 2:
            self.waveWidget.showPlot(x)
            self.fftWidget.showPlot(x)
        else:
            self.waveWidget.hidePlot(x)
            self.fftWidget.hidePlot(x)

    def checkBoxSetter(self, status):
        self.CH1check.setChecked(status)
        self.CH2check.setChecked(status)
        self.CH3check.setChecked(status)
        self.CH4check.setChecked(status)
        self.CH5check.setChecked(status)
        self.CH6check.setChecked(status)
        self.CH7check.setChecked(status)
        self.CH8check.setChecked(status)
        self.CH9check.setChecked(status)
        self.CH10check.setChecked(status)
        self.CH11check.setChecked(status)
        self.CH12check.setChecked(status)
        self.CH13check.setChecked(status)
        self.CH14check.setChecked(status)
        self.CH15check.setChecked(status)
        self.CH16check.setChecked(status)
        self.ECGCH9check.setChecked(status)
        self.ECGCH10check.setChecked(status)
        self.ECGCH11check.setChecked(status)

    def selectAllChannel(self, state): self.checkBoxSetter(state == 2)

    # Methods for Show/Hide plot
    def show_hide_wave(self, state):
        if state == 2:
            self.waveLabel.show()
            self.waveWidget.show()
            self.showSidebar()
        else:
            self.waveLabel.hide()
            self.waveWidget.hide()
            if not self.fftPlotCheckBox.isChecked() and not self.ecgPlotCheckBox.isChecked():
                self.hideSessionWidgets()

    def show_hide_fft(self, state):
        if state == 2:
            self.fftLabel.show()
            self.fftWidget.show()
            self.showSidebar()
        else:
            self.fftLabel.hide()
            self.fftWidget.hide()
            if not self.wavePlotCheckBox.isChecked() and not self.ecgPlotCheckBox.isChecked():
                self.hideSessionWidgets()

    def show_hide_ecg(self, state):
        if not self.mainViewGroup.isEnabled():
            return

        if state == 2:
            self.ecgLabel.show()
            self.ecgWidget.show()
            self.showSidebar()
        else:
            self.ecgLabel.hide()
            self.ecgWidget.hide()
            self.ecg_channels.hide()
            if not self.wavePlotCheckBox.isChecked() and not self.fftPlotCheckBox.isChecked():
                self.hideSessionWidgets()

    def showSidebar(self):
        self.allChannelCheck.show()
        self.eeg_channels.show()
        if self.ecgPlotCheckBox.isChecked():
            self.ecg_channels.show()

    def show_hide_toolbar(self):
        if self.controlsGroup.isVisible():
            self.controlsGroup.hide()
            self.liveControlGroup.hide()
            self.mainViewGroup.hide()
            self.patientGroup.hide()
            self.playbackGroup.hide()
        else:
            self.controlsGroup.show()
            self.liveControlGroup.show()
            self.mainViewGroup.show()
            self.patientGroup.show()
            self.playbackGroup.show()

    def on_off_ecg(self, state):
        if state == 2:
            self.ecgPlotCheckBox.setEnabled(True)
            self.ecgPlotCheckBox.setChecked(True)
            self.CH9check.hide()
            self.CH10check.hide()
            self.CH11check.hide()
        else:
            self.ecgPlotCheckBox.setEnabled(False)
            self.ecgPlotCheckBox.setChecked(False)
            self.CH9check.show()
            self.CH10check.show()
            self.CH11check.show()

    # Methods for loop
    def startLoop(self, loop, delay):
        self.timer.setInterval(delay)
        self.timer.timeout.connect(loop)
        self.timer.start()

    def stopLoop(self):
        self.timer.stop()
        self.playButton.setEnabled(True)
        self.pauseButton.setEnabled(False)


# ****************************************** - - - Main block - - - *****************************************#
def main():
    # main application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


# Start Process
if __name__ == "__main__":
    main()
