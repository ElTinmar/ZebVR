import os
import subprocess
import tarfile
import urllib.request
import shutil
import sys

EXPECTED_ENV_NAME = "ZebVR3"

SDK_URL = "https://flir.netx.net/file/asset/68771/original/attachment"
SDK_TARBALL = "spinnaker-4.2.0.46-amd64-22.04-pkg.tar.gz"
SDK_FOLDER = "spinnaker-4.2.0.46-amd64"

WHEEL_URL = "https://flir.netx.net/file/asset/68776/original/attachment"
WHEEL_TARBALL = "spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz"
WHEEL_FILE = "spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl"

REQUIRED_PACKAGES = [
    "libusb-1.0-0",
    "libpcre2-16-0",
    "libdouble-conversion3",
    "libxcb-xinput0",
    "libxcb-xinerama0",
    "qtbase5-dev",
    "qtchooser",
    "qt5-qmake",
    "qtbase5-dev-tools"
]

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

def install_system_packages():
    print("Installing required system packages...")
    subprocess.check_call(["sudo", "apt-get", "update"])
    subprocess.check_call(["sudo", "apt-get", "install", "-y"] + REQUIRED_PACKAGES)
    print("System packages installed.")

def download_and_extract(url, out_path):
    print(f"Downloading {out_path}...")
    urllib.request.urlretrieve(url, out_path)
    print(f"Extracting {out_path}...")
    with tarfile.open(out_path, "r:gz") as tar:
        tar.extractall()
    print("Extraction complete.")

def install_spinnaker_sdk():
    print("Installing Spinnaker SDK...")
    # Patch the udev restart line
    script_path = os.path.join(SDK_FOLDER, "configure_spinnaker.sh")
    subprocess.check_call([
        "sed", "-i",
        r"s|.*/etc/init.d/udev restart.*|    sudo systemctl restart systemd-udevd|",
        script_path
    ])
    # Run the installer
    subprocess.check_call(["sudo", "sh", "install_spinnaker.sh"], cwd=SDK_FOLDER)
    print("Spinnaker SDK installed.")

def install_python_wheel():
    print("Installing Spinnaker Python wheel...")
    # Find the wheel inside the tarball
    with tarfile.open(WHEEL_TARBALL, "r:gz") as tar:
        tar.extractall()
    subprocess.check_call([sys.executable, "-m", "pip", "install", WHEEL_FILE])
    print("Python wheel installed.")

def cleanup():
    print("Cleaning up...")
    for path in [SDK_TARBALL, WHEEL_TARBALL, WHEEL_FILE, SDK_FOLDER]:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
    print("Done.")

if __name__ == "__main__":
    conda_prefix = check_conda_environment()
    try:
        install_system_packages()
        download_and_extract(SDK_URL, SDK_TARBALL)
        install_spinnaker_sdk()
        download_and_extract(WHEEL_URL, WHEEL_TARBALL)
        install_python_wheel()
    finally:
        cleanup()
