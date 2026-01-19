import sys
import pdfplumber
import pandas as pd
import re

DEFAULT_INPUT_FILE_PATH = 'test.pdf'
OUTPUT_FILE_PATH = 'Income_Statement.csv'


TARGET_ROW_MAPPING = {
    'Total revenues': 'Total revenues',
    'Income (loss) from operations': 'Operating income',
    'Net income (loss)': 'Net Income',
    'Costs of revenues': 'Costs of revenues'
}

TOTAL_REVENUE = []

CURRENT_BASIC_SECTION = None
CURRENT_DILUTED_SECTION = None



VALUE_RE = re.compile(
    r"""
    ^\$?              # optional dollar sign
    \(?               # optional opening parenthesis
    -?                # optional minus
    \d[\d,]*          # digits with commas
    (\.\d+)?          # optional decimals
    \)?$              # optional closing parenthesis
    """,
    re.VERBOSE
)


def is_value_token(token: str) -> bool:
    return bool(VALUE_RE.match(token.strip()))


def parse_number(token: str) -> float:
    """
    Converts financial number string to float
    (3,455) -> -3455
    $1,234  -> 1234
    """
    t = token.replace("$", "").replace(",", "").strip()

    negative = False
    if t.startswith("(") and t.endswith(")"):
        negative = True
        t = t[1:-1]

    value = float(t)
    return -value if negative else value



def normalize_data(tokens):
    """
    tokens: list[str]
    returns:
      line_item: str
      values: list[float]
    """
    line_item_parts = []
    values = []
    buffer = ""

    number_started = False

    for token in tokens:
        token = token.strip()

        # Handle split tokens like "$" "(3,555)"
        if token in {"$", "(", ")"}:
            buffer += token
            continue

        candidate = buffer + token
        buffer = ""

        if not number_started and not is_value_token(candidate):
            line_item_parts.append(candidate)
        else:
            number_started = True
            if is_value_token(candidate):
                values.append(parse_number(candidate))

    line_item = " ".join(line_item_parts)
    return line_item, values

def get_gross_profit_values(values):
    if TOTAL_REVENUE is not None:
        gross_profit_values = [x-y for x,y in zip(TOTAL_REVENUE, values)]
        return gross_profit_values


def get_target(splited_text):
    global CURRENT_BASIC_SECTION
    global CURRENT_DILUTED_SECTION
    line_item, values = normalize_data(splited_text)


    if TARGET_ROW_MAPPING.get(line_item):
        if TARGET_ROW_MAPPING.get(line_item) == 'Total revenues':
            TOTAL_REVENUE.extend(values)
        if TARGET_ROW_MAPPING.get(line_item) == 'Costs of revenues':
            line_item = 'Gross profit'
            values = get_gross_profit_values(values)
    
        return line_item, values

    # Handle Basic / Diluted under a section
    if line_item == 'Basic':
        full_name = None
        if not CURRENT_BASIC_SECTION:
            CURRENT_BASIC_SECTION = 'EPS'
        else:
            CURRENT_BASIC_SECTION = 'Weighted average shares outstanding'

        full_name = f"{CURRENT_BASIC_SECTION}-{line_item}"
        return full_name, values

    if line_item == 'Diluted':
        full_name = None
        if not CURRENT_DILUTED_SECTION:
            CURRENT_DILUTED_SECTION = 'EPS'
        else:
            CURRENT_DILUTED_SECTION = 'Weighted average shares outstanding'

        full_name = f"{CURRENT_DILUTED_SECTION}-{line_item}"
        return full_name, values

    return None, None



def should_be_dropped(splited_text):
    line_item, values = normalize_data(splited_text)

    if line_item in {'Basic', 'Diluted'}:
        return False

    if len(values) <= 1:
        return True
    return False


def extract_data_points(line):
    result = {}
    text = line.get('text')
    splited_text = text.split(' ')
    dropped = should_be_dropped(splited_text)

    if dropped:
        return None

    line_item, values = get_target(splited_text)
    if line_item is not None and values is not None:
        result['line_item'] = line_item
        result['q2_2025'] = values[0]
        result['q1_2025'] = values[1]
        result['q2_2024'] = values[2]
        result['six_months_2025'] = values[3]
        result['six_months_2024'] = values[4]

        if line_item in ['EPS-Basic', 'EPS-Diluted', 'Weighted average shares outstanding-Basic', 'Weighted average shares outstanding-Diluted']:
            result['unit'] = 'per share'
        else:
            result['unit'] = 'in thousands'
    
    
    return result


def get_data_points(page):
    TOP = 160
    ROW_HEIGHT = 670
    LEFT_BOUND = 14
    RIGHT_BOUND = 580
    BOTTOM = TOP+ROW_HEIGHT

    target_area = page.crop((LEFT_BOUND, TOP, RIGHT_BOUND, BOTTOM))

    final_result = []
    try:
        lines = target_area.extract_text_lines()

        if lines is not None:
            for line in lines:
                result = extract_data_points(line)
                if result is None or result == {}:
                    pass
                else:
                    final_result.append(result)
        TOP += ROW_HEIGHT
        BOTTOM += ROW_HEIGHT
    except Exception as e:
        print(e)
            

    return final_result

 

def get_table_data(input_path):
    try:
        with pdfplumber.open(input_path) as pdf:
            target_page = pdf.pages[7]

            data = get_data_points(target_page)

            return data
            

    except Exception as e:
        print(e)
        return None



def main():
    input_file = None
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = DEFAULT_INPUT_FILE_PATH

    data = get_table_data(input_file)

    if data is not None:
        df = pd.DataFrame(data)

        df.to_csv(OUTPUT_FILE_PATH, index=False)

        print("SUCESSFULLY EXTRACTED DATA")

    sys.exit(1)

if __name__ == '__main__':
    main()