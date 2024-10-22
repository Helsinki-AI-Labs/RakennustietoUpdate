import json
import csv
from typing import List, Dict, Any

# Define Types
VotingData = Dict[str, Dict[str, Any]]
CsvRow = Dict[str, str]


def load_json(file_path: str) -> VotingData:
    """Load and parse JSON data from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_csv_rows(data: VotingData) -> List[CsvRow]:
    """Generate CSV rows from voting data by processing each item in parsed_voting_result."""
    rows: List[CsvRow] = []

    key_to_field = {
        "a. Otsikko:": "a_Otsikko",
        "b. Nykyinen sisältö:": "b_Nykyinen_sisalto",
        "c. Päivitystarve:": "c_Paivitystarve",
        "d. Viittaus uuteen lakiin:": "d_Viittaus_uuteen_lakiin",
    }

    for file_name, sections in data.items():
        for section_number, section_data in sections.items():
            parsed_voting_result = section_data.get("parsed_voting_result", {})

            # Ensure all values are lists
            for key, value in parsed_voting_result.items():
                if not isinstance(value, list):
                    parsed_voting_result[key] = [value]

            # Determine the number of entries based on the longest list
            max_entries = max(
                (len(v) for v in parsed_voting_result.values()), default=0
            )

            for i in range(max_entries):
                row: CsvRow = {
                    "file_name": file_name,
                    "section_number": section_number,
                }
                for key in key_to_field:
                    fieldname = key_to_field[key]
                    values = parsed_voting_result.get(key, [""] * max_entries)
                    if isinstance(values, list):
                        value = values[i] if i < len(values) else ""
                    else:
                        value = values if i == 0 else ""
                    row[fieldname] = value
                rows.append(row)
    return rows


def write_csv(rows: List[CsvRow], output_path: str) -> None:
    """Write CSV rows to a file."""
    fieldnames = [
        "file_name",
        "section_number",
        "a_Otsikko",
        "b_Nykyinen_sisalto",
        "c_Paivitystarve",
        "d_Viittaus_uuteen_lakiin",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_ALL,
            escapechar="\\",
            doublequote=True,
        )
        writer.writeheader()
        writer.writerows(rows)


def results_to_csv() -> None:
    """Main function to convert voting results JSON to CSV."""
    json_path = "voting_results.json"
    csv_path = "parsed_voting_results.csv"

    data = load_json(json_path)
    rows = generate_csv_rows(data)
    write_csv(rows, csv_path)
    print(f"CSV file '{csv_path}' has been written successfully.")


if __name__ == "__main__":
    results_to_csv()
