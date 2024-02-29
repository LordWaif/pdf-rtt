#!/bin/bash

apt install build-essential libpoppler-cpp-dev pkg-config python3-dev
apt install ghostscript python3-tk
python3 -m spacy download pt
python3 -m spacy download pt_core_news_sm
pip3 install -r requirements.txt