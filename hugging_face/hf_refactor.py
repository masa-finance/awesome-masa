import os
import dotenv
import time
import argparse
import json
import re
from huggingface_hub import HfApi, HfFolder, add_collection_item, create_collection, list_collections, delete_collection, logging as hf_logging
from datasets import load_dataset
from tqdm import tqdm
import sys

# Replace the existing logging configuration with this:
hf_logging.set_verbosity_info()
hf_logging.enable_progress_bar()

dotenv.load_dotenv()
org_name = os.getenv('HF_ORG_NAME')
token = os.getenv('HF_TOKEN')

UPLOAD_RECORD_FILE = os.path.join(os.path.dirname(__file__), 'hf_upload_record.json')

def load_upload_record():
    if os.path.exists(UPLOAD_RECORD_FILE):
        with open(UPLOAD_RECORD_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_upload_record(record):
    with open(UPLOAD_RECORD_FILE, 'w') as f:
        json.dump(record, f, indent=4)

def sanitize_repo_name(name):
    # Remove any characters that are not alphanumeric, '-', or '_'
    name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    
    # Remove leading or trailing '-' or '.'
    name = name.strip('-.')
    
    # Ensure the name doesn't contain '--' or '..'
    name = re.sub(r'--', '-', name)
    name = re.sub(r'\.\.', '.', name)
    
    # Truncate to 96 characters max
    name = name[:96]
    
    return name

def iterate_and_process_folders(datasets_path):
    failed_files = []
    hf_upload_record = load_upload_record()
    try:
        for collection_name in os.listdir(datasets_path):
            collection_path = os.path.join(datasets_path, collection_name)
            if os.path.isdir(collection_path):
                hf_logging.info(f"Processing collection: {collection_name}")
                collection_slug = get_or_create_collection(collection_name)
                for subfolder_name in os.listdir(collection_path):
                    subfolder_path = os.path.join(collection_path, subfolder_name)
                    if os.path.isdir(subfolder_path):
                        hf_logging.info(f"Processing subfolder: {subfolder_name}")
                        for file_name in os.listdir(subfolder_path):
                            file_path = os.path.join(subfolder_path, file_name)
                            if os.path.isfile(file_path):
                                file_mod_time = os.path.getmtime(file_path)
                                if file_path in hf_upload_record and hf_upload_record[file_path] >= file_mod_time:
                                    hf_logging.info(f"Skipping already uploaded file: {file_path}")
                                    continue
                                try:
                                    hf_logging.info(f"Uploading file: {file_path}")
                                    dataset = load_dataset_from_file(file_path)
                                    file_name_without_ext = os.path.splitext(file_name)[0]
                                    sanitized_name = sanitize_repo_name(f"{subfolder_name}_{file_name_without_ext}")
                                    repo_id = f"{org_name}/{sanitized_name}"
                                    dataset.push_to_hub(repo_id=repo_id)
                                    add_collection_item(
                                        collection_slug=collection_slug,
                                        item_id=repo_id,
                                        item_type="dataset",
                                        exists_ok=True
                                    )
                                    hf_logging.info(f"Successfully uploaded {file_name} to {collection_slug}")
                                    hf_upload_record[file_path] = file_mod_time
                                    save_upload_record(hf_upload_record)
                                    time.sleep(5)  # Sleep for 5 seconds to avoid overloading the API
                                except Exception as e:
                                    if "429 Client Error: Too Many Requests" in str(e):
                                        hf_logging.error(f"Rate limit reached. Exiting program.")
                                        print("Rate limit reached. Please try again after 24 hours.")
                                        sys.exit(1)
                                    hf_logging.error(f"Error processing file {file_path}: {e}")
                                    failed_files.append((file_path, e))
    except Exception as e:
        hf_logging.error(f"Error iterating and processing folders: {e}")
    
    # Print summary of failed files
    if failed_files:
        print("\nSummary of failed files:")
        for file_path, error in failed_files:
            print(f"File: {file_path}")
            print(f"Error: {str(error)}\n")
        print(f"Total failed files: {len(failed_files)}")
    else:
        print("All files processed successfully.")

def get_or_create_collection(collection_name):
    try:
        hf_logging.info(f"Checking for existing collection: {collection_name}")
        collections = list_collections(owner=org_name)
        for collection in collections:
            if collection.title == collection_name:
                hf_logging.info(f"Found existing collection: {collection_name}")
                return collection.slug
        
        hf_logging.info(f"Creating new collection: {collection_name}")
        collection = create_collection(
            title=collection_name,
            namespace=org_name,
            description=f"Collection for {collection_name}",
            private=False
        )
        hf_logging.info(f"Created new collection: {collection_name}")
        return collection.slug
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            hf_logging.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        hf_logging.error(f"Error getting or creating collection {collection_name}: {e}")
        raise

def load_dataset_from_file(file_path):
    try:
        hf_logging.info(f"Loading dataset from file: {file_path}")
        if file_path.endswith('.csv'):
            return load_dataset('csv', data_files=file_path)
        elif file_path.endswith('.json'):
            return load_dataset('json', data_files=file_path)
        elif file_path.endswith('.txt'):
            return load_dataset('text', data_files=file_path)
        else:
            raise ValueError(f"Unsupported file extension for file: {file_path}")
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            hf_logging.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        hf_logging.error(f"Error loading dataset from file {file_path}: {e}")
        raise

def delete_collection_by_slug():
    try:
        hf_logging.info(f"Fetching collections for organization: {org_name}")
        collections = list(list_collections(owner=org_name))
        if not collections:
            hf_logging.info("No collections found.")
        else:
            print(f"{len(collections) + 1}. All collections")

        print("Select a collection to delete:")
        for idx, collection in enumerate(collections, start=1):
            print(f"{idx}. {collection.title} (slug: {collection.slug})")
        print(f"{len(collections) + 1}. All collections")

        choice = int(input("Enter the number of the collection to delete: "))
        if choice == len(collections) + 1:
            confirm = input("Are you sure you want to delete all collections? (yes/no): ")
            if confirm.lower() == 'yes':
                for collection in collections:
                    hf_logging.info(f"Deleting collection: {collection.slug}")
                    delete_collection(collection_slug=collection.slug, missing_ok=True)
                    hf_logging.info(f"Successfully deleted collection: {collection.slug}")
            else:
                hf_logging.info("Deletion of all collections cancelled.")
        elif 1 <= choice <= len(collections):
            collection_slug = collections[choice - 1].slug
            confirm = input(f"Are you sure you want to delete the collection {collection_slug}? (yes/no): ")
            if confirm.lower() == 'yes':
                hf_logging.info(f"Deleting collection: {collection_slug}")
                delete_collection(collection_slug=collection_slug, missing_ok=True)
                hf_logging.info(f"Successfully deleted collection: {collection_slug}")
            else:
                hf_logging.info(f"Deletion of collection {collection_slug} cancelled.")
        else:
            hf_logging.error("Invalid choice.")
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            hf_logging.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        hf_logging.error(f"Error deleting collection: {e}")
        raise


def get_all_datasets_in_org(org_name):
    try:
        hf_logging.info(f"Fetching all datasets for organization: {org_name}")
        api = HfApi()
        datasets = api.list_datasets(author=org_name)
        dataset_names = [dataset.id for dataset in datasets]
        hf_logging.info(f"Found {len(dataset_names)} datasets for organization: {org_name}")
        return dataset_names
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            hf_logging.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        hf_logging.error(f"Error fetching datasets for organization {org_name}: {e}")
        raise


def delete_dataset_in_org(org_name):
    try:
        dataset_names = get_all_datasets_in_org(org_name)
        hf_logging.info(f"Deleting {len(dataset_names)} datasets for organization: {org_name}")
        
        confirm = input(f"Are you sure you want to delete all {len(dataset_names)} datasets? (yes/no): ")
        if confirm.lower() == 'yes':
            for dataset_name in tqdm(dataset_names, desc="Deleting datasets"):
                try:
                    api.delete_repo(
                        repo_id=f"{dataset_name}",
                        token=token,
                        repo_type="dataset",
                        missing_ok=True
                    )
                    hf_logging.info(f"Successfully deleted dataset: {dataset_name} from organization: {org_name}")
                    time.sleep(2)  # Sleep for the specified delay to avoid overloading the API
                except Exception as e:
                    if "429 Client Error: Too Many Requests" in str(e):
                        hf_logging.error(f"Rate limit reached. Exiting program.")
                        print("Rate limit reached. Please try again after 24 hours.")
                        sys.exit(1)
                    hf_logging.error(f"Unexpected error deleting dataset {dataset_name}: {e}")
        else:
            hf_logging.info("Deletion of all datasets cancelled.")
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            hf_logging.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        hf_logging.error(f"Error deleting datasets from organization {org_name}: {e}")
        raise



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process or delete collections or datasets on Hugging Face.")
    parser.add_argument("action", choices=["process", "delete_collection", "delete_dataset"], help="Action to perform: 'process' to iterate and process folders, 'delete_collection' to delete a collection, 'delete_dataset' to delete a dataset.")
    args = parser.parse_args()

    if args.action == "process":
        datasets_path = os.path.join(os.path.dirname(__file__), '..', 'datasets')
        hf_logging.info(f"Starting to process datasets in path: {datasets_path}")
        iterate_and_process_folders(datasets_path)
        hf_logging.info("Completed processing all datasets")
    elif args.action == "delete_collection":
        delete_collection_by_slug()
    elif args.action == "delete_dataset":
        delete_dataset_in_org(org_name)