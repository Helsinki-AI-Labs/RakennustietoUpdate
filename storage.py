import os
from google.cloud import storage
from urllib.parse import urlparse
from typing import Tuple


def upload_file_to_bucket(
    bucket_name: str, source_file_path: str, destination_blob_name: str
) -> None:
    """Upload a single file to GCP Storage bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_path)
    print(f"Uploaded {source_file_path} to {bucket_name}/{destination_blob_name}")


def download_file(
    bucket_name: str, source_blob_name: str, destination_file_path: str
) -> None:
    """Download a single file from GCS bucket to local path."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_path)
    print(f"Downloaded {source_blob_name} to {destination_file_path}")


def copy_batch_to_dir(batch_output_uri: str, chunks_dir: str) -> None:
    """Recursively move all JSON files from the batch output directory to the dchunks directory.

    Args:
        batch_output_uri (str): The GCS URI of the batch output directory.
        dchunks_dir (str): The GCS URI of the destination dchunks directory.
    """
    storage_client = storage.Client()

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
