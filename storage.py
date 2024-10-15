import os
from google.cloud import storage
from urllib.parse import urlparse
from typing import List, Tuple


def upload_file_to_bucket(
    bucket_name: str,
    destination_blob_name: str,
    source_file_path: str | None = None,
    file_contents: str | None = None,
) -> None:
    """
    Upload a single file or file contents to GCP Storage bucket.

    Args:
        bucket_name (str): The name of the GCP Storage bucket.
        destination_blob_name (str): The name of the blob in the bucket.
        source_file_path (str | None): The local path of the file to upload. Optional if file_contents is provided.
        file_contents (str | None): The contents of the file to upload. Optional if source_file_path is provided.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    if source_file_path:
        blob.upload_from_filename(source_file_path)
        print(f"Uploaded {source_file_path} to {bucket_name}/{destination_blob_name}")
    elif file_contents is not None:
        blob.upload_from_string(file_contents)
        print(f"Uploaded file contents to {bucket_name}/{destination_blob_name}")
    else:
        raise ValueError("Either source_file_path or file_contents must be provided")


def download_file(
    bucket_name: str, source_blob_name: str, destination_file_path: str | None = None
) -> str | None:
    """Download a single file from GCS bucket to local path or return its contents."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    if destination_file_path:
        blob.download_to_filename(destination_file_path)
        print(f"Downloaded {source_blob_name} to {destination_file_path}")
        return None
    else:
        contents = blob.download_as_text()
        print(f"Retrieved contents of {source_blob_name}")
        return contents


def parse_gcs_uri(uri: str) -> Tuple[str, str]:
    """Parse a GCS URI into bucket and prefix.

    Args:
        uri (str): The GCS URI (e.g., gs://bucket_name/path/to/dir).

    Returns:
        Tuple[str, str]: A tuple containing the bucket name and the prefix.
    """
    parsed = urlparse(uri)
    bucket_name = parsed.netloc
    prefix = parsed.path.lstrip("/")
    return bucket_name, prefix


def copy_batch_to_dir(batch_output_uri: str, chunks_dir: str) -> None:
    """Recursively move all JSON files from the batch output directory to the dchunks directory.

    Args:
        batch_output_uri (str): The GCS URI of the batch output directory.
        dchunks_dir (str): The GCS URI of the destination dchunks directory.
    """
    storage_client = storage.Client()

    source_bucket_name, source_prefix = parse_gcs_uri(batch_output_uri)
    dest_bucket_name, dest_prefix = parse_gcs_uri(chunks_dir)

    if source_bucket_name != dest_bucket_name:
        raise ValueError("Source and destination buckets must be the same.")

    bucket = storage_client.bucket(source_bucket_name)

    blobs = bucket.list_blobs(prefix=source_prefix)

    for blob in blobs:
        if blob.name.endswith(".json"):
            filename = os.path.basename(blob.name)  # Extract the filename
            # Remove the '-0' before the .json extension
            if filename.endswith("-0.json"):
                filename = filename.replace("-0.json", ".json")
            destination_blob_name = f"{dest_prefix}/{filename}"  # Set destination path

            # Copy the blob to the destination
            bucket.copy_blob(blob, bucket, destination_blob_name)

            print(f"Copied {blob.name} to {destination_blob_name}")


def list_files_in_dir(bucket_name: str, prefix: str) -> list[str]:
    """List all files in a given GCS bucket directory.

    Args:
        bucket_name (str): The name of the GCS bucket.
        prefix (str): The prefix (directory) to list files from.

    Returns:
        list[str]: A list of file names in the specified directory.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    file_list = [blob.name for blob in blobs if not blob.name.endswith("/")]

    print(f"Files in {bucket_name}/{prefix}:")
    for file in file_list:
        print(file)

    return file_list


def get_local_file(
    directory: str | None = None,
    filename: str | None = None,
    path: str | None = None,
) -> str:
    """
    Retrieve the contents of a local file given a directory and filename or a full path.

    Args:
        directory (str, optional): The directory containing the file.
        filename (str, optional): The name of the file.
        path (str, optional): The full path to the file.

    Returns:
        str: The contents of the file.

    Raises:
        ValueError: If neither path nor both directory and filename are provided.
        FileNotFoundError: If the specified file does not exist.
    """
    if path:
        file_path = path
    elif directory and filename:
        file_path = os.path.join(directory, filename)
    else:
        raise ValueError("Either path or both directory and filename must be provided.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, "r", encoding="utf-8") as file:
        contents = file.read()
        print(f"Retrieved contents of {file_path}")
        return contents


def save_local_file(
    content: str,
    directory: str | None = None,
    filename: str | None = None,
    path: str | None = None,
) -> None:
    """
    Save content to a local file given a directory and filename or a full path.

    Args:
        content (str): The content to save.
        directory (str, optional): The directory to save the file in.
        filename (str, optional): The name of the file.
        path (str, optional): The full path to save the file.

    Raises:
        ValueError: If neither path nor both directory and filename are provided.
        OSError: If the directory does not exist and cannot be created.
    """
    if path:
        file_path = path
    elif directory and filename:
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, filename)
    else:
        raise ValueError("Either path or both directory and filename must be provided.")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
        print(f"Saved content to {file_path}")


import json
import os
from datetime import datetime, timezone
from typing import Any, Dict


def append_completion_to_file(
    file_path: str,
    section_id: str,
    completion: str,
) -> None:
    """
    Appends a completion entry to a JSON file. Creates the file if it doesn't exist.

    Args:
        file_path (str): The path to the JSON file.
        section_id (str): The ID of the section.
        completion (str): The completion text.

    Raises:
        OSError: If the file cannot be written.
    """
    entry: Dict[str, Any] = {
        "sectionId": section_id,
        "completion": completion,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data: List[Dict[str, Any]] = json.load(file)
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data.append(entry)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        print(f"Appended completion to {file_path}")
