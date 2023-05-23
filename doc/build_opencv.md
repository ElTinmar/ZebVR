# Why would you want to compile opencv yourself ?

opencv-python in PyPI doesn't ship with a lot of codec because of licensing issues.

# Go to conda environment

This is important, everything has to be done in the proper conda environment 

```
conda activate VirtualReality
```

# Install dependencies

```
sudo apt install build-essential cmake pkg-config unzip yasm git checkinstall \
libjpeg-dev libpng-dev libtiff-dev \
libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
libxvidcore-dev x264 libx264-dev libfaac-dev libmp3lame-dev libtheora-dev \
libfaac-dev libmp3lame-dev libvorbis-dev \
libgtk-3-dev libtbb-dev libatlas-base-dev gfortran \
libavcodec-dev libavformat-dev libavutil-dev libswscale-dev
```

# Download sources

Adapt to the version of opencv you want to install

```
wget -O opencv.zip https://github.com/opencv/opencv/archive/refs/tags/4.7.0.zip
wget -O opencv_contrib.zip  https://github.com/opencv/opencv_contrib/archive/refs/tags/4.7.0.zip
unzip opencv.zip
unzip opencv_contrib.zip
cd opencv-4.7.0
mkdir build
cd build
```

# Configure 

Modify OPENCV_EXTRA_MODULES_PATH accordingly

```
cmake -D WITH_CUDA=OFF \
-D BUILD_TIFF=ON \
-D BUILD_opencv_java=OFF \
-D WITH_OPENGL=ON \
-D WITH_OPENCL=ON \
-D WITH_IPP=ON \
-D WITH_TBB=ON \
-D WITH_EIGEN=ON \
-D WITH_V4L=ON \
-D WITH_VTK=OFF \
-D BUILD_TESTS=OFF \
-D BUILD_PERF_TESTS=OFF \
-D CMAKE_BUILD_TYPE=RELEASE \
-D BUILD_opencv_python2=OFF \
-D CMAKE_INSTALL_PREFIX=/usr/local \
-D PYTHON3_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
-D PYTHON3_PACKAGES_PATH=$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
-D INSTALL_C_EXAMPLES=ON \
-D INSTALL_PYTHON_EXAMPLES=ON \
-D OPENCV_ENABLE_NONFREE=ON \
-D OPENCV_GENERATE_PKGCONFIG=ON \
-D PYTHON3_EXECUTABLE=$(which python3) \
-D PYTHON_DEFAULT_EXECUTABLE=$(which python3) \
-D OPENCV_EXTRA_MODULES_PATH=/home/martin/Downloads/opencv_contrib-4.7.0/modules \
-D BUILD_EXAMPLES=ON ..
```

# Make sure configuration is correct

Look for the Python section in the output, it should look something like this

```
-- Python 3:
--  Interpreter:  /home/martin/miniconda3/envs/VirtualReality/bin/python3 (ver 3.8.16)
--  Libraries:    /home/martin/miniconda3/envs/VirtualReality/lib/libpython3.8.so (ver 3.8.16)
--  numpy:        /home/martin/miniconda3/envs/VirtualReality/lib/python3.8/site-packages/numpy/core/include (ver 1.24.2)
--  install path: /home/martin/miniconda3/envs/VirtualReality/lib/python3.8/site-packages/cv2/python-3.8
```

# Compile and install

```
make -j10
sudo make install
sudo ldconfig
```

# Troubleshooting

```
ImportError: /home/martin/miniconda3/envs/VirtualReality/bin/../lib/libstdc++.so.6: version `GLIBCXX_3.4.30' not found (required by /usr/local/lib/libopencv_gapi.so.407)
```

```
conda install -c conda-forge gcc=12.1.0
```