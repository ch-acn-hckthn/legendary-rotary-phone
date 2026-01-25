import os
import re
import urllib.parse
import argparse
import sys

FILETYPES = (".png", ".jpg")


def extract_link_targets(text):
    pattern1 = r"(?<=]\().*?(?=\))"  # ![](...)
    pattern2 = r"(?<=\[\[).*?(?=\]\])"  # ![[]]

    matches1 = re.findall(pattern1, text)
    matches2 = re.findall(pattern2, text)

    return matches1 + matches2


def find_files(directory, filetypes):
    image_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(filetypes):
                image_files.append(os.path.join(root, file))
    return image_files


def find_linked_attachments(base_dir, filetypes):
    targets = set()

    for dirpath, dirnames, filenames in os.walk(base_dir):
        for filename in filenames:
            # Check if the file ends with .md
            if filename.endswith(".md"):
                file_path = os.path.join(dirpath, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        md_content = file.read()
                        current_targets = extract_link_targets(md_content)
                        # fix url encoding
                        current_targets = [
                            urllib.parse.unquote(t, encoding="utf-8")
                            for t in current_targets
                        ]
                        # only include files with valid ending
                        current_targets = [
                            t
                            for t in current_targets
                            if any([t.endswith(suffix) for suffix in filetypes])
                        ]
                        # extract filename if link is a path
                        current_targets = [t.split("/")[-1] for t in current_targets]
                        targets.update(current_targets)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return targets


def main():
    parser = argparse.ArgumentParser(
        description="Finds orphan attachments in an Obsidian vault."
    )
    parser.add_argument("--vault", help="Location of the Obsidian vault")
    parser.add_argument("--destructive", action="store_true", help="Delete orphan attachments")

    args = parser.parse_args()
    print(args)

    if args.vault is None:
        print("Please provide a valid Obsidian vault\n")
        parser.print_help()
        sys.exit(1)

    # current_directory = os.getcwd()  # Get the current working directory
    vault = args.vault
    vault = vault.strip('"').strip("'")
    
    vault = os.path.normpath(vault)

    obsidian_dir = os.path.join(vault, ".obsidian")
    

    # check if there is a vault
    if not (os.path.exists(obsidian_dir) and os.path.isdir(obsidian_dir)):
        print("Obsidian directory does not exist.")
        sys.exit(-1)

    link_targets = find_linked_attachments(vault, FILETYPES)

    image_paths = find_files(vault, FILETYPES)

    to_delete = []
    for image_path in image_paths:
        
        sep = '/'  # default to unix style
        if os.name == "nt":
            sep = "\\"  # windows style
        image_filename = image_path.split(sep)[-1]
        
        if image_filename not in link_targets and "attachments" in image_path:
            print(image_path)
            to_delete.append(image_path)

    n_to_delete = len(to_delete)
    print(f"Found {n_to_delete} orphan attachments.")

    if args.destructive and n_to_delete > 0:
        f"Deleting {len(to_delete)} orphan attachments..."
        # get user confirmation
        confirm = input("Are you sure you want to delete these files? (y/n): ")
        if confirm.lower() == "y":
            for file_path in to_delete:
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        else:
            print("Deletion cancelled by user.")

if __name__ == "__main__":
    main()
