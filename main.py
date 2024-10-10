import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from prompt import create_prompt
from typing import List, TypedDict


class Section(TypedDict):
    title: str
    content: List[str]


class Completion(TypedDict):
    title: str
    content: List[str]
    input: str
    output: str


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


def run_prompt(
    new_law_part: str, combined_content: str, output_file: str, identifier: str
) -> None:
    prompt = create_prompt(new_law_part, combined_content)

    stream = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        stream=True,
    )

    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"\n\nAnalysis for {identifier}:\n")
        f.write(f"**Input Content:**\n{combined_content}\n\n")
        f.write(f"**Model Output:**\n")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="")
                f.write(content)
        f.write("\n\n####\n\n")


def combine_title_content(section: dict) -> str:
    title = section.get("title", "").strip()
    content = section.get("content", [])
    combined_content = f"{title}\n\n\n" + "\n".join(content)
    return combined_content


def main() -> None:
    with open("new-construction-law.txt", "r", encoding="utf-8") as file:
        new_construction_law: str = file.read()

    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)

    folder_path = "sections_json"

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        input_file_path = os.path.join(folder_path, filename)
        with open(input_file_path, "r", encoding="utf-8") as file:
            try:
                sections = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}")
                continue

        output_file = os.path.join(
            output_dir, f"analysis_{os.path.splitext(filename)[0]}.txt"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Analysis for {filename}\n")
            f.write("====================================\n")

        for index, section in enumerate(sections, start=1):
            combined_content = combine_title_content(section)
            identifier = f"{filename} - Section {index}"
            print(f"\n\nProcessing {identifier} with new-construction-law.txt:")
            run_prompt(new_construction_law, combined_content, output_file, identifier)

    print(
        "\nAnalysis complete. Output files have been saved in the 'output' directory."
    )


if __name__ == "__main__":
    main()
