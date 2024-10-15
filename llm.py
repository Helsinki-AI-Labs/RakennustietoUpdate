import json
import os
import time
from typing import List, TypedDict, Optional, Dict
from openai import OpenAI
from helpers import combine_title_content
from prompt import create_prompt
from os.path import basename

CLIENT = OpenAI()


class Section(TypedDict):
    title: str
    content: List[str]


class Completion(TypedDict):
    title: str
    content: List[str]
    input: str
    output: str


class Message(TypedDict):
    role: str
    content: str
    refusal: Optional[str]


class Choice(TypedDict):
    index: int
    message: Message
    logprobs: Optional[Dict]
    finish_reason: str


class Body(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Dict
    system_fingerprint: str


class Response(TypedDict):
    status_code: int
    request_id: str
    body: Body


class BatchRequest(TypedDict):
    id: str
    custom_id: str
    response: Response
    error: Optional[Dict]


def prepare_batch_input(sections: List[Dict], law_text: str) -> str:
    """
    Prepares a JSONL file for Batch API with all section prompts.

    Args:
        sections (List[Dict]): List of sections with custom_id and content.
        law_text (str): The content of the law text.

    Returns:
        str: The full path to the prepared batch input file.
    """
    batch_inputs_dir = "batch_inputs"
    os.makedirs(batch_inputs_dir, exist_ok=True)
    batch_input_filename = f"batch_input_{int(time.time())}.jsonl"
    full_path = os.path.join(batch_inputs_dir, batch_input_filename)

    with open(full_path, "w", encoding="utf-8") as f:
        for item in sections:
            custom_id = item["custom_id"]
            section = item["section"]
            combined_content = combine_title_content(section)
            prompt = create_prompt(law_text, combined_content)
            request: BatchRequest = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-2024-08-06",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                },
            }
            f.write(json.dumps(request) + "\n")
    return full_path


def upload_batch_file(batch_input_path: str) -> str:
    """
    Uploads the batch input file to OpenAI.

    Args:
        batch_input_path (str): Path to the batch input JSONL file.

    Returns:
        str: The uploaded file's ID.
    """
    with open(batch_input_path, "rb") as file:
        response = CLIENT.files.create(
            file=file,
            purpose="batch",
        )
    return response.id


def create_batch_job(input_file_id: str, endpoint: str = "/v1/chat/completions") -> str:
    """
    Creates a batch job with the uploaded input file.

    Args:
        input_file_id (str): The ID of the uploaded batch input file.
        endpoint (str): The API endpoint to use for the batch.

    Returns:
        str: The created batch job's ID.
    """
    batch = CLIENT.batches.create(
        input_file_id=input_file_id,
        endpoint=endpoint,
        completion_window="24h",
        metadata={
            "description": "Automated batch processing for law sections analysis"
        },
    )
    return batch.id


def poll_batch_status(batch_id: str) -> Dict:
    """
    Polls the batch job status until completion.

    Args:
        batch_id (str): The ID of the batch job.

    Returns:
        Dict: The final batch object.
    """
    while True:
        batch = CLIENT.batches.retrieve(batch_id)
        status = batch.status
        print(f"Batch Status: {status}")
        if status in ["completed", "failed", "expired", "cancelled"]:
            break
        time.sleep(10)  # Wait for 10 seconds before polling again
    return batch


def retrieve_batch_results(output_file_id: str) -> List[Dict]:
    """
    Retrieves and parses the batch results from the output file.

    Args:
        output_file_id (str): The ID of the output file.

    Returns:
        List[Dict]: List of response objects.
    """
    file_content = CLIENT.files.content(output_file_id)
    results: List[Dict] = []
    for line in file_content.text.strip().split("\n"):
        result = json.loads(line)
        results.append(result)
    return results


def process_batch_results(
    results: List[Dict], filenames: List[str], sections: Dict[str, Section]
) -> List[str]:
    """
    Processes the batch results and compiles the analysis content.

    Args:
        results (List[Dict]): List of response objects from the batch.
        filenames (List[str]): List of source filenames for reference.
        sections (Dict[str, Section]): Dictionary mapping custom_ids to sections.

    Returns:
        List[str]: List of compiled analysis contents per file.
    """
    analysis_dict: Dict[str, List[str]] = {basename(fn): [] for fn in filenames}

    for result in results:
        custom_id = result.get("custom_id")
        response = result.get("response")
        error = result.get("error")

        if error:
            filename = custom_id.split("-Section-")[0]
            analysis_dict[filename].append(f"\nError in {custom_id}: {error}\n")
            continue

        content = response["body"]["choices"][0]["message"]["content"]
        combined_content = combine_title_content(sections[custom_id])
        analysis_result = (
            "\n\n====================================\n\n"
            f"\nTEXT SECTION:\n{combined_content}\n\nSUGGESTED CHANGES:\n"
            f"{content}"
        )
        filename = custom_id.split("-Section-")[0]
        analysis_dict[filename].append(analysis_result)

    # Compile analysis content per file
    compiled_analyses = []
    for filename, analyses in analysis_dict.items():
        compiled_content = f"Source File: {filename}\n" + "\n".join(analyses)
        compiled_analyses.append(compiled_content)

    return compiled_analyses
