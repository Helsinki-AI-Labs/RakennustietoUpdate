import os
import json
from typing import Dict, List, Any


def is_empty_response(response: str) -> bool:
    return response.startswith("Ei päivitettävää") or response.startswith(
        "Valitettavasti"
    )


def group_responses(batch_outputs_dir: str, output_file: str) -> None:
    grouped_data: Dict[str, Dict[str, Dict[str, List[Any]]]] = {}
    consistent_count = 0
    semi_consistent_count = 0
    not_consistent_count = 0

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

                    try:
                        main_filename, section = custom_id.rsplit("-", 1)
                        main_filename = main_filename.replace("-Section", "")
                    except ValueError:
                        print(
                            f"Invalid custom_id format in file {file_path}: {custom_id}"
                        )
                        continue

                    if main_filename not in grouped_data:
                        grouped_data[main_filename] = {}

                    if section not in grouped_data[main_filename]:
                        grouped_data[main_filename][section] = {"responses": []}

                    response_body = item.get("response", {}).get("body", {})
                    message_content = (
                        response_body.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                    grouped_data[main_filename][section]["responses"].append(
                        message_content
                    )

    # Calculate consistency counts per section
    for main_filename, sections in grouped_data.items():
        for section, details in sections.items():
            responses = details["responses"]
            empty_responses_count = sum(
                1 for response in responses if is_empty_response(response)
            )
            non_empty_responses_count = len(responses) - empty_responses_count

            details["empty_responses_count"] = empty_responses_count
            details["non_empty_responses_count"] = non_empty_responses_count

            is_consistent = empty_responses_count == 0 or empty_responses_count == len(
                responses
            )
            details["is_consistent"] = is_consistent

            is_semi_consistent = not is_consistent and (
                empty_responses_count == 1 or non_empty_responses_count == 1
            )
            details["is_semi_consistent"] = is_semi_consistent

            if is_consistent:
                consistent_count += 1
            elif is_semi_consistent:
                semi_consistent_count += 1
            else:
                not_consistent_count += 1

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grouped_data, f, ensure_ascii=False, indent=4)

    print(f"Grouped responses have been written to {output_file}")
    print(
        f"Total sections: {consistent_count + semi_consistent_count + not_consistent_count}"
    )
    print(f"Consistent sections: {consistent_count}")
    print(f"Semi-consistent sections: {semi_consistent_count}")
    print(f"Not consistent sections: {not_consistent_count}")


if __name__ == "__main__":
    batch_outputs_directory = "batch_outputs"
    output_json_file = "grouped_responses.json"
    group_responses(batch_outputs_directory, output_json_file)
