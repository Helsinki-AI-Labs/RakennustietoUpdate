import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Callable
from datetime import datetime, timezone

from helpers import check_args_and_env_vars, update_state  # Import update_state
from storage import upload_file_to_bucket, download_file
from google.cloud import storage


def ignore_lataaja(text: str) -> bool:
    """
    Rule to ignore paragraphs starting with 'Lataaja:'.

    Args:
        text (str): The text of the paragraph.

    Returns:
        bool: True if the paragraph should be ignored, False otherwise.
    """
    return text.startswith("Lataaja:")


def ignore_header_footer(text_type: str, text: str) -> bool:
    """
    Rule to ignore blocks of type 'header' or 'footer'.

    Args:
        text_type (str): The type of the text block.
        text (str): The text of the block.

    Returns:
        bool: True if the block should be ignored, False otherwise.
    """
    return text_type in {"header", "footer"}


PARAGRAPH_RULES: List[Callable[[str], bool]] = [
    ignore_lataaja,
]

BLOCK_RULES: List[Callable[[str, str], bool]] = [
    ignore_header_footer,
]


def process_blocks(
    blocks: List[Dict[str, Any]],
    sections: List[Dict[str, Any]],
    previous_type: List[str],
    active_heading_levels: List[int],
) -> None:
    for block in blocks:
        text_block = block.get("textBlock", {})
        text_type = text_block.get("type", "").lower()
        text = text_block.get("text", "").strip()

        # Apply block-type rules
        should_ignore_block = any(rule(text_type, text) for rule in BLOCK_RULES)
        if should_ignore_block:
            continue

        if text_type.startswith("heading"):
            heading_level = extract_heading_level(text_type)
            if heading_level in active_heading_levels:
                if sections and sections[-1]["title"]:
                    sections.append({"title": text, "content": []})
                else:
                    sections.append({"title": text, "content": []})
                previous_type.append(text_type)
            else:
                handle_paragraph(text, sections, previous_type)
        elif text_type == "paragraph":
            # Apply rules to the paragraph
            should_ignore = any(rule(text) for rule in PARAGRAPH_RULES)
            if not should_ignore:
                if not sections:
                    sections.append({"title": "", "content": [text]})
                else:
                    sections[-1]["content"].append(text)
            previous_type.append(text_type)
        else:
            if not sections:
                sections.append({"title": "", "content": [text]})
            else:
                sections[-1]["content"].append(text)
            previous_type.append(text_type)

        # Recursively process nested blocks
        nested_blocks = text_block.get("blocks", [])
        if nested_blocks:
            process_blocks(
                nested_blocks, sections, previous_type, active_heading_levels
            )


def extract_heading_level(text_type: str) -> int:
    """
    Extracts the heading level from the text_type string.

    Args:
        text_type (str): The type of the text block.

    Returns:
        int: The heading level (e.g., 1 for heading-1).
    """
    try:
        return int(text_type.split("heading-")[1])
    except (IndexError, ValueError):
        return 1  # Default to level 1 if extraction fails


def handle_paragraph(
    text: str, sections: List[Dict[str, Any]], previous_type: List[str]
) -> None:
    """
    Handles adding a paragraph to the sections.

    Args:
        text (str): The paragraph text.
        sections (List[Dict[str, Any]]): The list of sections.
        previous_type (List[str]): The list of previous block types.
    """
    should_ignore = any(rule(text) for rule in PARAGRAPH_RULES)
    if not should_ignore:
        if not sections:
            sections.append({"title": "", "content": [text]})
        else:
            sections[-1]["content"].append(text)
    previous_type.append("paragraph")


def determine_active_heading_levels(
    blocks: List[Dict[str, Any]], page_count: int
) -> List[int]:
    """
    Determines which heading levels to use for splitting sections based on the number of pages.

    Args:
        blocks (List[Dict[str, Any]]): The list of blocks in the document.
        page_count (int): The number of pages in the document.

    Returns:
        List[int]: The active heading levels to use for splitting.
    """
    max_heading_level = 6  # Assuming heading levels 1 through 6
    for level in range(1, max_heading_level + 1):
        active_levels = list(range(1, level + 1))
        sections = []
        previous_type = []
        process_blocks(blocks, sections, previous_type, active_levels)
        if len(sections) >= page_count:
            return active_levels
    return list(range(1, max_heading_level + 1))


def get_max_page_end(blocks: List[Dict[str, Any]]) -> int:
    """
    Recursively finds the maximum pageEnd value in all blocks.

    Args:
        blocks (List[Dict[str, Any]]): The list of blocks.

    Returns:
        int: The maximum pageEnd value.
    """
    max_page = 1
    for block in blocks:
        page_span = block.get("pageSpan", {})
        page_end = page_span.get("pageEnd", 1)
        if isinstance(page_end, int) and page_end > max_page:
            max_page = page_end

        # Check nested blocks
        text_block = block.get("textBlock", {})
        nested_blocks = text_block.get("blocks", [])
        if nested_blocks:
            nested_max = get_max_page_end(nested_blocks)
            if nested_max > max_page:
                max_page = nested_max
    return max_page


def convert_json_to_json_array(
    input_file_gcs: str,
    output_file_json_gcs: str,
    output_file_txt_gcs: str,
    bucket_name: str,
) -> None:
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_input:
        download_file(bucket_name, input_file_gcs, tmp_input.name)
        tmp_input.flush()
        with open(tmp_input.name, "r", encoding="utf-8") as f:
            data = json.load(f)

    document_layout = data.get("documentLayout", {})
    blocks = document_layout.get("blocks", [])
    # Calculate page_count as the maximum pageEnd value across all blocks
    page_count = get_max_page_end(blocks)

    active_heading_levels = determine_active_heading_levels(blocks, page_count)

    sections: List[Dict[str, Any]] = []
    previous_type: List[str] = []
    process_blocks(blocks, sections, previous_type, active_heading_levels)

    # Remove all sections that have no contents
    cleaned_sections = [
        section for section in sections if section["title"] or section["content"]
    ]

    # Remove all sections where title + all contents combined length is below 30 characters
    filtered_sections = [
        section
        for section in cleaned_sections
        if len(section["title"] + "".join(section["content"])) >= 30
    ]

    # Write JSON array to a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_json_output:
        json.dump(filtered_sections, tmp_json_output, indent=4)
        tmp_json_output.flush()
        upload_file_to_bucket(bucket_name, tmp_json_output.name, output_file_json_gcs)
        os.unlink(tmp_json_output.name)

    # Prepare text content
    lines: List[str] = []
    for section in filtered_sections:
        if section["title"]:
            lines.append(f"{section['title']}\n")
        for paragraph in section["content"]:
            lines.append(f"{paragraph}\n")
        lines.append("\n\n")  # Separator between sections

    final_text = "".join(lines).strip()

    # Write TXT content to a temporary file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_txt_output:
        tmp_txt_output.write(final_text)
        tmp_txt_output.flush()
        upload_file_to_bucket(bucket_name, tmp_txt_output.name, output_file_txt_gcs)
        os.unlink(tmp_txt_output.name)

    # Update state with sectionsCreatedAt timestamp
    current_time = datetime.now(timezone.utc).isoformat()
    file_name = Path(input_file_gcs).stem
    update_state(file_name, {"sectionsCreatedAt": current_time})


def list_json_files(bucket_name: str, prefix: str) -> List[str]:
    """List all JSON files in the specified GCS bucket and prefix."""
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
    json_files = [blob.name for blob in blobs if blob.name.lower().endswith(".json")]
    return json_files


def process_all_files(
    bucket_name: str, input_dir: str, output_dir_json: str, output_dir_txt: str
) -> None:
    json_files = list_json_files(bucket_name, input_dir)
    if not json_files:
        print(f"No JSON files found in gs://{bucket_name}/{input_dir}")
        return

    for input_file_gcs in json_files:
        file_stem = Path(input_file_gcs).stem
        output_file_json_gcs = f"{output_dir_json}/{file_stem}.json"
        output_file_txt_gcs = f"{output_dir_txt}/{file_stem}.txt"

        convert_json_to_json_array(
            input_file_gcs, output_file_json_gcs, output_file_txt_gcs, bucket_name
        )
        print(
            f"Converted gs://{bucket_name}/{input_file_gcs} to gs://{bucket_name}/{output_file_json_gcs} and gs://{bucket_name}/{output_file_txt_gcs}"
        )


def main() -> None:
    """Main function to process JSON files from GCS bucket and convert them to sections."""

    config = check_args_and_env_vars(
        required_env_vars=[
            "BUCKET_NAME",
            "CHUNKS_DIR",
            "SECTIONS_JSON_DIR",
            "SECTIONS_TXT_DIR",
        ]
    )

    BUCKET_NAME = config["BUCKET_NAME"]
    INPUT_DIR = config["CHUNKS_DIR"]
    OUTPUT_DIR_JSON = config["SECTIONS_JSON_DIR"]
    OUTPUT_DIR_TXT = config["SECTIONS_TXT_DIR"]

    process_all_files(BUCKET_NAME, INPUT_DIR, OUTPUT_DIR_JSON, OUTPUT_DIR_TXT)


if __name__ == "__main__":
    main()
