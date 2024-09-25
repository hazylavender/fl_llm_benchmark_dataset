#!/bin/sh
YEAR=2024
MONTH=8
python3 ca_parliament.py -y $YEAR -m $MONTH
python3 gbr_parliament.py -y $YEAR -m $MONTH
python3 us_congress.py -y $YEAR -m $MONTH
python3 postprocess.py -y $YEAR -m $MONTH