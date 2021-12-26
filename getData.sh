#!/bin/bash

cd ~/csgo-map-stats/

git pull

source .venv/bin/activate

python getData.py