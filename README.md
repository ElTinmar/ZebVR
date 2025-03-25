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
conda env create -f ZebVR2.yml
conda activate ZebVR2
```

### Allow the python interpreter to set scheduler

```bash
sudo setcap cap_sys_nice=eip /home/martinprivat/miniconda3/envs/ZebVR2/bin/python3.8
```

### CPU shield and affinity

```bash
sudo apt install cpuset
```

```bash
sudo cset shield --cpu 1-31 --kthread=on
sudo cset shield --exec bash
su username
conda activate ZebVR2
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
conda activate ZebVR2
wget https://www.ximea.com/downloads/recent/XIMEA_Linux_SP.tgz
tar xzf XIMEA_Linux_SP.tgz
cd package
./install -pcie
cp -r api/Python/v3/ximea "${CONDA_PREFIX}/lib/python3.8/site-packages/"
cd ..
rm -f XIMEA_Linux_SP.tgz
rm -rf package
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

### Check number of uniforms

```
from vispy import app, gloo
canvas = app.Canvas()
canvas.show()
app.process_events()
info = gloo.gl.glGetParameter(gloo.gl.GL_MAX_FRAGMENT_UNIFORM_VECTORS)
print("Max Fragment Uniform Vectors:", info)
canvas.close()
```
