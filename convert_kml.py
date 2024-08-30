import os
from osgeo import osr
from osgeo import gdal
from osgeo import gdalconst
from osgeo import ogr

# if you are using conda, uncomment these two lines below. chnage username and environmentname

# os.environ['PROJ_LIB'] = 'C:\\Users\\username\\.conda\\envs\\environmentname\\Library\\share\\proj'
# os.environ['GDAL_DATA'] = 'C:\\Users\\username\\.conda\\envs\\environmentname\\Library\\share'

kml_file = 'input_file.kml' #input kml file
geojson_file = 'output_file.geojson' #output geojson file

kml_driver = ogr.GetDriverByName('KML')
if not kml_driver:
    print("KML driver is not available.")
else:
    print("KML driver is available.")


kml_datasource = kml_driver.Open(kml_file, 0) # 0 means read onlyy
if not kml_datasource:
    print(f"Failed to open KML file: {kml_file}")
else:
    print(f"KML file opened successfully: {kml_file}")

layer = kml_datasource.GetLayer()


geojson_driver = ogr.GetDriverByName('GeoJSON')
if not geojson_driver:
    print("GeoJSON driver is not available.")
else:
    print("GeoJSON driver is available.")


geojson_datasource = geojson_driver.CreateDataSource(geojson_file)
print(f"GeoJSON file created successfully: {geojson_file}")
geojson_layer = geojson_datasource.CopyLayer(layer, layer.GetName())
kml_datasource = None
geojson_datasource = None

print("Done.")
