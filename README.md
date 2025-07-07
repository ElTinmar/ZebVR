# ZebVR

Virtual reality for zebrafish.

<!---TODO
Add screenshots of the GUI
-->

## Installation

This program is meant to run on Ubuntu >= 22.04

### Dependencies

```bash
sudo apt-get install libportaudio2 build-essential libusb-1.0-0-dev
```

### Labjack exodriver

Ubuntu
```bash
git clone https://github.com/labjack/exodriver.git
cd exodriver/
sudo ./install.sh
cd .. 
rm -rf exodriver
```

Windows: https://files.labjack.com/installers/LJM/Windows/x86_64/release/LabJack_2024-05-16.exe

### Get code from github and create conda environment

```bash
git clone https://github.com/ElTinmar/ZebVR.git
cd ZebVR
conda env create -f ZebVR3.yml
conda activate ZebVR3
```

### Install camera SDK and python bindings into environment

The SDK and python binding URLs are hardcoded in the script and will break
if the camera manufacturers decide to change their website.

```bash
conda activate ZebVR3
python setup_ximea.py
python setup_spinnaker.py
```

You can also install the SDK (requires sudo) or python bindings separately:

```bash
python setup_ximea.py --only-sdk
python setup_spinnaker.py --only-sdk
```

```bash
conda activate ZebVR3
python setup_ximea.py --only-python
python setup_spinnaker.py --only-python
```

Please note that every time a new kernel is installed during a system update,
the SDK needs to be reinstalled.

### Permissions to access hardware

```bash
sudo usermod -a -G plugdev,dialout "$USER"
```

### CUDA

This seems necessary for now
TODO make that optional

```bash
sudo apt install nvidia-cuda-toolkit
```

## Run

```bash
conda activate ZebVR3
python -m ZebVR
```

## Using .desktop

Change the content depending on where ZebVR was downloaded

(Otional) If you change settings and want to check syntax:

```bash
desktop-file-validate ZebVR.desktop
```

```bash
cp ZebVR.desktop ~/.local/share/applications/
```

## Optimizations (experimental)

### Allow the python interpreter to set scheduler

```bash
sudo setcap cap_sys_nice=eip /home/martinprivat/miniconda3/envs/ZebVR3/bin/python3.8
```

### CPU shield and affinity

```bash
sudo apt install cpuset
```

```bash
sudo cset shield --cpu 1-31 --kthread=on
sudo cset shield --exec bash
su username
conda activate ZebVR3
python -m ZebVR
```

```bash
sudo cset shield --reset
```

### OpenGL check number of uniforms

```python
from vispy import app, gloo
from OpenGL.GL import GL_FRAMEBUFFER_SRGB, glIsEnabled
canvas = app.Canvas()
canvas.show()
app.process_events()

gpu_info = {
    "sRGB": glIsEnabled(GL_FRAMEBUFFER_SRGB),
    "Renderer": gloo.gl.glGetParameter(gloo.gl.GL_RENDERER),
    "Vendor": gloo.gl.glGetParameter(gloo.gl.GL_VENDOR),
    "OpenGL Version": gloo.gl.glGetParameter(gloo.gl.GL_VERSION),
    "Shading Language Version": gloo.gl.glGetParameter(gloo.gl.GL_SHADING_LANGUAGE_VERSION),
    "Max Vertex Uniform Vectors": gloo.gl.glGetParameter(gloo.gl.GL_MAX_VERTEX_UNIFORM_VECTORS),
    "Max Fragment Uniform Vectors": gloo.gl.glGetParameter(gloo.gl.GL_MAX_FRAGMENT_UNIFORM_VECTORS),
    "Max Varying Vectors": gloo.gl.glGetParameter(gloo.gl.GL_MAX_VARYING_VECTORS),
    "Max Texture Size": gloo.gl.glGetParameter(gloo.gl.GL_MAX_TEXTURE_SIZE),
    "Max Cube Map Texture Size": gloo.gl.glGetParameter(gloo.gl.GL_MAX_CUBE_MAP_TEXTURE_SIZE),
    "Max Combined Texture Image Units": gloo.gl.glGetParameter(gloo.gl.GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS),
    "Max Vertex Attributes": gloo.gl.glGetParameter(gloo.gl.GL_MAX_VERTEX_ATTRIBS),
    "Max Vertex Texture Image Units": gloo.gl.glGetParameter(gloo.gl.GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS),
    "Max Renderbuffer Size": gloo.gl.glGetParameter(gloo.gl.GL_MAX_RENDERBUFFER_SIZE),
}

for key, value in gpu_info.items():
    print(f"{key}: {value}")


canvas.close()
```


## Troubleshooting

### Ximea Error 57

if error 57 device already open, or if program is slower than usual

```bash
sudo killall python
```

### Ximea Error 56

if error 56 No Devices Found, reinstall SDK (requires sudo)

```bash
python setup_ximea.py --only-sdk
```

## modprobe: ERROR: could not insert 'ximea_cam_pcie': Key was rejected by service

Disable secure boot in the BIOS

## module not found

Try refreshing the environment

```
conda env update -f ZebVR3.yml
```