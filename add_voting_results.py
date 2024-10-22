import json


def add_voting_results():

    # Load the data from 'grouped_responses.json'
    with open("grouped_responses.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Iterate over each file and its content
    for filename, file_data in data.items():
        for key, item in file_data.items():
            # Check if 'responses' key exists in the item
            if "responses" in item:
                non_empty_responses_count = item.get("non_empty_responses_count", 0)
                if non_empty_responses_count >= 2:
                    responses = item["responses"]
                    # Filter out empty responses ("Ei päivitettävää.")
                    non_empty_responses = [
                        resp for resp in responses if resp != "Ei päivitettävää."
                    ]
                    # If there are non-empty responses, find the longest one
                    if non_empty_responses:
                        longest_response = max(non_empty_responses, key=len)
                        item["voting_result"] = longest_response
                    else:
                        # If somehow there are no non-empty responses, set voting_result to "-"
                        item["voting_result"] = "-"
                else:
                    # If non-empty responses count is less than 2, set voting_result to "-"
                    item["voting_result"] = "-"
            else:
                # If 'responses' key does not exist, you might want to handle it or skip
                pass

    # Save the updated data to 'voting_results.json'
    with open("voting_results.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    add_voting_results()
