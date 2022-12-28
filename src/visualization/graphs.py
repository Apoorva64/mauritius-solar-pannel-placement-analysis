import abc
import sys

import xarray

from config import MAURITIUS_CONTOUR_FILE, ghi_data_path, poa_data_path, dni_data_path
from utils import plot_map


class Graph(abc.ABC):

    def __init__(self, title, x_label, y_label, matplotlib_widget):
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.matplotlib_widget = matplotlib_widget
        self.latitude_limits = [-20.55, -19.95]
        self.longitude_limits = [57.3, 57.84]

    def load(self):
        pass

    def rebuild(self, time_range):
        pass


class DNIGraph(Graph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataset = None
        self.color_bar_max = None
        self.color_bar_min = None

    def load(self):
        dni_dataset = xarray.open_mfdataset(str(dni_data_path) + "/*.nc", combine="nested", concat_dim="time")
        dni_dataset = dni_dataset.to_dataframe().reset_index()
        self.dataset = dni_dataset.set_index('time')

    def rebuild(self, time_range):
        data_select = self.dataset[time_range[0]:time_range[1]]
        data = data_select.groupby(['lat', 'lon']).mean().reset_index()
        fig = self.matplotlib_widget.figure
        fig.clear()
        ax = fig.add_subplot()
        ax.set_title(f"DNI ({time_range[0]} - {time_range[1]})")
        ax.set_ylabel('latitude')
        ax.set_xlabel('longitude')
        plot_map(ax, MAURITIUS_CONTOUR_FILE)
        contourf = ax.tricontourf(data['lon'], data['lat'], data['SID'])
        contour = ax.tricontour(data['lon'], data['lat'], data['SID'])

        ax.set_xlim(self.longitude_limits)
        ax.set_ylim(self.latitude_limits)
        ax.figure.colorbar(contourf, label='DNI (W/m²)')
        ax.clabel(contour, inline=1, fontsize=7, colors='black')
        self.matplotlib_widget.canvas.draw()


class GHIGraph(Graph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataset = None
        self.color_bar_max = None
        self.color_bar_min = None

    def load(self):
        ghi_dataset = xarray.open_mfdataset(str(ghi_data_path) + "/*.nc", combine="nested", concat_dim="time")
        ghi_dataset = ghi_dataset.to_dataframe().reset_index()
        self.dataset = ghi_dataset.set_index('time')

    def rebuild(self, time_range):
        data_select = self.dataset[time_range[0]:time_range[1]]
        data = data_select.groupby(['lat', 'lon']).mean().reset_index()
        fig = self.matplotlib_widget.figure
        fig.clear()
        ax = fig.add_subplot()
        ax.set_title(f"GHI ({time_range[0]} - {time_range[1]})")
        ax.set_ylabel('latitude')
        ax.set_xlabel('longitude')
        plot_map(ax, MAURITIUS_CONTOUR_FILE)
        contourf = ax.tricontourf(data['lon'], data['lat'], data['SIS'])
        contour = ax.tricontour(data['lon'], data['lat'], data['SIS'])

        ax.set_xlim(self.longitude_limits)
        ax.set_ylim(self.latitude_limits)
        ax.figure.colorbar(contourf, label='GHI (W/m²)')
        ax.clabel(contour, inline=1, fontsize=7, colors='black')
        self.matplotlib_widget.canvas.draw()


class POAGraph(Graph):
    def __init__(self, update_widget, surface_azimuth_widget, surface_tilt_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_range = None
        self.longitudes = None
        self.latitudes = None
        self.dataset = None
        self.color_bar_max = None
        self.color_bar_min = None
        self.surface_azimuth_widget = surface_azimuth_widget
        self.surface_tilt_widget = surface_tilt_widget
        self.update_widget = update_widget
        self.update_widget.clicked.connect(self.full_rebuild)

    def full_rebuild(self):
        self.load(self.surface_tilt_widget.value(), self.surface_azimuth_widget.value())
        self.rebuild(self.time_range)

    def load(self, tilt=0, azimuth=0):
        poa_data_part = poa_data_path / f"{tilt}_{azimuth}.nc"
        if not poa_data_part.exists():
            return
        poa_dataset = xarray.open_dataset(poa_data_part)
        poa_dataset = poa_dataset.to_dataframe().reset_index()
        self.dataset = poa_dataset.set_index('time')
        self.time_range = [self.dataset.index[0], self.dataset.index[-1]]

    def rebuild(self, time_range):
        data_select = self.dataset[time_range[0]:time_range[1]]
        self.time_range = time_range
        data = data_select.groupby(['lat', 'lon']).mean().reset_index()
        fig = self.matplotlib_widget.figure
        fig.clear()
        ax = fig.add_subplot()
        ax.set_title(f"POA ({time_range[0]} - {time_range[1]})")
        ax.set_ylabel('latitude')
        ax.set_xlabel('longitude')
        plot_map(ax, MAURITIUS_CONTOUR_FILE)
        contourf = ax.tricontourf(data['lon'], data['lat'], data['POA_GLOBAL_IRRADIANCE'])
        contour = ax.tricontour(data['lon'], data['lat'], data['POA_GLOBAL_IRRADIANCE'])

        ax.set_xlim(self.longitude_limits)
        ax.set_ylim(self.latitude_limits)
        ax.figure.colorbar(contourf, label='POA (W/m²)')
        ax.clabel(contour, inline=1, fontsize=7, colors='black')
        self.matplotlib_widget.canvas.draw()


class TranspositionFactorGraph(Graph):
    def __init__(self, update_widget, surface_azimuth_widget, surface_tilt_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_range = None
        self.longitudes = None
        self.latitudes = None
        self.dataset = None
        self.color_bar_max = None
        self.color_bar_min = None
        self.surface_azimuth_widget = surface_azimuth_widget
        self.surface_tilt_widget = surface_tilt_widget
        self.poa_0_0 = None
        self.update_widget = update_widget
        self.update_widget.clicked.connect(self.full_rebuild)

    def full_rebuild(self):
        self.reload(self.surface_tilt_widget.value(), self.surface_azimuth_widget.value())
        self.rebuild(self.time_range)

    def reload(self, tilt=0, azimuth=0):
        poa_data_part = poa_data_path / f"{tilt}_{azimuth}.nc"
        if not poa_data_part.exists():
            return
        poa_dataset = xarray.open_dataset(poa_data_part)
        poa_dataset = poa_dataset.to_dataframe().reset_index()
        self.dataset = poa_dataset.set_index('time')
        self.time_range = [self.dataset.index[0], self.dataset.index[-1]]

    def load(self):
        poa_data_path_0_0 = poa_data_path / f"0_0.nc"
        if not poa_data_path_0_0.exists():
            return
        poa_dataset = xarray.open_dataset(poa_data_path_0_0)
        poa_dataset = poa_dataset.to_dataframe().reset_index()
        self.poa_0_0 = poa_dataset.set_index('time')
        self.reload(self.surface_tilt_widget.value(), self.surface_azimuth_widget.value())

    def rebuild(self, time_range):
        data_select = self.dataset[time_range[0]:time_range[1]]
        data_select_0_0 = self.poa_0_0[time_range[0]:time_range[1]]
        self.time_range = time_range
        data = data_select.groupby(['lat', 'lon']).mean().reset_index()
        data_0_0 = data_select_0_0.groupby(['lat', 'lon']).mean().reset_index()
        data['transposition_factor'] = data['POA_GLOBAL_IRRADIANCE'] / data_0_0['POA_GLOBAL_IRRADIANCE']
        fig = self.matplotlib_widget.figure
        fig.clear()
        ax = fig.add_subplot()
        ax.set_title(f"Transposition Factor ({time_range[0]} - {time_range[1]})")
        ax.set_ylabel('latitude')
        ax.set_xlabel('longitude')
        plot_map(ax, MAURITIUS_CONTOUR_FILE)
        contourf = ax.tricontourf(data['lon'], data['lat'], data['transposition_factor'])
        contour = ax.tricontour(data['lon'], data['lat'], data['transposition_factor'], colors='black')

        ax.set_xlim(self.longitude_limits)
        ax.set_ylim(self.latitude_limits)
        ax.figure.colorbar(contourf, label='Transposition Factor')
        ax.clabel(contour, inline=1, fontsize=7, colors='black')
        self.matplotlib_widget.canvas.draw()
