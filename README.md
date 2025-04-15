# ZebVR

Virtual reality for zebrafish.

```bash
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

## Installation

### Get code from github and create conda environment

```bash
git clone https://github.com/ElTinmar/ZebVR.git
cd ZebVR
conda env create -f ZebVR3.yml
conda activate ZebVR3
```

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

### CUDA

This seems necessary for now
TODO make that optional

```bash
sudo apt install nvidia-cuda-toolkit
```

### Install ximea package into environment

```bash
conda activate ZebVR3
wget https://updates.ximea.com/public/ximea_linux_sp_beta.tgz
tar xzf ximea_linux_sp_beta.tgz
cd package
./install -pcie
cp -r api/Python/v3/ximea "${CONDA_PREFIX}/lib/python3.8/site-packages/"
cd ..
rm -f ximea_linux_sp_beta.tgz
rm -rf package
```

### Download and install spinnaker SDK and python whl (this will break if they change URL)

Install SDK for Ubuntu 22.04

```bash
sudo apt-get install libusb-1.0-0 libpcre2-16-0 libdouble-conversion3 libxcb-xinput0 libxcb-xinerama0 qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools
wget -O spinnaker-4.2.0.46-amd64-22.04-pkg.tar.gz https://flir.netx.net/file/asset/68771/original/attachment
tar xzf spinnaker-4.2.0.46-amd64-22.04-pkg.tar.gz
cd spinnaker-4.2.0.46-amd64
sed -i 's|.*/etc/init.d/udev restart.*|    sudo systemctl restart systemd-udevd|' configure_spinnaker.sh
sudo sh install_spinnaker.sh
cd ..
rm -rf spinnaker-4.2.0.46-amd64
rm -f spinnaker-4.2.0.46-amd64-22.04-pkg.tar.gz
```

Python 3.8 wheel:

```bash
wget -O spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz https://flir.netx.net/file/asset/68776/original/attachment
tar xzf spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz
conda activate ZebVR3
pip install spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
rm -f spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
rm -f spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz
```


## Troubleshooting

if error 57 device already open, or if program is slower than usual

```bash
sudo killall python
```

error 11 unable to open XIMEA cameras: add user to the plugdev group

```bash
sudo usermod -a -G plugdev <user>
```

Permissions to access serial ports to interact with projector / temperature sensor:

```bash
sudo usermod -a -G dialout <user>
```

### Check number of uniforms

```python
from vispy import app, gloo
canvas = app.Canvas()
canvas.show()
app.process_events()

gpu_info = {
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
