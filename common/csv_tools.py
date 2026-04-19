import csv
import io
import logging
from typing import List, Dict

logger = logging.getLogger('contactmailer')

def parse_csv(file_content: str, column_mapping: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Reads CSV and maps columns based on dictionary mapping.
    Uses map() to strip whitespace from headers.
    Returns a list of parsed dictionaries.
    """
    logger.info(f"Parsing CSV with mapping: {column_mapping}")
    f = io.StringIO(file_content)
    reader = csv.reader(f)
    
    try:
        headers = next(reader)
        # using map() to clean headers as required
        cleaned_headers = list(map(str.strip, headers))
    except StopIteration:
        logger.warning("Attempted to parse empty CSV file.")
        return []

    # create a reversed map: CSV column name -> Model field name
    # example mapping input: {'Name': 'Contact Name', 'Email': 'Email Address', ...}
    reverse_map = column_mapping
    
    # Identify the index for each model field based on header
    index_map = {}
    for i, col in enumerate(cleaned_headers):
        if col in reverse_map:
            index_map[reverse_map[col]] = i

    results = []
    for row_num, row in enumerate(reader, start=2):
        row = list(map(str.strip, row))
        try:
            entry = {}
            for model_field, idx in index_map.items():
                if idx < len(row):
                    entry[model_field] = row[idx]
                else:
                    entry[model_field] = ""
            if entry:
                results.append(entry)
        except Exception as e:
            logger.error(f"Error parsing row {row_num}: {e}")

    logger.info(f"Successfully parsed {len(results)} rows from CSV.")
    return results

def generate_csv(data: List[Dict[str, str]], columns: List[str]) -> str:
    """
    Generates CSV string from list of dicts.
    """
    f = io.StringIO()
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(data)
    return f.getvalue()
