# About the repository
Welcome to the GIS Data Processing Scripts repository! This repository contains a collection of scripts and tools designed to facilitate various GIS (Geographic Information Systems) data processing tasks. Whether you're working on spatial analysis, data transformation, or visualization, these scripts are here to help.

# Important
Most of the GDAL based python scripts uses anaconda / "miniconda", you have to create the environment first with GDAL installed first here is how
To create an environment, change python version if you like but for me GDAL worked on python 3.6 so kept that, later releases of GDAL works with python > 3.10
>> conda create -n environmentname python=3.6 gdal 
>> conda activate environmentname
>> pip install pyproj

# Contents
1. Spatial Data Manipulation: Scripts for processing and transforming vector and raster data.
2. Geospatial Analysis: Tools for performing spatial analysis, including overlay analysis, proximity calculations, and more.
3. Data Conversion: Scripts to convert between different geospatial data formats (e.g., Shapefile, GeoJSON, KML).
4. Visualization: Scripts for visualizing GIS data using libraries like Leaflet, Matplotlib, or Folium.
5. Automation: Tools for automating repetitive GIS tasks using Python and other programming languages.

# Requirements
To run these scripts, you will need to have the following software and libraries installed:

Python 3.x
GDAL/OGR
QGIS
Fiona
Geopandas
Shapely
Rtree
Matplotlib
Folium
Leaflet.js (for web-based visualization)
