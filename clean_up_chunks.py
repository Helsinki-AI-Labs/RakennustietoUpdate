import os
import json
from typing import List, Dict
from helpers import check_args_and_env_vars
from filters import filter_chunks, text_length_filter, space_count_filter
from combiners import (
    combine_chunks,
    combine_short_chunks,
)


def chunks_to_txt(chunks: List[Dict], output_txt_path: str) -> None:
    combined_text_list = []
    for chunk in chunks:
        text = chunk.get("text", "")
        combined_text_list.append(text)
        if chunk.get("type") == "Title":
            combined_text_list.append("\n\n###\n\n")
    combined_text = "\n".join(combined_text_list)
    with open(output_txt_path, "w", encoding="utf-8") as txt_file:
        txt_file.write(combined_text)
    print(f"Combined text written to {output_txt_path}")


def clean_up_chunks(from_dir: str, to_dir: str):
    os.makedirs(to_dir, exist_ok=True)

    filters = [
        text_length_filter,
        space_count_filter,
    ]

    combine_functions = [
        lambda chunks: combine_short_chunks(chunks, word_limit=4)  # Example word limit
    ]

    for filename in os.listdir(from_dir):
        if filename.endswith(".json"):
            input_path = os.path.join(from_dir, filename)
            output_json_path = os.path.join(to_dir, filename)
            output_txt_path = os.path.splitext(output_json_path)[0] + ".txt"

            with open(input_path, "r", encoding="utf-8") as infile:
                chunks = json.load(infile)

            cleaned_chunks = filter_chunks(chunks, filters)
            combined_chunks = combine_chunks(cleaned_chunks, combine_functions)

            with open(output_json_path, "w", encoding="utf-8") as outfile:
                json.dump(combined_chunks, outfile, ensure_ascii=False, indent=4)

            print(f"Processed {filename}: {len(combined_chunks)} chunks kept.")

            chunks_to_txt(combined_chunks, output_txt_path)


if __name__ == "__main__":
    from_dir = "chunks"
    to_dir = "cleaned_chunks"
    config = check_args_and_env_vars(
        required_args=[],
        required_env_vars=[],
        optional_args=["--from_dir", "--to_dir"],
    )

    from_dir: str = config.get("FROM_DIR") or from_dir
    to_dir: str = config.get("TO_DIR") or to_dir

    clean_up_chunks(from_dir, to_dir)
