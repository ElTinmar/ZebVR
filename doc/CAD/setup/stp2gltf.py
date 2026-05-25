import os
import sys
import cadquery as cq

# Set the directory containing your STEP files
folder_path = '.' 

# Linear deflection controls mesh fineness (lower = smoother/more polygons)
tolerance = 0.1 

print("Starting batch conversion to glTF...")

# Track conversion stats
converted_count = 0
skipped_count = 0

for filename in os.listdir(folder_path):
    if filename.lower().endswith(('.step', '.stp')):
        step_path = os.path.join(folder_path, filename)
        # Changing the target format to .gltf
        gltf_filename = os.path.splitext(filename)[0] + '.gltf'
        gltf_path = os.path.join(folder_path, gltf_filename)
        
        # Check if the glTF version already exists to skip re-conversion
        if os.path.exists(gltf_path):
            print(f"Skipping: {filename} (glTF already exists)")
            skipped_count += 1
            continue
            
        print(f"Converting: {filename} -> {gltf_filename}", flush=True)
        
        try:
            # 1. Load the STEP file as an ASSEMBLY to preserve color/structure
            assembly = cq.Assembly.importStep(step_path)
            
            # 2. Export to glTF (automatically handles colors and hierarchy)
            # tolerance controls the mesh fineness just like before
            assembly.save(gltf_path, exportType="GLTF", tolerance=tolerance)
            
            converted_count += 1
            
        except Exception as e:
            print(f"Error converting {filename}: {e}")

print("\n--- Conversion Summary ---")
print(f"Successfully converted: {converted_count}")
print(f"Skipped (already existed): {skipped_count}")
print("Conversion complete!")
