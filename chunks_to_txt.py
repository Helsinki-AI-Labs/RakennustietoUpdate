import json
from pathlib import Path
from typing import Any, Dict, List, Callable


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
    input_file: Path, output_file_json: Path, output_file_txt: Path
) -> None:
    with input_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    document_layout = data.get("documentLayout", {})
    blocks = document_layout.get("blocks", [])
    # Calculate page_count as the maximum pageEnd value across all blocks
    page_count = get_max_page_end(blocks)

    active_heading_levels = determine_active_heading_levels(blocks, page_count)
    print(f"Input file: {input_file}")
    print(f"Page count: {page_count}")
    print(f"Active heading levels: {active_heading_levels}")

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

    # Write JSON array
    with output_file_json.open("w", encoding="utf-8") as f_json:
        json.dump(filtered_sections, f_json, indent=4)

    # Prepare text content
    lines: List[str] = []
    for section in filtered_sections:
        if section["title"]:
            lines.append(f"{section['title']}\n")
        for paragraph in section["content"]:
            lines.append(f"{paragraph}\n")
        lines.append("\n\n")  # Separator between sections

    final_text = "".join(lines).strip()

    # Write TXT file
    with output_file_txt.open("w", encoding="utf-8") as f_txt:
        f_txt.write(final_text)


def process_all_files(
    input_dir: Path, output_dir_json: Path, output_dir_txt: Path
) -> None:
    if not output_dir_json.exists():
        output_dir_json.mkdir(parents=True)
    if not output_dir_txt.exists():
        output_dir_txt.mkdir(parents=True)

    for input_file in input_dir.glob("*.json"):
        output_file_json = output_dir_json / f"{input_file.stem}.json"
        output_file_txt = output_dir_txt / f"{input_file.stem}.txt"
        convert_json_to_json_array(input_file, output_file_json, output_file_txt)
        print(f"Converted {input_file} to {output_file_json} and {output_file_txt}")


if __name__ == "__main__":
    INPUT_DIR = Path("chunks")
    OUTPUT_DIR_JSON = Path("sections_json")
    OUTPUT_DIR_TXT = Path("sections_txt")
    process_all_files(INPUT_DIR, OUTPUT_DIR_JSON, OUTPUT_DIR_TXT)
