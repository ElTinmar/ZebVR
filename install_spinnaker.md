# Installing spinnaker for PointGrey camera

## Manually download SDK and python whl from Teledyne's website

https://www.teledynevisionsolutions.com/products/spinnaker-sdk

```bash
vim configure_spinnaker.sh
```

replace (line 77)

```bash
/etc/init.d/udev restart
```

with 

```bash
sudo systemctl restart systemd-udevd
```

Then install the SDK

```bash
sudo apt-get install libusb-1.0-0 libpcre2-16-0 libdouble-conversion3 libxcb-xinput0 libxcb-xinerama0 qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools
sudo sh install_spinnaker.sh
```

and install the python library

```bash
pip install ~/Downloads/spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04/spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
```

## Download and install SDK and python whl (this will break if they change URL)

Install SDK

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

Python wheel:

```bash
wget -O spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz https://flir.netx.net/file/asset/68776/original/attachment
tar xzf spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz
conda activate ZebVR3
pip install spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
rm -f spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64.whl
rm -f spinnaker_python-4.2.0.46-cp38-cp38-linux_x86_64-20.04.tar.gz
```
