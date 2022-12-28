import multiprocessing

import pandas as pd
import pytz
import xarray
from pvlib import location
from config import ghi_data_path, solar_positions_path

azimuth_range = range(-180, 190, 10)
tilt_range = range(0, 100, 10)
if not solar_positions_path.is_dir():
    solar_positions_path.mkdir(parents=True)

ghi_dataset = xarray.open_mfdataset(str(ghi_data_path) + "/*.nc", combine="nested", concat_dim="time")
ghi_dataset = ghi_dataset.to_dataframe().reset_index()
ghi_dataset = ghi_dataset.set_index('time')
times = ghi_dataset.index.drop_duplicates().tz_localize(pytz.UTC)

latitudes = pd.unique(ghi_dataset['lat'])
longitudes = pd.unique(ghi_dataset['lon'])

tz = pytz.timezone('Etc/GMT+4')


def get_solar_position(latitude, longitude):
    filename = solar_positions_path / f"{round(latitude, 2)}_{round(longitude, 2)}.h5"
    if not filename.is_file():
        print(f"Calculating solar position for {latitude}_{longitude}")
        site_location = location.Location(latitude, longitude, tz=tz)
        solar_position = site_location.get_solarposition(times=times)
        # save solar position to file
        solar_position.to_hdf(str(filename), key="solar_position", mode="w", complevel=9,
                              complib="zlib")


if __name__ == '__main__':

    latitudes_longitudes = []
    for latitude in latitudes:
        for longitude in longitudes:
            latitudes_longitudes.append((latitude, longitude))

    with multiprocessing.Pool(processes=16) as pool:
        pool.starmap(get_solar_position, latitudes_longitudes)
