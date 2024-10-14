from google.cloud import storage


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
