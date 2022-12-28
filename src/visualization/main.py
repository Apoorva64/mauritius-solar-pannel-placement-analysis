import matplotlib as mpl
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from bs4 import BeautifulSoup
from qtrangeslider import QRangeSlider, QDoubleRangeSlider
from tqdm import tqdm

from main_window import Ui_MainWindow
from visualization.graphs import DNIGraph, GHIGraph, POAGraph, TranspositionFactorGraph


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, color_dict, *args, **kwargs):
        """

        :param color_dict: Defines the colors that are going to be used to build the interface
        :param args: Main Window args
        :param kwargs: Main Window kwargs
        """
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # main window setup
        self.color_dict = color_dict
        self.setWindowTitle('Solar Energy')
        # self.toolbar = NavigationToolbar(self.MplWidget.canvas, self)
        # self.addToolBar(self.toolbar)
        self.graphs = []

        self.graphs.append(DNIGraph("DNI", "longitude", "latitude", self.dni_mpl_widget))
        self.graphs.append(GHIGraph("GHI", "longitude", "latitude", self.ghi_mpl_widget))
        self.graphs.append(
            POAGraph(self.update_POA, self.surface_azimuth, self.surface_tilt, "POA Irradiance", "longitude",
                     "latitude",
                     self.poa_irradiance_mpl_widget))
        self.graphs.append(
            TranspositionFactorGraph(self.update_TF, self.surface_azimuth_transposition_factor,
                                     self.surface_tilt_transposition_factor,
                                     "Transposition Factor",
                                     "longitude", "latitude", self.transposition_factor_mpl_widget))

        for graph in tqdm(self.graphs):
            graph.load()

        # horizontal slider setup
        self.horizontalSlider.hide()
        self.range_slider = QDoubleRangeSlider(Qt.Horizontal)
        self.centralwidget.layout().addWidget(self.range_slider)
        self.range_slider.setRange(0, self.graphs[0].dataset.index.size - 1)
        self.range_slider.setTickInterval(self.graphs[0].dataset.index.size / 12)
        self.range_slider.setTickPosition(QRangeSlider.TicksBelow)
        self.range_slider.valueChanged.connect(self.rebuild_time_changed)
        self.time_range = self.graphs[0].dataset.index[0], self.graphs[0].dataset.index[-1]

        self.surface_tilt.valueChanged.connect(self.rebuild_params_changed)
        self.surface_azimuth.valueChanged.connect(self.rebuild_params_changed)

    def rebuild_params_changed(self):
        for graph in self.graphs:
            if not graph.matplotlib_widget.visibleRegion().isEmpty():
                graph.rebuild(self.time_range)

    def rebuild_time_changed(self, index_range):
        self.time_range = self.graphs[0].dataset.index[int(index_range[0])], self.graphs[0].dataset.index[
            int(index_range[1])]
        for graph in self.graphs:
            if not graph.matplotlib_widget.visibleRegion().isEmpty():
                graph.rebuild(self.time_range)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    THEME = 'dark_teal'
    # apply_stylesheet(app, theme=f'../../poa_0_0/themes/{THEME}.xml')
    font = app.font()

    # FACTOR on base size of the font
    FACTOR = 1.4
    font.setPointSize(int(8 * FACTOR))
    app.setFont(font)

    # get colors from THEME
    f = open(f'../../data/themes/{THEME}.xml', 'r')
    colors = BeautifulSoup(f, 'xml').find_all("color")
    f.close()
    colors_dict = {
        "primaryColor": colors[0].decode_contents(),
        "primaryLightColor": colors[1].decode_contents(),
        "secondaryColor": colors[2].decode_contents(),
        "secondaryLightColor": colors[3].decode_contents(),
        "secondaryDarkColor": colors[4].decode_contents(),
        "primaryTextColor": colors[5].decode_contents(),
        "secondaryTextColor": colors[6].decode_contents()
    }

    # mpl setup
    mpl.rc('axes', edgecolor=colors_dict['primaryLightColor'], facecolor=colors_dict['secondaryColor'], grid=True,
           labelcolor=colors_dict['primaryLightColor'])
    mpl.rc('xtick', color=colors_dict['primaryLightColor'])
    mpl.rc('ytick', color=colors_dict['primaryLightColor'])
    mpl.rc('figure', facecolor=colors_dict['secondaryColor'])
    mpl.rc('legend', facecolor=colors_dict['secondaryLightColor'])
    mpl.rc('text', color=colors_dict['secondaryTextColor'])
    FACTOR = 2
    SMALL_SIZE = 8 * FACTOR
    MEDIUM_SIZE = 10 * FACTOR
    BIGGER_SIZE = 12 * FACTOR

    mpl.rc('font', size=SMALL_SIZE)  # controls default text sizes
    mpl.rc('axes', titlesize=SMALL_SIZE)  # fontsize of the axes title
    mpl.rc('axes', labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
    mpl.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    mpl.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    mpl.rc('legend', fontsize=SMALL_SIZE / 1.3)  # legend fontsize
    mpl.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    mpl.rcParams["figure.autolayout"] = True  # always fit to canvas resolution
    main_window = MainWindow(colors_dict)
    main_window.showMaximized()

    app.exec_()
