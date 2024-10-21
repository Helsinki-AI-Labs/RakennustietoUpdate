import datetime
import json
import os
import time
import tempfile
from typing import Dict, List

from llm import (
    create_batch_job,
    poll_batch_status,
    process_batch_results,
    retrieve_batch_results,
    upload_batch_file,
)
from helpers import check_args_and_env_vars, update_state
from storage import list_files_in_dir, download_file, upload_file_to_bucket


def main() -> None:
    config = check_args_and_env_vars(
        required_env_vars=[
            "OPENAI_API_KEY",
            "BUCKET_NAME",
            "ANALYSIS_DIR",
            "COMPLETIONS_FILE",
        ],
    )
    bucket_name: str = config["BUCKET_NAME"]
    batch_inputs_prefix: str = "batch_inputs/"

    # Retrieve prepared batch input files from the bucket
    batch_input_files = list_files_in_dir(
        bucket_name=bucket_name,
        prefix=batch_inputs_prefix,
    )

    if not batch_input_files:
        print("No prepared batch input files found in the bucket.")
        return

    prepared_batches: Dict[str, List[str]] = {}

    for batch_input_file in batch_input_files:
        try:
            # Derive the batch_input_file_id from the filename
            batch_input_file_id = os.path.splitext(os.path.basename(batch_input_file))[
                0
            ]

            # Download the batch input file content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_path = temp_file.name
                file_content = download_file(bucket_name, batch_input_file)
                temp_file.write(file_content.encode("utf-8"))

            # Upload the batch input file to OpenAI
            upload_response_id = upload_batch_file(temp_file_path)

            # Remove the temporary file
            os.remove(temp_file_path)

            # Create batch job
            batch_id = create_batch_job(upload_response_id)
            print(
                f"Batch job {batch_id} created for input file ID {batch_input_file_id}."
            )

            # Parse the JSONL content
            batch_requests = [
                json.loads(line) for line in file_content.splitlines() if line.strip()
            ]

            # Extract unique filenames from custom_ids
            batch_filenames = list(
                {req["custom_id"].split("-Section-")[0] for req in batch_requests}
            )

            if not batch_filenames:
                print(f"No batch filenames found in {batch_input_file}. Skipping.")
                continue

            prepared_batches[batch_id] = batch_filenames

        except Exception as e:
            print(f"Failed to process batch input file {batch_input_file}: {e}")
            fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for filename in prepared_batches.get(batch_input_file_id, []):
                update_state(filename, {"batchProcessingFailedAt": fail_time})

    if not prepared_batches:
        print("No valid prepared batches to process.")
        return

    start_time = datetime.datetime.now(datetime.timezone.utc)
    print(f"Started processing batches at {start_time.isoformat()}.")

    pending_batches: Dict[str, List[str]] = prepared_batches.copy()
    completed_batches: Dict[str, List[str]] = {}
    failed_batches: Dict[str, List[str]] = {}

    while pending_batches:
        for batch_id in list(pending_batches.keys()):
            try:
                batch = poll_batch_status(batch_id)
                if batch.status == "completed":
                    print(f"Batch job {batch_id} completed.")
                    completed_batches[batch_id] = pending_batches.pop(batch_id)
                    process_batch(batch_id, completed_batches[batch_id], bucket_name)
                elif batch.status == "failed":
                    print(f"Batch job {batch_id} failed.")
                    failed_batches[batch_id] = pending_batches.pop(batch_id)
                    fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    for filename in failed_batches[batch_id]:
                        update_state(filename, {"batchProcessingFailedAt": fail_time})
                else:
                    print(f"Batch job {batch_id} status: {batch.status}.")
            except Exception as e:
                print(f"Error polling status for batch {batch_id}: {e}")
        elapsed_time = datetime.datetime.now(datetime.timezone.utc) - start_time
        print(f"Elapsed time: {elapsed_time}. Pending batches: {len(pending_batches)}.")
        time.sleep(10)  # Wait before next polling cycle

    end_time = datetime.datetime.now(datetime.timezone.utc)
    total_elapsed = end_time - start_time
    print(
        f"All batches processed by {end_time.isoformat()}. Total elapsed time: {total_elapsed}."
    )


def process_batch(batch_id: str, batch_filenames: List[str], bucket_name: str) -> None:
    try:
        batch = poll_batch_status(batch_id)
        output_file_id = batch.output_file_id
        if not output_file_id:
            print(f"No output file for batch job {batch_id}.")
            fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for filename in batch_filenames:
                update_state(filename, {"batchProcessingFailedAt": fail_time})
            return

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
                f"analysis/{os.path.splitext(os.path.basename(filename))[0]}.txt"
            )

            file_analysis = "\n".join(
                [
                    section_analysis
                    for section_analysis in analysis_content
                    if section_analysis.startswith(
                        f"Source File: {os.path.basename(filename)}"
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

            completion_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
            update_state(filename, {"batchProcessingCompletedAt": completion_time})

    except Exception as e:
        print(f"An error occurred while processing batch {batch_id}: {e}")
        fail_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for filename in batch_filenames:
            update_state(filename, {"batchProcessingFailedAt": fail_time})


if __name__ == "__main__":
    main()
