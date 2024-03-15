#!/bin/bash

apt install build-essential libpoppler-cpp-dev pkg-config python3-dev -y
apt install ghostscript python3-tk
pip3 install -r requirements.txt
python3 -m spacy download pt_core_news_sm