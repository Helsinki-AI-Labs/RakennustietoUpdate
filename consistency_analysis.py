import os
import json
from typing import Dict, List, Any


def group_responses(batch_outputs_dir: str, output_file: str) -> None:
    grouped_data: Dict[str, Dict[str, List[Any]]] = {}
    varying_sections_data: Dict[str, Dict[str, List[str]]] = {}

    # Iterate over all JSON files in the batch_outputs directory
    for filename in os.listdir(batch_outputs_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(batch_outputs_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {file_path}: {e}")
                    continue

                for item in data:
                    custom_id = item.get("custom_id", "")
                    if not custom_id:
                        continue

                    # Split the custom_id into main filename and section
                    try:
                        main_filename, section = custom_id.rsplit("-", 1)
                        main_filename = main_filename.replace(
                            "-Section", ""
                        )  # Remove "-Section" from the key
                    except ValueError:
                        print(
                            f"Invalid custom_id format in file {file_path}: {custom_id}"
                        )
                        continue

                    # Initialize the main_filename key if not present
                    if main_filename not in grouped_data:
                        grouped_data[main_filename] = {}

                    # Initialize the section key if not present
                    if section not in grouped_data[main_filename]:
                        grouped_data[main_filename][section] = []

                    # Append only the content of the response to the array
                    response_body = item.get("response", {}).get("body", {})
                    message_content = (
                        response_body.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    grouped_data[main_filename][section].append(message_content)

    # Write the aggregated data to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grouped_data, f, ensure_ascii=False, indent=4)

    print(f"Grouped responses have been written to {output_file}")

    # Analysis: Count total sections, varying message contents, and identical message contents
    total_sections = 0
    varying_sections = 0
    identical_sections = 0

    EMPTY_RESPONSE_STRING = "Ei päivitettävää."

    for main_file, sections in grouped_data.items():
        for section, responses in sections.items():
            total_sections += 1
            unique_message_contents = set(responses)
            # Check if there are multiple unique responses and at least one is the empty response
            if (
                len(unique_message_contents) > 1
                and EMPTY_RESPONSE_STRING in unique_message_contents
            ):
                varying_sections += 1
                # Initialize the main_file key if not present
                if main_file not in varying_sections_data:
                    varying_sections_data[main_file] = {}
                # Add the section and its message contents (including duplicates)
                varying_sections_data[main_file][section] = responses
            else:
                identical_sections += 1

    print(f"Total sections: {total_sections}")
    print(f"Sections with varying message contents: {varying_sections}")
    print(f"Sections with identical message contents: {identical_sections}")

    # Write the varying sections data to a new file
    varying_output_file = "varying_sections.json"
    with open(varying_output_file, "w", encoding="utf-8") as f:
        json.dump(varying_sections_data, f, ensure_ascii=False, indent=4)

    print(f"Varying sections have been written to {varying_output_file}")


if __name__ == "__main__":
    batch_outputs_directory = "batch_outputs"
    output_json_file = "grouped_responses.json"
    group_responses(batch_outputs_directory, output_json_file)
