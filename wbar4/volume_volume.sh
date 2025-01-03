#!/bin/bash

# output: integer number from 0 to 100


#_vol=`amixer sget Master|grep 'Front Left:'| awk -F ' ' '{print $5}'`
#echo -n "${_vol:1:2}"


_vol=`pactl get-sink-volume @DEFAULT_SINK@|grep 'front-left'| awk -F ' ' '{print $5}'`
echo -n "${_vol:0:2}"


# echo -n `wpctl get-volume @DEFAULT_AUDIO_SINK@| awk -F ' ' '{print $2}' | awk -F '.' '{print $2}'`
