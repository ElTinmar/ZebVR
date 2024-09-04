# ZebVR

Virtual reality for zebrafish.

```
python ZebVR/main.py
```

## Installation

### Get code from github and create conda environment 

```
git clone https://github.com/ElTinmar/ZebVR.git
cd ZebVR
conda env create -f ZebVR.yml
conda activate ZebVR
conda develop . 
```

### CUDA

This seems necessary for now
TODO make that optional

```
sudo apt install nvidia-cuda-toolkit
```

### Install ximea package into environment
```
conda activate ZebVR
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