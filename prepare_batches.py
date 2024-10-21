import datetime
import json
import os
from posixpath import basename
from typing import Dict, List, TypedDict
import dotenv

dotenv.load_dotenv()

from llm import prepare_batch_input, upload_batch_file
from helpers import check_args_and_env_vars, update_state
from storage import download_file, list_files_in_dir, upload_file_to_bucket


class Section(TypedDict):
    title: str
    content: List[str]


def prepare_batches() -> Dict[str, List[Dict[str, str]]]:
    config = check_args_and_env_vars(
        required_env_vars=[
            "OPENAI_API_KEY",
            "BUCKET_NAME",
            "SECTIONS_JSON_DIR",
            "ANALYSIS_DIR",
            "COMPLETIONS_FILE",
        ],
    )

    bucket_name = config["BUCKET_NAME"]
    json_sections_dir = config["SECTIONS_JSON_DIR"]

    with open("new-construction-law.txt", "r", encoding="utf-8") as file:
        new_construction_law: str = file.read()

    if not new_construction_law:
        raise ValueError("new-construction-law.txt is empty")

    section_filenames = list_files_in_dir(
        bucket_name=bucket_name,
        prefix=json_sections_dir,
    )

    json_filenames = [fn for fn in section_filenames if fn.endswith(".json")]

    batch_size = 10
    total_batches = (len(json_filenames) + batch_size - 1) // batch_size
    prepared_batches = {}

    for i in range(0, len(json_filenames), batch_size):
        batch_number = i // batch_size + 1
        batch_filenames = json_filenames[i : i + batch_size]

        batch_start_time = datetime.datetime.now(datetime.timezone.utc)
        print(
            f"Batch {batch_number}/{total_batches} started at {batch_start_time.isoformat()} with {len(batch_filenames)} files."
        )

        start_time_iso = batch_start_time.isoformat()
        for filename in batch_filenames:
            update_state(filename, {"batchProcessingStartAt": start_time_iso})

        batch_input_sections = []
        sections_dict: Dict[str, Section] = {}

        for filename in batch_filenames:
            source_blob_name: str = filename

            sections_contents = download_file(bucket_name, source_blob_name)

            try:
                sections: List[Section] = json.loads(sections_contents)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}")
                fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                update_state(filename, {"batchProcessingFailedAt": fail_time})
                continue

            for index, section in enumerate(sections, start=1):
                custom_id = f"{basename(filename)}-Section-{index}"
                sections_dict[custom_id] = section
                batch_input_sections.append(
                    {"custom_id": custom_id, "section": section}
                )

        if not batch_input_sections:
            print("No valid sections to process in this batch.")
            fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for filename in batch_filenames:
                update_state(filename, {"batchProcessingFailedAt": fail_time})
            continue

        batch_input_path = prepare_batch_input(
            batch_input_sections, new_construction_law
        )

        batch_input_blob_name = f"batch_inputs/{os.path.basename(batch_input_path)}"
        upload_file_to_bucket(
            bucket_name=bucket_name,
            destination_blob_name=batch_input_blob_name,
            source_file_path=batch_input_path,
        )
        print(f"Batch input file uploaded to {batch_input_blob_name}")

        batch_input_file_id = upload_batch_file(batch_input_path)

        prepared_batches[batch_input_file_id] = batch_filenames

    return prepared_batches


if __name__ == "__main__":
    prepare_batches()
