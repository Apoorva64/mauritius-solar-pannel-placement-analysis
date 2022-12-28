from datetime import datetime, timedelta

import pandas as pd
import pytz
import shapefile
import xarray
from config import poa_data_path, data_path

tz = pytz.timezone("Etc/GMT+4")
azimuth_range = range(-180, 190, 10)
tilt_range = range(0, 100, 10)
date_range = [
    datetime(2019, 1, 1),
    datetime(2020, 1, 1) - timedelta(minutes=30)
]


def get_poa_for_azimuth_tilt(azimuth, tilt):
    poa = xarray.open_dataset(poa_data_path / f"{azimuth}_{tilt}.nc")
    poa = poa.to_dataframe().reset_index().set_index("time")
    poa = poa[date_range[0]:date_range[1]].groupby(['lat', 'lon']).mean().reset_index().set_index("time")
    return poa


MAURITIUS_CONTOUR_FILE = shapefile.Reader(data_path / "shapefiles/mauritius_coastline.shp")

poa_0_0 = get_poa_for_azimuth_tilt(0, 0)


def get_transposition_factor(azimuth, tilt):
    poa = get_poa_for_azimuth_tilt(azimuth, tilt)
    transposition_factor = poa["POA_GLOBAL_IRRADIANCE"] / poa_0_0["POA_GLOBAL_IRRADIANCE"]
    poa["transposition_factor"] = transposition_factor
    return poa


def select_lat_lon(df, lat, lon):
    return df[(df["lat"] == lat) & (df["lon"]) == lon]


best_tilt_azimuth = pd.DataFrame(columns=["lat", "lon", "transposition_factor", "tilt", "azimuth"])
for lat in poa_0_0["lat"].unique():
    for lon in poa_0_0["lon"].unique():
        # insert 0 as default value
        best_tilt_azimuth = pd.concat([best_tilt_azimuth, pd.DataFrame({
            'lat': [lat],
            'lon': [lon],
            'transposition_factor': [0],
            'tilt': [0],
            'azimuth': [0]
        })])

for azimuth in azimuth_range:
    for tilt in tilt_range:
        print(f"Processing {azimuth} {tilt}")
        transposition_factor = get_transposition_factor(azimuth, tilt)
        for lat in poa_0_0["lat"].unique():
            for lon in poa_0_0["lon"].unique():
                if select_lat_lon(transposition_factor, lat, lon)['transposition_factor'].values[0] > \
                        select_lat_lon(best_tilt_azimuth, lat, lon)['transposition_factor'].values[0]:
                    best_tilt_azimuth.loc[
                        (best_tilt_azimuth["lat"] == lat) & (best_tilt_azimuth["lon"] == lon), "transposition_factor"] = \
                    select_lat_lon(transposition_factor, lat, lon)['transposition_factor'].values[0]
                    best_tilt_azimuth.loc[
                        (best_tilt_azimuth["lat"] == lat) & (best_tilt_azimuth["lon"] == lon), "tilt"] = tilt
                    best_tilt_azimuth.loc[
                        (best_tilt_azimuth["lat"] == lat) & (best_tilt_azimuth["lon"] == lon), "azimuth"] = azimuth
