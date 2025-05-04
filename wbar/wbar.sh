#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir
python3 wbar.py > /dev/null 2>&1 &
