# Income Statement PDF Extractor

## Description

This script extracts financial data from a PDF income statement by using pdfplumber to read the text and a combination of regular expressions and token normalization to identify line items and numeric values. It calculates derived values like Gross Profit and includes sub-items such as Basic and Diluted EPS and Weighted Average Shares Outstanding in the final CSV.

Usage

**Create and Activate your virtual environment first**

install the required dependencies 

```
pip install -r requirements.txt
```

run the script

```
python main.py [path_to_pdf]
```

If no PDF path is provided, it defaults to test.pdf.

Output CSV file is saved as Income_Statement.csv.

Requirements

- Python 3.9+

- pandas

- pdfplumber
