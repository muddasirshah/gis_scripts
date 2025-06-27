import rasterio
import geopandas as gpd
import numpy as np
from shapely.geometry import shape
import json
import os
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
from rasterio.merge import merge
from shapely.validation import make_valid
from tqdm import tqdm
import glob

def mosaic_rasters(raster_folder, output_mosaic_path):
    """Merge all rasters in a folder into a single mosaic."""
    # Find all TIFF files in the folder
    raster_files = glob.glob(os.path.join(raster_folder, "*.tif"))
    if not raster_files:
        raise FileNotFoundError(f"No TIFF files found in {raster_folder}")
    
    # Open all raster files
    src_files = []
    for raster_path in tqdm(raster_files, desc="Reading rasters for mosaicking"):
        src = rasterio.open(raster_path)
        src_files.append(src)
    
    # Merge rasters
    with tqdm(total=1, desc="Mosaicking rasters") as pbar:
        mosaic, mosaic_transform = merge(src_files)
        pbar.update(1)
    
    # Get metadata from one of the source files and update
    meta = src_files[0].meta.copy()
    meta.update({
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": mosaic_transform,
        "driver": "GTiff"
    })
    
    # Write mosaic to disk
    with rasterio.open(output_mosaic_path, "w", **meta) as dst:
        dst.write(mosaic)
    
    # Close all source files
    for src in src_files:
        src.close()
    
    print(f"Mosaic created at {output_mosaic_path}")
    # Return first band if single-band raster
    return mosaic[0], mosaic_transform, meta['crs'], meta

def read_vector(geojson_path):
    """Read GeoJSON vector and return GeoDataFrame with all geometries."""
    gdf = gpd.read_file(geojson_path)
    if gdf.empty:
        raise ValueError("GeoJSON file contains no features.")
    
    # Ensure all geometries are valid
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: make_valid(geom) if not geom.is_valid else geom)
    print(f"Vector CRS: {gdf.crs}, Number of polygons: {len(gdf)}")
    return gdf

def reproject_vector(vector_gdf, raster_crs):
    """Reproject vector to match raster CRS."""
    if vector_gdf.crs != raster_crs:
        print(f"Reprojecting vector from {vector_gdf.crs} to {raster_crs}")
        vector_gdf = vector_gdf.to_crs(raster_crs)
    return vector_gdf

def resample_and_clip(raster_data, transform, raster_crs, vector_gdf, meta, output_path_template, target_resolution=0.1):
    """Resample raster to finer resolution and clip using each vector geometry, returning clipped file paths."""
    from shapely.geometry import box
    clipped_files = []
    
    for idx, row in tqdm(vector_gdf.iterrows(), total=len(vector_gdf), desc="Processing polygons"):
        # Create a single-geometry GeoDataFrame for this polygon
        single_gdf = gpd.GeoDataFrame([row], columns=vector_gdf.columns, crs=vector_gdf.crs)
        
        # Get the bounds of the current geometry
        vector_bounds = single_gdf.total_bounds
        minx, miny, maxx, maxy = vector_bounds

        # Check if bounds are valid
        if not box(minx, miny, maxx, maxy).is_valid:
            print(f"Skipping invalid bounds for polygon {idx}")
            continue

        # Calculate new shape based on target resolution
        width = int((maxx - minx) / target_resolution)
        height = int((maxy - miny) / target_resolution)
        new_transform = rasterio.transform.from_bounds(minx, miny, maxx, maxy, width, height)

        # Initialize output array for resampled data
        resampled_data = np.zeros((height, width), dtype=raster_data.dtype)

        # Perform resampling
        reproject(
            source=raster_data,
            destination=resampled_data,
            src_transform=transform,
            src_crs=raster_crs,
            dst_transform=new_transform,
            dst_crs=raster_crs,
            resampling=Resampling.bilinear
        )

        # Convert single geometry to list for rasterio.mask
        geometries = [single_gdf.geometry.iloc[0]]

        # Perform masking on resampled data
        with rasterio.io.MemoryFile() as memfile:
            meta.update({
                'height': height,
                'width': width,
                'transform': new_transform,
                'count': 1  # Ensure single band
            })
            with memfile.open(**meta) as dataset:
                dataset.write(resampled_data, 1)
            out_image, out_transform = mask(
                dataset=memfile.open(),
                shapes=geometries,
                crop=True,
                all_touched=True,
                filled=True,
                nodata=meta.get('nodata', 0)
            )

        # Update metadata with new shape and transform
        meta.update({
            'height': out_image.shape[1],
            'width': out_image.shape[2],
            'transform': out_transform,
            'driver': 'GTiff',
            'nodata': meta.get('nodata', 0),
            'count': 1  # Ensure single band
        })

        # Generate unique output path for this polygon
        output_path = output_path_template.format(idx=idx)
        
        # Write the clipped raster
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(out_image)
        print(f"Clipped raster for polygon {idx} saved to {output_path}")
        clipped_files.append(output_path)
    
    return clipped_files

def mosaic_clipped_rasters(clipped_files, final_mosaic_path, meta):
    """Merge all clipped rasters into a final mosaic."""
    if not clipped_files:
        raise ValueError("No clipped rasters to mosaic.")
    
    # Open all clipped raster files
    src_files = []
    for clipped_path in tqdm(clipped_files, desc="Reading clipped rasters for final mosaic"):
        src = rasterio.open(clipped_path)
        src_files.append(src)
    
    # Merge clipped rasters
    with tqdm(total=1, desc="Creating final mosaic") as pbar:
        final_mosaic, final_transform = merge(src_files)
        pbar.update(1)
    
    # Update metadata for final mosaic
    meta.update({
        "height": final_mosaic.shape[1],
        "width": final_mosaic.shape[2],
        "transform": final_transform,
        "driver": "GTiff",
        "count": final_mosaic.shape[0]  # Update to match number of bands
    })
    
    # Write final mosaic to disk
    with rasterio.open(final_mosaic_path, "w", **meta) as dst:
        dst.write(final_mosaic)
    
    # Close all source files
    for src in src_files:
        src.close()
    
    print(f"Final mosaic of clipped rasters saved to {final_mosaic_path}")

def main(raster_folder, geojson_path, output_mosaic_path, output_clipped_path_template, final_mosaic_path):
    """Main function to mosaic, clip rasters for all polygons, and create final mosaic."""
    # Step 1: Mosaic input rasters
    print("Creating initial mosaic...")
    raster_data, transform, raster_crs, meta = mosaic_rasters(raster_folder, output_mosaic_path)
    
    # Step 2: Read and reproject vector
    print("Reading vector...")
    vector_gdf = read_vector(geojson_path)
    vector_gdf = reproject_vector(vector_gdf, raster_crs)
    
    # Step 3: Resample and clip for each polygon
    print("Resampling and clipping mosaic for all polygons...")
    clipped_files = resample_and_clip(raster_data, transform, raster_crs, vector_gdf, meta, output_clipped_path_template, target_resolution=0.1)
    
    # Step 4: Mosaic all clipped rasters
    print("Creating final mosaic of clipped rasters...")
    mosaic_clipped_rasters(clipped_files, final_mosaic_path, meta)

if __name__ == "__main__":
    # Input paths
    raster_folder = "rasters" 
    geojson_path = "Field_0.geojson"
    output_mosaic_path = "mosaic_raster.tif"
    output_clipped_path_template = "clipped_raster_{idx}.tif" 
    final_mosaic_path = "final_mosaic.tif"  
    
    # Check if input folder and file exist
    if not os.path.exists(raster_folder):
        raise FileNotFoundError(f"Raster folder {raster_folder} not found.")
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"GeoJSON file {geojson_path} not found.")
    
    # Run the process
    try:
        main(raster_folder, geojson_path, output_mosaic_path, output_clipped_path_template, final_mosaic_path)
    except Exception as e:
        print(f"Error: {str(e)}")