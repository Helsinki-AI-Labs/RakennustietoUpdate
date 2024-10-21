import json
from typing import Dict, List, Any
from helpers import check_args_and_env_vars
from storage import list_files_in_dir, download_file


def is_empty_response(response: str) -> bool:
    return response.startswith("Ei päivitettävää") or response.startswith(
        "Valitettavasti"
    )


def group_responses(
    batch_outputs_bucket: str, batch_outputs_prefix: str, output_file: str
) -> None:
    """
    Groups responses from batch output files in GCS Storage.

    Args:
        batch_outputs_bucket (str): The name of the GCS bucket containing batch output files.
        batch_outputs_prefix (str): The prefix (directory) within the bucket to list batch output files.
        output_file (str): The local path to save the grouped responses.
    """
    grouped_data: Dict[str, Dict[str, Dict[str, List[Any]]]] = {}
    consistent_count = 0
    semi_consistent_count = 0
    not_consistent_count = 0

    # List all JSON files in the specified GCS bucket and prefix
    file_names = list_files_in_dir(batch_outputs_bucket, batch_outputs_prefix)

    for blob_name in file_names:
        if blob_name.endswith(".json"):
            response_content = download_file(batch_outputs_bucket, blob_name)
            if response_content is None:
                print(f"No content retrieved for {blob_name}")
                continue
            try:
                data = json.loads(response_content)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from blob {blob_name}: {e}")
                continue

            for item in data:
                custom_id = item.get("custom_id", "")
                if not custom_id:
                    continue

                try:
                    main_filename, section = custom_id.rsplit("-", 1)
                    main_filename = main_filename.replace("-Section", "")
                except ValueError:
                    print(f"Invalid custom_id format in blob {blob_name}: {custom_id}")
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

    # Save the grouped data to a local JSON file
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
    config = check_args_and_env_vars()
    # Define your GCS bucket and prefix where batch output files are stored
    batch_outputs_bucket = config["BUCKET_NAME"]
    batch_outputs_prefix = "batch_outputs"

    # Define the local output JSON file path
    output_json_file = "grouped_responses.json"

    group_responses(batch_outputs_bucket, batch_outputs_prefix, output_json_file)
