import datetime
import json
import os
from posixpath import basename
from typing import Dict, List, TypedDict

from llm import (
    create_batch_job,
    poll_batch_status,
    process_batch_results,
    retrieve_batch_results,
)
from helpers import check_args_and_env_vars, update_state
from storage import (
    upload_file_to_bucket,
)
from prepare_batches import prepare_batches


class Section(TypedDict):
    title: str
    content: List[str]


class Completion(TypedDict):
    title: str
    content: List[str]
    input: str
    output: str


def main() -> None:
    prepared_batches = prepare_batches()
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

    for batch_input_file_id, batch_filenames in prepared_batches.items():
        try:
            batch_start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            batch_id = create_batch_job(batch_input_file_id)
            print(f"Batch job {batch_id} created. Waiting for completion...")

            batch = poll_batch_status(batch_id)

            if batch.status != "completed":
                print(
                    f"Batch job {batch_id} did not complete successfully. Status: {batch.status}"
                )
                fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for filename in batch_filenames:
                    update_state(filename, {"batchProcessingFailedAt": fail_time})
                continue

            output_file_id = batch.output_file_id
            if not output_file_id:
                print(f"No output file for batch job {batch_id}.")
                fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for filename in batch_filenames:
                    update_state(filename, {"batchProcessingFailedAt": fail_time})
                continue

            results = retrieve_batch_results(output_file_id)

            os.makedirs("batch_outputs", exist_ok=True)
            output_file_path = os.path.join("batch_outputs", f"{output_file_id}.json")
            with open(output_file_path, "w", encoding="utf-8") as file:
                json.dump(results, file, indent=4)

            batch_output_blob_name = f"batch_outputs/{output_file_id}.json"
            upload_file_to_bucket(
                bucket_name=bucket_name,
                destination_blob_name=batch_output_blob_name,
                source_file_path=output_file_path,
            )
            print(f"Batch output file uploaded to {batch_output_blob_name}")

            analysis_content = process_batch_results(results, batch_filenames, {})

            for filename in batch_filenames:
                destination_blob_name: str = (
                    f"analysis/{os.path.splitext(basename(filename))[0]}.txt"
                )

                file_analysis = "\n".join(
                    [
                        section_analysis
                        for section_analysis in analysis_content
                        if section_analysis.startswith(
                            f"Source File: {basename(filename)}"
                        )
                    ]
                )

                upload_file_to_bucket(
                    bucket_name=bucket_name,
                    destination_blob_name=destination_blob_name,
                    file_contents=file_analysis,
                )
                print(
                    f"Analysis complete for {filename}. Uploaded to {destination_blob_name}"
                )

                completion_time = datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat()
                update_state(filename, {"batchProcessingCompletedAt": completion_time})

            batch_end_time = datetime.datetime.now(datetime.timezone.utc)
            elapsed_time = batch_end_time - datetime.datetime.fromisoformat(
                batch_start_time
            )
            print(
                f"Batch {batch_id} completed at {batch_end_time.isoformat()} with elapsed time: {elapsed_time}."
            )

        except Exception as e:
            print(f"An error occurred while processing the batch: {e}")
            fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for filename in batch_filenames:
                update_state(filename, {"batchProcessingFailedAt": fail_time})


if __name__ == "__main__":
    main()
