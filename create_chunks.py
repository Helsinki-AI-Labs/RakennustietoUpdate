from datetime import datetime, timezone
import re
from typing import List, Optional

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import InternalServerError, RetryError
from google.cloud import storage, documentai_v1beta3 as documentai
from helpers import check_args_and_env_vars
from google.cloud.documentai_toolbox import gcs_utilities
from dataclasses import dataclass

BATCH_SIZE: int = 3


@dataclass
class Config:
    BUCKET_NAME: str
    LOCATION: str
    PROCESSOR_FULL_NAME: str
    CHUNKS_DIR: str
    PDF_DIR: str


def get_pdf_files_from_bucket(bucket_name: str, source_dir: str) -> List[str]:
    """Retrieve all PDF file names from the specified GCS bucket and source directory."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=source_dir)
    pdf_files = [blob.name for blob in blobs if blob.name.lower().endswith(".pdf")]
    return pdf_files


def batch_process_documents(
    processor_full_name: str,
    location: str,
    gcs_output_uri: str,
    gcs_input_uris: Optional[List[str]] = None,
    timeout: int = 400,
    input_mime_type: str = "application/pdf",
) -> None:
    """Process specific documents using Document AI and save the results to GCS."""
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    if gcs_input_uris:
        # Specify specific GCS URIs to process individual documents
        gcs_documents = [
            documentai.GcsDocument(gcs_uri=uri, mime_type=input_mime_type)
            for uri in gcs_input_uris
        ]
        gcs_document_list = documentai.GcsDocuments(documents=gcs_documents)
        input_config = documentai.BatchDocumentsInputConfig(
            gcs_documents=gcs_document_list
        )
    else:
        raise ValueError("No input URIs provided for batch processing.")

    gcs_output_config = documentai.DocumentOutputConfig.GcsOutputConfig(
        gcs_uri=gcs_output_uri
    )
    output_config = documentai.DocumentOutputConfig(gcs_output_config=gcs_output_config)

    request = documentai.BatchProcessRequest(
        name=processor_full_name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    try:
        operation = client.batch_process_documents(request=request)
        print(f"Waiting for operation {operation.operation.name} to complete...")
        operation.result(timeout=timeout)
    except (RetryError, InternalServerError) as e:
        print(e.message)
        return

    metadata = documentai.BatchProcessMetadata(operation.metadata)

    if metadata.state != documentai.BatchProcessMetadata.State.SUCCEEDED:
        raise ValueError(f"Batch Process Failed: {metadata.state_message}")

    print(f"Batch Process Succeeded: {metadata.state_message}")


def main() -> None:
    """Main function to process PDF files from GCS bucket using Document AI in batches."""
    config: Config = check_args_and_env_vars(
        required_env_vars=[
            "BUCKET_NAME",
            "LOCATION",
            "PROCESSOR_FULL_NAME",
            "CHUNKS_DIR",
            "PDF_DIR",
        ]
    )

    bucket_name = config["BUCKET_NAME"]
    location = config["LOCATION"]
    processor_full_name = config["PROCESSOR_FULL_NAME"]
    output_dir = config["CHUNKS_DIR"]
    source_dir = config["PDF_DIR"]

    pdf_files = get_pdf_files_from_bucket(bucket_name, source_dir)

    print(f"Total PDF files: {len(pdf_files)}")

    if not pdf_files:
        print("No PDF files found in the bucket to process.")
        return

    batches = gcs_utilities.create_batches(
        gcs_bucket_name=bucket_name, gcs_prefix=source_dir, batch_size=BATCH_SIZE
    )

    print(f"Total batches: {len(batches)}")

    for batch in batches:
        print(f"{len(batch.gcs_documents.documents)} files in batch.")
        document_uris = [doc.gcs_uri for doc in batch.gcs_documents.documents]
        print(document_uris)

        # Define the output URI for this batch
        batch_output_uri = f"gs://{bucket_name}/{output_dir.rstrip('/')}/batch_{datetime.now(timezone.utc).isoformat()}"

        print(f"Batch Output URI: {batch_output_uri}")

        # Process the batch with specific document URIs
        batch_process_documents(
            processor_full_name=processor_full_name,
            location=location,
            gcs_output_uri=batch_output_uri,
            gcs_input_uris=document_uris,
            timeout=400,
            input_mime_type="application/pdf",
        )


if __name__ == "__main__":
    main()
