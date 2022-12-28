import datetime
import multiprocessing

import netCDF4 as nc
import numpy as np
import pandas as pd
import pytz
import xarray
from pvlib import irradiance
from tqdm.notebook import tqdm

from config import dni_data_path, ghi_data_path, solar_positions_path, poa_data_path

tz = pytz.timezone("Etc/GMT+4")

poa_data_path.mkdir(exist_ok=True)

ghi_dataset = xarray.open_mfdataset(str(ghi_data_path) + "/*.nc", combine="nested", concat_dim="time")
ghi_dataset = ghi_dataset.to_dataframe().reset_index()
ghi_dataset = ghi_dataset.set_index('time')
latitudes = pd.unique(ghi_dataset['lat'])
longitudes = pd.unique(ghi_dataset['lon'])

dni_dataset = xarray.open_mfdataset(str(dni_data_path) + "/*.nc", combine="nested", concat_dim="time")
dni_dataset = dni_dataset.to_dataframe().reset_index()
dni_dataset = dni_dataset.set_index('time')


def get_data_at_loc(data, lat, lon, data_name):
    select1 = data[data["lat"] == lat]
    select2 = select1[select1["lon"] == lon]
    series = pd.Series(select2.index.values, index=select2[data_name])
    series = pd.Series(series.index.values, index=series, name=data_name)
    return series


# Load solar positions


def get_poa_irradiance(latitude, longitude, azimuth, tilt, solar_positions):
    solar_position = solar_positions[(latitude, longitude)]

    dni_series = get_data_at_loc(dni_dataset, latitude, longitude, "SID").tz_localize(pytz.UTC)
    ghi_series = get_data_at_loc(ghi_dataset, latitude, longitude, "SIS").tz_localize(pytz.UTC)
    dhi_series = ghi_series - dni_series * np.cos(np.radians(solar_position['zenith']))
    POA_irradiance = irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        dni=dni_series,
        ghi=ghi_series,
        dhi=dhi_series,
        # dhi=clearsky['dhi'],
        dni_extra=irradiance.get_extra_radiation(ghi_series.index),
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'],
        albedo=0.2,
        model="perez"
    )['poa_global']
    return POA_irradiance


def calculate_and_save_poa_irradiance(azimuth, tilt, latitudes, longitudes, solar_positions):
    file_path = poa_data_path / f"{tilt}_{azimuth}.nc"
    if file_path.is_file():
        print(f"Skipping {tilt}_{azimuth}")
        return
    dataset = xarray.open_mfdataset(str(dni_data_path) + '/*.nc', combine="nested", concat_dim="time")
    dataset.to_netcdf(str(file_path))
    dataset.close()
    dataset = nc.Dataset(str(file_path), "r+")
    dataset.renameVariable('SID', 'POA_GLOBAL_IRRADIANCE')
    dataset.variables['POA_GLOBAL_IRRADIANCE'].long_name = "Plane of Array Irradiance"
    dataset.variables['POA_GLOBAL_IRRADIANCE'].units = "W/m^2"
    dataset.variables['POA_GLOBAL_IRRADIANCE'].set_auto_mask(False)
    dataset.variables['POA_GLOBAL_IRRADIANCE'].set_auto_scale(False)
    dataset.CDI = "Climate Data Interface version 1.9.8 (http://mpimet.mpg.de/cdi)"
    dataset.Conventions = "CF-1.6"
    dataset.history = f'Created {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'

    dataset.creator_name = "Appadoo Apoorva Srinivas"
    dataset.creator_email = "apoorvaappadoo@gmail.com"

    dataset.project = "Mauritius Solar Pannel Placement Analysis"
    dataset.creator_type = "person"
    dataset.title = f"Plane of Array Irradiance for Mauritius at tilt {tilt} and azimuth {azimuth} for the year 2019"
    dataset.publisher_name = "Appadoo Apoorva Srinivas"
    dataset.publisher_email = "apoorvaappadoo@gmail.com"

    dataset.publisher_type = "person"
    dataset.summary = f"This file contains the plane of array irradiance for Mauritius at tilt {tilt} and azimuth {azimuth} for the year 2019"
    dataset.keywords = "Plane of Array Irradiance, Mauritius, Solar Pannels, Tilt, Azimuth"
    dataset.keywords_vocabulary = "GCMD Science Keywords"
    dataset.time_coverage_start = "2019-01-01"
    dataset.time_coverage_end = "2019-12-31"
    dataset.time_coverage_duration = "P1Y"
    dataset.time_coverage_resolution = "P30M"
    dataset.date_created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dataset.product_version = "1.0"

    dataset.publisher_url = ""
    dataset.institution = ""
    dataset.references = ""
    dataset.source = ""
    dataset.CMSAF_nwp_data = ""
    dataset.creator_url = ""
    dataset.instrument = ""
    dataset.instrument_vocabulary = ""
    dataset.platform = ""
    dataset.platform_vocabulary = ""

    # remove attributes
    dataset.__delattr__('publisher_url')
    dataset.__delattr__('institution')
    dataset.__delattr__('references')
    dataset.__delattr__('source')
    dataset.__delattr__('CMSAF_nwp_data')
    dataset.__delattr__('creator_url')
    dataset.__delattr__('instrument')
    dataset.__delattr__('instrument_vocabulary')
    dataset.__delattr__('platform')
    dataset.__delattr__('platform_vocabulary')

    for i, latitude in tqdm(enumerate(latitudes), desc="latitudes", leave=False, total=len(latitudes)):
        for j, longitude in enumerate(longitudes):
            dataset.variables['POA_GLOBAL_IRRADIANCE'][:, i, j] = get_poa_irradiance(latitude, longitude,
                                                                                     azimuth, tilt, solar_positions)

    dataset.close()

    print(f"Saved {tilt}_{azimuth}")


if __name__ == '__main__':
    azimuth_range = range(-180, 190, 10)
    tilt_range = range(0, 100, 10)
    inputs = []
    solar_positions = {}

    for latitude in latitudes:
        for longitude in longitudes:
            print(f"Loading solar position data for {latitude}_{longitude}")
            df = pd.HDFStore(solar_positions_path / f"{round(latitude, 2)}_{round(longitude, 2)}.h5", mode='r')[
                'solar_position']
            solar_positions[(latitude, longitude)] = df

    for azimuth in azimuth_range:
        for tilt in tilt_range:
            inputs.append((azimuth, tilt, latitudes, longitudes, solar_positions))
    with multiprocessing.Pool(processes=16) as pool:
        pool.starmap(calculate_and_save_poa_irradiance, inputs)
