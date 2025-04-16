import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request

EXPECTED_ENV_NAME = "ZebVR3"
SDK_URL = "https://updates.ximea.com/public/ximea_linux_sp_beta.tgz"
SDK_ARCHIVE = "ximea_linux_sp_beta.tgz"
SDK_FOLDER = "package"
INSTALL_FLAG = "-pcie"


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
    conda_prefix = check_conda_environment()
    try:
        download_sdk()
        extract_sdk()
        run_installer()
        copy_python_bindings(conda_prefix)
    finally:
        cleanup()
