from distutils.core import setup

setup(
    name='ZebVR',
    python_requires='>=3.8',
    author='Martin Privat',
    version='0.1.0',
    packages=['ZebVR'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='Open and closed-loop virtual reality',
    long_description=open('README.md').read(),
    install_requires=[
        "qt_widgets @ git+https://github.com/ElTinmar/qt_widgets.git@main",
        "tracker @ git+https://github.com/ElTinmar/tracker.git@main",
        "Lightcrafter @ git+https://github.com/ElTinmar/Lightcrafter.git@main",
        "email @ git+https://github.com/ElTinmar/email.git@main",
        "multiprocessing_logger @ git+https://github.com/ElTinmar/multiprocessing_logger.git@main",
        "video_tools @ git+https://github.com/ElTinmar/video_tools.git@main",
        "image_tools @ git+https://github.com/ElTinmar/image_tools.git@main",
        "camera_tools @ git+https://github.com/ElTinmar/camera_tools.git@main",
        "ipc_tools @ git+https://github.com/ElTinmar/ipc_tools.git@main",
        "image_saver @ git+https://github.com/ElTinmar/image_saver.git@main",
        "dagline @ git+https://github.com/ElTinmar/dagline.git@main",
        "daq_tools @ git+https://github.com/ElTinmar/daq_tools.git@main",
    ]
)