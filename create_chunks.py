import os
import time
import json
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, operations
from unstructured_client.models.errors import SDKError

from helpers import check_args_and_env_vars


def process_pdf_file(
    relative_path: str,
    from_dir: str,
    to_dir: str,
    client: UnstructuredClient,
):
    input_path = os.path.join(from_dir, relative_path)
    output_path = os.path.join(to_dir, os.path.splitext(relative_path)[0] + ".json")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Check if the output file already exists
    if os.path.exists(output_path):
        print(f"Skipping {relative_path} as output file already exists.")
        return 0, 1  # files_processed, files_skipped

    with open(input_path, "rb") as file:
        print(f"Processing {relative_path}...")
        req = operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=shared.Files(
                    content=file.read(),
                    file_name=relative_path,
                ),
                strategy=shared.Strategy.HI_RES,
                languages=["fin"],
                content_type="application/pdf",
                split_pdf_concurrency_level=15,
            ),
        )

    start_time = time.time()
    try:
        # Update the partition call to use the keyword argument 'request'
        res = client.general.partition(request=req)
        end_time = time.time()
        print(
            f"Processed {relative_path}. Time elapsed: {end_time - start_time:.2f} seconds"
        )

        with open(output_path, "w") as json_file:
            json.dump([element for element in res.elements], json_file, indent=4)

        return 1, 0  # files_processed, files_skipped

    except SDKError as e:
        print(e)
        return 0, 0


def process_files(from_dir: str, client: UnstructuredClient, to_dir: str):
    files_processed = 0
    files_skipped = 0
    filenames_to_process = []

    # Collect all files to process
    for root, _, filenames in os.walk(from_dir):
        for filename in sorted(filenames):
            relative_path = os.path.relpath(os.path.join(root, filename), from_dir)
            filenames_to_process.append(relative_path)

    # Initialize tqdm progress bar
    for relative_path in filenames_to_process:
        processed, skipped = process_pdf_file(relative_path, from_dir, to_dir, client)
        files_processed += processed
        files_skipped += skipped

    print(
        f"All done. Processed {files_processed} files. Skipped {files_skipped} files."
    )


if __name__ == "__main__":
    required_args = ["--from_dir", "--to_dir"]
    required_env_vars = ["UNSTRUCTURED_API_KEY", "UNSTRUCTURED_SERVER_URL"]

    config = check_args_and_env_vars(
        required_args=required_args, required_env_vars=required_env_vars
    )

    client = UnstructuredClient(
        api_key_auth=config.get("UNSTRUCTURED_API_KEY"),
        server_url=config.get("UNSTRUCTURED_SERVER_URL"),
    )

    from_dir: str = config.get("FROM_DIR")
    to_dir: str = config.get("TO_DIR")

    process_files(from_dir, client, to_dir)
