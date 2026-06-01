import os
import re
from pipdeptree._models import PackageDAG
from pipdeptree._discovery import get_installed_distributions
import graphviz  

CUSTOM_PACKAGES = {
    "tracker", "camera_tools", "video_tools", "image_tools", "qt_widgets", 
    "dagline", "ipc_tools", "daq_tools", "thorlabs_ccs", "thorlabs_pmd", "viewsonicprojectorrs232", 
    "multiprocessing_logger", "ds18b20"
}
def normalize(name):
    return re.sub(r'[-_]', '', name).lower().strip()

def main():
    norm_custom = {normalize(pkg) for pkg in CUSTOM_PACKAGES}
    
    print("Step 1: Loading installed packages...")
    pkgs = get_installed_distributions()
    
    # Build the graph structure using pipdeptree's official API
    full_dag = PackageDAG.from_pkgs(pkgs)
    
    print("Step 2: Filtering custom package connections...")
    # Initialize a Graphviz Digraph directly
    dot = graphviz.Digraph(comment="Custom Dependencies", format="png")
    
    # Track nodes we've added to prevent duplicates in the visualization
    added_nodes = set()

    # full_dag behaves like a dictionary directly now!
    for parent, children in full_dag.items():
        norm_parent = normalize(parent.project_name)
        
        # Only process if the parent is one of your custom packages
        if norm_parent in norm_custom:
            p_name = parent.project_name
            
            if p_name not in added_nodes:
                dot.node(p_name, p_name)
                added_nodes.add(p_name)
            
            # Filter and add edges only to other custom packages
            for child in children:
                if normalize(child.project_name) in norm_custom:
                    c_name = child.project_name
                    
                    if c_name not in added_nodes:
                        dot.node(c_name, c_name)
                        added_nodes.add(c_name)
                        
                    dot.edge(p_name, c_name)

    output_filename = "custom_dependencies"
    print(f"Step 3: Rendering image to {output_filename}.png...")
    
    # Render and clean up the raw text source file automatically
    dot.render(output_filename, cleanup=True)
    print(f"Success! Graph rendered at: {os.path.abspath(output_filename + '.png')}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()