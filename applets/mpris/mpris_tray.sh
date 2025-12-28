#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir

python3 mpris_tray.py

cd $HOME
