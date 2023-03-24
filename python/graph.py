from pyqtgraph import *


class Function:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Graph(PlotWidget):
    def __init__(self):
        super().__init__()
        self.plots = []

        self.showGrid(x=True, y=True)
        self.lightTheme()

    def setLabels(self, x_label, y_label):
        self.setLabel("left", y_label)
        self.setLabel("bottom", x_label)

    def lightTheme(self):
        self.setBackground("white")

    def darkTheme(self):
        self.setBackground("black")

    def hidePlot(self, index):
        if index <= len(self.plots):
            self.removeItem(self.plots[index - 1])

    def showPlot(self, index):
        if index <= len(self.plots):
            self.addItem(self.plots[index - 1])

    def addPlot(self, color):
        pen = mkPen(color=color)
        graph = self.plot([], [], pen=pen)
        self.plots.append(graph)
        return graph

    def clear(self):
        super().clear()
        self.plots.clear()

    def refresh(self, data):
        for i, graph in enumerate(self.plots):
            graph.setData(data[i].x, data[i].y)
