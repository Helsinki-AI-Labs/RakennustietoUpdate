import json
from typing import List, TypedDict

from llm import (
    OpenAI,
    create_batch_job,
    poll_batch_status,
    prepare_batch_input,
    retrieve_batch_results,
    upload_batch_file,
)
from helpers import (
    check_args_and_env_vars,
)
from storage import (
    download_file,
    list_files_in_dir,
)


class Section(TypedDict):
    title: str
    content: List[str]


class Completion(TypedDict):
    title: str
    content: List[str]
    input: str
    output: str


with open("new-construction-law.txt", "r", encoding="utf-8") as file:
    law_text = file.read()

if not law_text:
    raise ValueError("new-construction-law.txt is empty")


def main() -> None:
    """
    Main function to process sections using OpenAI's Batch API and upload analysis to the storage bucket.
    """
    # Load environment variables and command-line arguments
    config = check_args_and_env_vars(
        required_env_vars=[
            "OPENAI_API_KEY",
            "BUCKET_NAME",
            "SECTIONS_JSON_DIR",
            "ANALYSIS_DIR",
            "COMPLETIONS_FILE",  # Path to save completions
        ],
    )

    api_key: str = config["OPENAI_API_KEY"]
    bucket_name = config["BUCKET_NAME"]
    json_sections_dir = config["SECTIONS_JSON_DIR"]
    completions_file = config["COMPLETIONS_FILE"]

    client = OpenAI(api_key=api_key)

    with open("new-construction-law.txt", "r", encoding="utf-8") as file:
        new_construction_law: str = file.read()

    if not new_construction_law:
        raise ValueError("new-construction-law.txt is empty")

    section_filenames = list_files_in_dir(
        bucket_name=bucket_name,
        prefix=json_sections_dir,
    )

    for filename in section_filenames:
        if not filename.endswith(".json"):
            continue

        source_blob_name: str = filename  # Using the filename directly

        sections_contents = download_file(bucket_name, source_blob_name)

        try:
            sections: List[Section] = json.loads(sections_contents)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {filename}: {e}")
            continue

        # Prepare batch input file
        batch_input_path = prepare_batch_input(sections, filename)

        # Upload batch input file
        batch_input_file_id = upload_batch_file(client, batch_input_path)

        # Create batch job
        batch_id = create_batch_job(client, batch_input_file_id)

        print(f"Batch job {batch_id} created. Waiting for completion...")

        # Poll for batch status
        batch = poll_batch_status(client, batch_id)

        if batch.status != "completed":
            print(
                f"Batch job {batch_id} did not complete successfully. Status: {batch.status}"
            )
            continue

        # Retrieve batch results
        output_file_id = batch.output_file_id
        if not output_file_id:
            print(f"No output file for batch job {batch_id}.")
            continue

        results = retrieve_batch_results(client, output_file_id)

        # save results to local file
        with open(f"{output_file_id}.json", "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4)

        # # Process results
        # analysis_content = process_batch_results(results, filename)

        # destination_blob_name: str = (
        #     f"analysis/{os.path.splitext(basename(filename))[0]}.txt"
        # )

        # upload_file_to_bucket(
        #     bucket_name=bucket_name,
        #     destination_blob_name=destination_blob_name,
        #     file_contents=analysis_content,
        # )
        # print(f"Analysis complete for {filename}. Uploaded to {destination_blob_name}")

        # current_time = datetime.now(timezone.utc).isoformat()
        # update_state(filename, {"analysedAt": current_time})


if __name__ == "__main__":
    main()
