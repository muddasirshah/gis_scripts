# use this script to convert kml file to geojson using GDAL and add attributes to the geojson e.g. area of polygon, name etc
import os
from osgeo import osr
from osgeo import gdal
from osgeo import gdalconst
from osgeo import ogr

# if you are using conda, uncomment these two lines below. chnage username and environmentname
# os.environ['PROJ_LIB'] = 'C:\\Users\\username\\.conda\\envs\\environmentname\\Library\\share\\proj'
# os.environ['GDAL_DATA'] = 'C:\\Users\\username\\.conda\\envs\\environmentname\\Library\\share'


kml_file = 'input_file.kml'
geojson_file = 'output_file.geojson'

kml_driver = ogr.GetDriverByName('KML')
if not kml_driver:
    print("KML driver is not available.")
else:
    print("KML driver is available.")

kml_datasource = kml_driver.Open(kml_file, 0)  # 0 means read-onlyy
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
if not geojson_datasource:
    print(f"Failed to create GeoJSON file: {geojson_file}")
else:
    print(f"GeoJSON file created successfully: {geojson_file}")
srs = layer.GetSpatialRef()
geojson_layer = geojson_datasource.CreateLayer(layer.GetName(), srs, ogr.wkbMultiPolygon)

# Add 'name' and 'area' fields to the new GeoJSON layer
name_field = ogr.FieldDefn('name', ogr.OFTString)
name_field.SetWidth(256)  # Set a maximum width for the name field
geojson_layer.CreateField(name_field)

area_field = ogr.FieldDefn('area', ogr.OFTReal)
geojson_layer.CreateField(area_field)

# Iterate over features in the KML layer
for feature in layer:
    # Get the geometry and calculate its area
    geometry = feature.GetGeometryRef()
    area = geometry.GetArea()
    # Create a new feature for the GeoJSON layer
    geojson_feature = ogr.Feature(geojson_layer.GetLayerDefn())
    # Set the 'name' and 'area' attributes
    geojson_feature.SetField('name', kml_file)  # Use the KML file name
    geojson_feature.SetField('area', area)
    # Set the geometry for the new feature
    geojson_feature.SetGeometry(geometry)
    # Add the feature to the GeoJSON layer
    geojson_layer.CreateFeature(geojson_feature)
    geojson_feature = None


kml_datasource = None
geojson_datasource = None

print("Done!")
