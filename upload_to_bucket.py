import os
import glob
from typing import Generator, Dict, Any
from helpers import check_args_and_env_vars, update_state
from datetime import datetime, timezone
from storage import upload_file_to_bucket
from dotenv import load_dotenv

load_dotenv()


def get_pdf_files(directory: str) -> Generator[str, None, None]:
    """Retrieve all PDF files from the specified directory using a generator."""
    pattern = os.path.join(directory, "*.pdf")
    yield from glob.iglob(pattern)


def main() -> None:
    """Main function to upload all PDF files in the specified PDF_DIR to GCP Storage bucket."""
    config = check_args_and_env_vars(
        required_env_vars=["BUCKET_NAME", "PDF_DIR", "LOCAL_PDF_DIR"]
    )

    bucket_name = config["BUCKET_NAME"]
    pdf_dir = config["PDF_DIR"]
    local_pdf_dir = config["LOCAL_PDF_DIR"]

    pdf_files = get_pdf_files(local_pdf_dir)

    has_files = False
    for file_path in pdf_files:
        has_files = True
        file_name = os.path.basename(file_path)
        upload_path = os.path.join(pdf_dir, file_name)
        upload_file_to_bucket(bucket_name, file_path, upload_path)
        update_state(file_name, {"uploadedAt": datetime.now(timezone.utc).isoformat()})

    if not has_files:
        print("No PDF files found to upload.")


if __name__ == "__main__":
    main()
