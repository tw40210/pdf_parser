## SETUP
- pip install -r requirements/requirements.txt
- install Tesseract
  (from https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.1.20230401.exe)
- set tesseract_cmd in `main.py`
- put `example.pdf` in `/data`
## RUN
`python ./src/main.py`

output: `data/memo_merged.txt`