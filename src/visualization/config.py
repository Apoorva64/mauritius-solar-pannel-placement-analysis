from pathlib import Path

import shapefile

data_path = Path(__file__).parents[2] / 'data'

ghi_data_path = data_path / "satellite-data/irradiance-data/RAYT_HORAIRE_GLOBAL_2019"
dni_data_path = data_path / "satellite-data/irradiance-data/RAYT_HORAIRE_DIRECT_2019"
solar_positions_path = data_path / "solar_positions"
height_data_path = data_path / "satellite-data/height_data/NASADEM_NC.001_30m_aid0001.nc"
temperature_data_path = data_path / "satellite-data/temperature-data/MOD11A1.006_1km_aid0001.nc"
poa_data_path = data_path / "poa-irradiance"
MAURITIUS_CONTOUR_FILE = shapefile.Reader(str(data_path / "shapefiles/mauritius_coastline.shp"))
