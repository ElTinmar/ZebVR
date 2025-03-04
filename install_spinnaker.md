# Installing spinnaker for PointGrey camera

## Download SDK and python whl from Teledyne's website

https://www.teledynevisionsolutions.com/products/spinnaker-sdk

## Install dependencies

```
sudo apt-get install libusb-1.0-0 libpcre2-16-0 libdouble-conversion3 libxcb-xinput0 libxcb-xinerama0 qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools
```

## Install old version of ffmpeg

Spinnaker uses an old version of ffmpeg, install in environment

```
conda activate ZebVR2
conda install -c conda-forge ffmpeg==4.4.2
```


## Modify install script for newer systemctl

```
vim configure_spinnaker.sh
```

replace (line 77)

```
/etc/init.d/udev restart
```

with 

```
sudo systemctl restart systemd-udevd
```

## Install the SDK 

```
sudo sh install_spinnaker.sh
```

## Install python wheel

```
pip install ~/Downloads/spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04/spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
```
