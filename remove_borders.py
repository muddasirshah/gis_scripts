import rasterio
from rasterio.windows import Window
import numpy as np
import os
import glob

def crop_raster(input_path, output_path):
    # Open the input raster
    with rasterio.open(input_path) as src:
        # Get raster metadata
        profile = src.profile
        width, height = src.width, src.height
        
        # Define window to crop 1 pixel from each side
        window = Window(1, 1, width-2, height-2)
        
        # Read data from window
        data = src.read(window=window)
        
        # Update metadata for new dimensions
        profile.update({
            'width': width-2,
            'height': height-2,
            'transform': src.window_transform(window)
        })
        
        # Write cropped raster to new file
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data)

def batch_crop_rasters(input_folder, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Find all TIFF files in the input folder
    tiff_files = glob.glob(os.path.join(input_folder, "*.tif"))
    
    # Process each TIFF file
    for input_raster in tiff_files:
        # Get the filename from the input path
        filename = os.path.basename(input_raster)
        # Define output path
        output_raster = os.path.join(output_folder, filename)
        
        # Crop the raster
        crop_raster(input_raster, output_raster)
        print(f"Cropped raster saved to {output_raster}")


if __name__ == "__main__":
    input_folder = "rasters"  
    output_folder = "clipped"      
    batch_crop_rasters(input_folder, output_folder)