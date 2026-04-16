import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import argparse

EXPECTED_ENV_NAME = "ZebVR3"
SDK_URL = "https://updates.ximea.com/public/ximea_linux_sp.tgz"
SDK_ARCHIVE = "ximea_linux_sp.tgz"
SDK_FOLDER = "package"
INSTALL_FLAG = "-pcie"

# TODO add package dependencies
# sudo apt-get install build-essential linux-headers-"$(uname -r)" libtiff5 libxcb-cursor0

def parse_arguments():
    parser = argparse.ArgumentParser(description="Install XIMEA SDK and/or Python bindings")
    parser.add_argument("--only-sdk", action="store_true", help="Only install SDK (skip Python bindings)")
    parser.add_argument("--only-python", action="store_true", help="Only install Python bindings (skip SDK)")
    parser.add_argument("--no-cleanup", action="store_true", help="Do not delete downloaded/extracted files after install")
    return parser.parse_args()

def check_conda_environment():
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if not conda_prefix:
        print("Conda environment not active. Please run:")
        print(f"   conda activate {EXPECTED_ENV_NAME}")
        sys.exit(1)

    env_name = os.path.basename(conda_prefix)
    if env_name != EXPECTED_ENV_NAME:
        print(f"Warning: Active conda environment is '{env_name}', expected '{EXPECTED_ENV_NAME}'")
        proceed = input("Continue anyway? [y/N] ").strip().lower()
        if proceed != "y":
            sys.exit(1)
    
    print(f"Conda environment '{env_name}' is active.")
    return conda_prefix

def download_sdk():
    print(f"Downloading SDK from {SDK_URL}...")
    urllib.request.urlretrieve(SDK_URL, SDK_ARCHIVE)
    print("Download complete.")

def extract_sdk():
    print("Extracting SDK archive...")
    with tarfile.open(SDK_ARCHIVE, "r:gz") as tar:
        tar.extractall()
    print("Extracted to ./package")

def run_installer():
    # NOTE: this requires admin rights
    print("Running installer...")
    subprocess.check_call(["chmod", "+x", f"{SDK_FOLDER}/install"])
    subprocess.check_call([f"./install", INSTALL_FLAG], cwd=SDK_FOLDER)
    print("Installation complete.")

def copy_python_bindings(conda_prefix):
    src = os.path.join(SDK_FOLDER, "api/Python/v3/ximea")
    dst = os.path.join(conda_prefix, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "ximea")
    print(f"Copying Python bindings to {dst}...")
    if os.path.exists(dst):
        print("Warning: Overwriting existing ximea folder.")
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print("Python bindings installed.")

def cleanup():
    print("Cleaning up...")
    os.remove(SDK_ARCHIVE)
    shutil.rmtree(SDK_FOLDER)
    print("Done.")

if __name__ == "__main__":

    args = parse_arguments()

    if args.only_sdk and args.only_python:
        print("Error: Cannot use --only-sdk and --only-python together.")
        sys.exit(1)

    conda_prefix = None
    if not args.only_sdk:
        conda_prefix = check_conda_environment()

    try:
        download_sdk()
        extract_sdk()

        if not args.only_python:
            run_installer()
            
        if not args.only_sdk:
            copy_python_bindings(conda_prefix)
            
    finally:
        if not args.no_cleanup:
            cleanup()