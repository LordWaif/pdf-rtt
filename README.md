# Ready To Train PDF (PDF-RTT)
This project is a Python-based PDF preprocessing tool. It provides various operations such as removing headers and footers, marking bounding boxes, removing tables, excluding lines, and saving the result as HTML or TXT.

### Getting Started
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites
You need to have Python installed on your machine. You can download Python [here](https://www.python.org/downloads/).

### Installing
Clone the repository to your local machine:
```
git clone git@github.com:LordWaif/pdf-rtt.git
```
Install the spacy and poppler:
```
apt install build-essential libpoppler-cpp-dev pkg-config python3-dev
python -m spacy download pt
python -m spacy download pt_core_news_sm
```
Install the required packages:
```
pip install -r requirements.txt
```
## Usage
The main functionality of the project is encapsulated in the preprocess_pdf function. Here is a basic usage example:
```
from preprocesser import preprocess_pdf

preprocess_pdf(
    file,
    isBbox=True,  
    out_file_bbox=out, 
    out_path_html=html, 
    out_path_txt=txt, 
    pages=pages, 
    min_chain=5, 
    max_lines_header=10, 
    max_lines_footer=10, 
    cross_similarities_header=False, 
    cross_similarities_footer=True, 
    verbose=True, 
    slice_window=3
)
```
### Api
```
uvicorn service:app --reload --port 19002 --host 0.0.0.0
celery -A celery_app worker --pool=threads --loglevel=info -Q rtt_queue

docker-compose -p rtt_services up -d
```
### License
This project is licensed under the MIT License - see the LICENSE.md file for details
