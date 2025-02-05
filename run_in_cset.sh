#!/bin/bash

cset shield --cpu 2-31 --kthread on
cset shield --user martinprivat --exec bash -c 'conda activate ZebVR2 && cd /home/martin/Development/ZebVR && python ZebVR/main.py'
cset shield --reset