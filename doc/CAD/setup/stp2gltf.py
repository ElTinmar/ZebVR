import os
import sys
import cadquery as cq

# Set the directory containing your STEP files
folder_path = '.' 

# Linear deflection controls mesh fineness (lower = smoother/more polygons)
tolerance = 0.1 

print("Starting robust batch conversion to glTF...")

# Track conversion stats
converted_count = 0
skipped_count = 0

for filename in os.listdir(folder_path):
    if filename.lower().endswith(('.step', '.stp')):
        step_path = os.path.join(folder_path, filename)
        gltf_filename = os.path.splitext(filename)[0] + '.gltf'
        gltf_path = os.path.join(folder_path, gltf_filename)
        
        if os.path.exists(gltf_path):
            print(f"Skipping: {filename} (glTF already exists)")
            skipped_count += 1
            continue
            
        print(f"Converting: {filename} -> {gltf_filename}", flush=True)
        
        try:
            try:
                # Strategy 1: Try importing as an Assembly (preserves colors/hierarchy)
                assembly = cq.Assembly.importStep(step_path)
            except Exception as assembly_error:
                # Strategy 2: Fallback if it's a single part without assembly data
                print(f"  -> Note: Not an assembly ({assembly_error}). Importing as single part...")
                
                # Load raw shape/compound
                raw_shape = cq.importers.importStep(step_path)
                
                # Manually wrap the single part into a temporary Assembly object
                # This allows us to still use the modern glTF exporter for Blender
                assembly = cq.Assembly(raw_shape, name=os.path.splitext(filename)[0])
            
            # Export to glTF (Blender-friendly)
            assembly.save(gltf_path, exportType="GLTF", tolerance=tolerance)
            converted_count += 1
            
        except Exception as e:
            print(f"Error converting {filename}: {e}")

print("\n--- Conversion Summary ---")
print(f"Successfully converted: {converted_count}")
print(f"Skipped (already existed): {skipped_count}")
print("Conversion complete!")