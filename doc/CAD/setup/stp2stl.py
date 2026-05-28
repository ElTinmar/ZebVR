import os
import sys
import cadquery as cq

# Set the directory containing your STEP files
# Leave as '.' if the script is in the same folder as the files
folder_path = '.' 

# Linear deflection controls mesh fineness (lower = smoother/more polygons)
tolerance = 0.1 

print("Starting batch conversion...")

# Track conversion stats
converted_count = 0
skipped_count = 0

for filename in os.listdir(folder_path):
    if filename.lower().endswith(('.step', '.stp')):
        step_path = os.path.join(folder_path, filename)
        stl_filename = os.path.splitext(filename)[0] + '.stl'
        stl_path = os.path.join(folder_path, stl_filename)
        
        # Check if the STL version already exists to skip re-conversion
        if os.path.exists(stl_path):
            print(f"Skipping: {filename} (STL already exists)")
            skipped_count += 1
            continue
            
        print(f"Converting: {filename} -> {stl_filename}", flush=True)
        
        try:
            # Load the STEP file
            result = cq.importers.importStep(step_path)
            
            # Export to STL
            cq.exporters.export(result, stl_path, cq.exporters.ExportTypes.STL, tolerance)
            converted_count += 1
            
        except Exception as e:
            print(f"Error converting {filename}: {e}")

print("\n--- Conversion Summary ---")
print(f"Successfully converted: {converted_count}")
print(f"Skipped (already existed): {skipped_count}")
print("Conversion complete!")
