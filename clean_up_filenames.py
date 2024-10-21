import os


def clean_filenames(directory: str) -> None:
    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        # Check if it is a file (skip directories)
        if os.path.isfile(os.path.join(directory, filename)):
            # Remove dashes and underscores from the filename
            cleaned_name = filename.replace("-", "").replace("_", "")

            # Get the full old and new file paths
            old_file = os.path.join(directory, filename)
            new_file = os.path.join(directory, cleaned_name)

            # Rename the file
            os.rename(old_file, new_file)
            print(f"Renamed: {old_file} -> {new_file}")


# Provide the directory path you want to clean up
directory_path = "./data_top100"
clean_filenames(directory_path)
