# ZebVR

Virtual reality for zebrafish.

```
python -m ZebVR
```

## Using .desktop

Change the content depending on where ZebVR was downloaded


(Otional) If you change settings and want to check syntax:
```
desktop-file-validate ZebVR.desktop
```

```
cp ZebVR.desktop ~/.local/share/applications/
```

## Installation

### Get code from github and create conda environment 



```
git clone https://github.com/ElTinmar/ZebVR.git
cd ZebVR
conda env create -f ZebVR.yml
conda activate ZebVR
```

### Allow the python interpreter to set scheduler

```
sudo setcap cap_sys_nice=eip /home/martinprivat/miniconda3/envs/ZebVR2/bin/python3.8
```

### CPU shield and affinity

```
sudo apt install cpuset
```

```
sudo cset shield --cpu 1-31 --kthread=on
sudo cset shield --exec bash
su username
conda activate ZebVR2
python -m ZebVR
```

```
sudo cset shield --reset
```

### CUDA

This seems necessary for now
TODO make that optional

```
sudo apt install nvidia-cuda-toolkit
```

### Install ximea package into environment
```
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

### Install CUDA



## Troubleshooting

if error 57 device already open, or if program is slower than usual

```
sudo killall python
```

error 11 unable to open XIMEA cameras: add user to the plugdev group

```
sudo usermod -a -G plugdev <user>
```
