import json
import re
from typing import Dict, List

response_part_separators = [
    "\n\na. Otsikko:",
    "\n\nb. Nykyinen sisältö:",
    "\n\nc. Päivitystarve:",
    "\n\nd. Viittaus uuteen lakiin:",
]


# Handle the special case where 'd. Viittaus uuteen lakiin:' is missing
def handle_viittaus_uuteen_lakiin(entry_parts: Dict[str, str]) -> None:
    c_content = entry_parts.get("c. Päivitystarve:", "")
    if "d. Viittaus uuteen lakiin:" in c_content:
        # Split 'c. Päivitystarve:' into 'c' and 'd' parts
        c_part, d_part = c_content.split("d. Viittaus uuteen lakiin:", 1)
        entry_parts["c. Päivitystarve:"] = c_part.strip()
        entry_parts["d. Viittaus uuteen lakiin:"] = d_part.strip()
    else:
        # Find unique '{number} §' patterns in 'c. Päivitystarve:'
        matches = re.findall(r"\b\d+ §", c_content)
        unique_matches = list(
            dict.fromkeys(matches)
        )  # Remove duplicates while preserving order
        if unique_matches:
            entry_parts["d. Viittaus uuteen lakiin:"] = "\n".join(unique_matches)


def parse_response(response: str) -> Dict[str, List[str]]:
    labels = [
        "a. Otsikko:",
        "b. Nykyinen sisältö:",
        "c. Päivitystarve:",
        "d. Viittaus uuteen lakiin:",
    ]
    # Initialize a dictionary to hold lists of contents for each label
    parts: Dict[str, List[str]] = {label: [] for label in labels}

    # Split the response into individual entries using '####' as a separator
    entries = re.split(r"####\s*", response)

    for entry in entries:
        if entry.strip():
            entry_parts = {}
            # Regular expression pattern to match labels within an entry
            label_pattern = r"(a\. Otsikko:|b\. Nykyinen sisältö:|c\. Päivitystarve:|d\. Viittaus uuteen lakiin:)"
            # Split the entry based on the labels
            matches = re.split(label_pattern, entry)
            i = 1
            while i < len(matches):
                label = matches[i]
                content = matches[i + 1].strip()
                entry_parts[label] = content
                i += 2
            # Handle the special case where 'd. Viittaus uuteen lakiin:' is missing
            if "d. Viittaus uuteen lakiin:" not in entry_parts:
                handle_viittaus_uuteen_lakiin(entry_parts)
            # Append the parsed contents to the 'parts' dictionary
            for label in labels:
                parts[label].append(entry_parts.get(label, ""))
    return parts


def add_voting_results():

    # Load the data from 'grouped_responses.json'
    with open("grouped_responses.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Iterate over each file and its content
    for filename, file_data in data.items():
        for key, item in file_data.items():
            # Check if 'responses' key exists in the item
            if "responses" in item:
                non_empty_responses_count = item.get("non_empty_responses_count", 0)
                if non_empty_responses_count >= 2:
                    responses = item["responses"]
                    # Filter out empty responses ("Ei päivitettävää.")
                    non_empty_responses = [
                        resp for resp in responses if resp != "Ei päivitettävää."
                    ]
                    # If there are non-empty responses, find the longest one
                    if len(non_empty_responses) >= 2:
                        # Sort responses by length in descending order
                        sorted_responses = sorted(
                            non_empty_responses, key=len, reverse=True
                        )
                        second_longest_response = sorted_responses[1]
                        item["voting_result"] = second_longest_response

                        # Parse the second longest response into parts
                        parts = parse_response(second_longest_response)
                        item["parsed_voting_result"] = parts
                    elif non_empty_responses:
                        # If there's only one non-empty response, use that
                        item["voting_result"] = non_empty_responses[0]
                        parts = parse_response(non_empty_responses[0])
                        item["parsed_voting_result"] = parts
                    else:
                        # If somehow there are no non-empty responses, set voting_result to "-"
                        item["voting_result"] = "-"
                else:
                    # If non-empty responses count is less than 2, set voting_result to "-"
                    item["voting_result"] = "-"
            else:
                # If 'responses' key does not exist, you might want to handle it or skip
                pass

    # Save the updated data to 'voting_results.json'
    with open("voting_results.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    add_voting_results()
