# Installing spinnaker for PointGrey camera

## Download SDK and python whl from Teledyne's website

https://www.teledynevisionsolutions.com/products/spinnaker-sdk

Install SDK

```bash
wget -O spinnaker-4.2.0.46-amd64-20.04-pkg.tar.gz https://flir.netx.net/file/asset/68777/original/attachment
tar xzf spinnaker-4.2.0.46-amd64-20.04-pkg.tar.gz
cd spinnaker-4.2.0.46-amd64
sed -i 's|.*/etc/init.d/udev restart.*|    sudo systemctl restart systemd-udevd|' configure_spinnaker.sh
sudo sh install_spinnaker.sh
cd ..
rm -rf spinnaker-4.2.0.46-amd64
rm -f spinnaker-4.2.0.46-amd64-20.04-pkg.tar.gz
```

Python wheel:

```bash
wget -O spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz https://flir.netx.net/file/asset/68776/original/attachment
tar xzf spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz
conda activate ZebVR3
pip install spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
rm -f spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
rm -f spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz
```

## Install dependencies

```bash
sudo apt-get install libusb-1.0-0 libpcre2-16-0 libdouble-conversion3 libxcb-xinput0 libxcb-xinerama0 qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools
```

## Install old version of ffmpeg

Spinnaker uses an old version of ffmpeg, install in environment

```bash
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
