#!/bin/bash
file=${1--}
d_date=`date +%s`
touch clips/$d_date
echo `cat -- "$file"` >> clips/$d_date
