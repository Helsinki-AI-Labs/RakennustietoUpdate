import os
import time
import json
from google.api_core.client_options import ClientOptions
from google.cloud import documentai

from helpers import check_args_and_env_vars


def process_pdf_file(
    relative_path: str,
    from_dir: str,
    to_dir: str,
    project_id: str,
    location: str,
    processor_id: str,
    processor_version: str,
):
    input_path = os.path.join(from_dir, relative_path)
    output_path = os.path.join(to_dir, os.path.splitext(relative_path)[0] + ".json")

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Check if the output file already exists
    if os.path.exists(output_path):
        print(f"Skipping {relative_path} as output file already exists.")
        return 0, 1  # files_processed, files_skipped

    start_time = time.time()
    try:
        document = process_document(
            project_id,
            location,
            processor_id,
            processor_version,
            input_path,
            "application/pdf",
        )
        end_time = time.time()
        print(
            f"Processed {relative_path}. Time elapsed: {end_time - start_time:.2f} seconds"
        )

        with open(output_path, "w") as json_file:
            json.dump(document.to_dict(), json_file, indent=4)

        return 1, 0  # files_processed, files_skipped

    except Exception as e:
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


def process_document(
    project_id: str,
    location: str,
    processor_id: str,
    processor_version: str,
    file_path: str,
    mime_type: str,
    process_options: Optional[documentai.ProcessOptions] = None,
) -> documentai.Document:
    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(
            api_endpoint=f"{location}-documentai.googleapis.com"
        )
    )

    name = client.processor_version_path(
        project_id, location, processor_id, processor_version
    )

    with open(file_path, "rb") as image:
        image_content = image.read()

    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(content=image_content, mime_type=mime_type),
        process_options=process_options,
    )

    result = client.process_document(request=request)
    return result.document


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
