import os
import dotenv
import time
import argparse
import json
import re
import logging
import colorlog
from huggingface_hub import HfApi, HfFolder, add_collection_item, create_collection, list_collections, delete_collection, metadata_update
from datasets import load_dataset
from tqdm import tqdm
import sys
from fuzzywuzzy import fuzz, process

# Set up colorlog
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(name)s:%(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

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

def iterate_and_process_folders(datasets_path, subfolder=None, folder=None):
    failed_files = []
    hf_upload_record = load_upload_record()
    try:
        for collection_name in os.listdir(datasets_path):
            collection_path = os.path.join(datasets_path, collection_name)
            if os.path.isdir(collection_path):
                if subfolder and collection_name != subfolder:
                    continue
                process_collection(collection_name, collection_path, folder, hf_upload_record, failed_files)
    except Exception as e:
        logger.error(f"Error iterating and processing folders: {e}")
    
    print_summary_of_failed_files(failed_files)

def process_collection(collection_name, collection_path, folder, hf_upload_record, failed_files):
    logger.info(f"Processing collection: {collection_name}")
    collection_slug = get_or_create_collection(collection_name)
    for subfolder_name in os.listdir(collection_path):
        subfolder_path = os.path.join(collection_path, subfolder_name)
        if os.path.isdir(subfolder_path):
            if folder and subfolder_name != folder:
                continue
            process_subfolder(subfolder_name, subfolder_path, collection_slug, hf_upload_record, failed_files)

def process_subfolder(subfolder_name, subfolder_path, collection_slug, hf_upload_record, failed_files):
    logger.info(f"Processing subfolder: {subfolder_name}")
    for file_name in os.listdir(subfolder_path):
        file_path = os.path.join(subfolder_path, file_name)
        if os.path.isfile(file_path):
            process_file(file_name, file_path, subfolder_name, collection_slug, hf_upload_record, failed_files)

def process_file(file_name, file_path, subfolder_name, collection_slug, hf_upload_record, failed_files):
    file_mod_time = os.path.getmtime(file_path)
    if file_path in hf_upload_record and hf_upload_record[file_path] >= file_mod_time:
        logger.info(f"Skipping already uploaded file: {file_path}")
        return
    try:
        logger.info(f"Uploading file: {file_path}")
        dataset = load_dataset_from_file(file_path)
        file_name_without_ext = os.path.splitext(file_name)[0]
        sanitized_name = sanitize_repo_name(f"{subfolder_name}_{file_name_without_ext}")
        repo_id = f"{org_name}/{sanitized_name}"
        
        if not repo_exists(repo_id):
            upload_dataset(dataset, repo_id, collection_slug, file_path, file_mod_time, hf_upload_record)
    except Exception as e:
        handle_file_processing_error(e, file_path, failed_files)

def repo_exists(repo_id):
    try:
        api.repo_info(repo_id=repo_id)
        logger.info(f"Repository {repo_id} already exists. Skipping upload.")
        return True
    except Exception as e:
        if "404 Client Error" in str(e):
            return False
        else:
            raise e

def upload_dataset(dataset, repo_id, collection_slug, file_path, file_mod_time, hf_upload_record):
    dataset.push_to_hub(repo_id=repo_id)
    add_collection_item(
        collection_slug=collection_slug,
        item_id=repo_id,
        item_type="dataset",
        exists_ok=True
    )
    logger.info(f"Successfully uploaded {file_path} to {collection_slug}")
    hf_upload_record[file_path] = file_mod_time
    save_upload_record(hf_upload_record)
    time.sleep(5)  # Sleep for 5 seconds to avoid overloading the API

def handle_file_processing_error(e, file_path, failed_files):
    if "429 Client Error: Too Many Requests" in str(e):
        logger.error(f"Rate limit reached. Exiting program.")
        print("Rate limit reached. Please try again after 24 hours.")
        sys.exit(1)
    logger.error(f"Error processing file {file_path}: {e}")
    failed_files.append((file_path, e))

def print_summary_of_failed_files(failed_files):
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
        logger.info(f"Checking for existing collection: {collection_name}")
        collections = list_collections(owner=org_name)
        for collection in collections:
            if collection.title == collection_name:
                logger.info(f"Found existing collection: {collection_name}")
                return collection.slug
        
        logger.info(f"Creating new collection: {collection_name}")
        collection = create_collection(
            title=collection_name,
            namespace=org_name,
            description=f"Collection for {collection_name}",
            private=False
        )
        logger.info(f"Created new collection: {collection_name}")
        return collection.slug
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            logger.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        logger.error(f"Error getting or creating collection {collection_name}: {e}")
        raise

def load_dataset_from_file(file_path):
    try:
        logger.info(f"Loading dataset from file: {file_path}")
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
            logger.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        logger.error(f"Error loading dataset from file {file_path}: {e}")
        raise

def delete_collection_by_slug():
    try:
        logger.info(f"Fetching collections for organization: {org_name}")
        collections = list(list_collections(owner=org_name))
        if not collections:
            logger.info("No collections found.")
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
                    logger.info(f"Deleting collection: {collection.slug}")
                    delete_collection(collection_slug=collection.slug, missing_ok=True)
                    logger.info(f"Successfully deleted collection: {collection.slug}")
            else:
                logger.info("Deletion of all collections cancelled.")
        elif 1 <= choice <= len(collections):
            collection_slug = collections[choice - 1].slug
            confirm = input(f"Are you sure you want to delete the collection {collection_slug}? (yes/no): ")
            if confirm.lower() == 'yes':
                logger.info(f"Deleting collection: {collection_slug}")
                delete_collection(collection_slug=collection_slug, missing_ok=True)
                logger.info(f"Successfully deleted collection: {collection_slug}")
            else:
                logger.info(f"Deletion of collection {collection_slug} cancelled.")
        else:
            logger.error("Invalid choice.")
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            logger.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        logger.error(f"Error deleting collection: {e}")
        raise


def get_all_datasets_in_org(org_name):
    try:
        logger.info(f"Fetching all datasets for organization: {org_name}")
        api = HfApi()
        datasets = api.list_datasets(author=org_name)
        dataset_names = [dataset.id for dataset in datasets]
        logger.info(f"Found {len(dataset_names)} datasets for organization: {org_name}")
        return dataset_names
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            logger.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        logger.error(f"Error fetching datasets for organization {org_name}: {e}")
        raise


def delete_datasets_in_org(org_name):
    try:
        dataset_names = get_all_datasets_in_org(org_name)
        logger.info(f"Deleting {len(dataset_names)} datasets for organization: {org_name}")
        
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
                    logger.info(f"Successfully deleted dataset: {dataset_name} from organization: {org_name}")
                    time.sleep(2)  # Sleep for the specified delay to avoid overloading the API
                except Exception as e:
                    if "429 Client Error: Too Many Requests" in str(e):
                        logger.error(f"Rate limit reached. Exiting program.")
                        print("Rate limit reached. Please try again after 24 hours.")
                        sys.exit(1)
                    logger.error(f"Unexpected error deleting dataset {dataset_name}: {e}")
        else:
            logger.info("Deletion of all datasets cancelled.")
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            logger.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        logger.error(f"Error deleting datasets from organization {org_name}: {e}")
        raise


def create_dataset_json(org_name, output_file):
    try:
        logger.info(f"Fetching all datasets for organization: {org_name}")
        datasets = api.list_datasets(author=org_name)
        
        with open(output_file, 'w') as f:
            for dataset in datasets:
                logger.info(f"Processing dataset: {dataset.id}")
                dataset_id = dataset.id
                dataset_info = api.dataset_info(dataset_id)
                
                # Extract the podcast name from the dataset title
                data_source = dataset_info.cardData.get('title', '').split('_')[0]
                
                # Create the URL
                url = f"https://huggingface.co/datasets/{dataset_id}"
                
                # Get the number of downloads and last updated timestamp
                downloads = dataset_info.downloads
                last_modified = dataset_info.lastModified.strftime("%Y-%m-%d %H:%M:%S")  # Convert datetime to string
                
                dataset_info_dict = {
                    "title": dataset_info.cardData.get('pretty_name', ''),
                    "data_source": dataset_info.cardData.get('data_source', ''),
                    "url": url,
                    "downloads": downloads,
                    "last_modified": last_modified
                }
                
                json.dump(dataset_info_dict, f)
                f.write('\n')  # Write each dataset info on a new line
                
                logger.info(f"Processed dataset: {dataset.id}")
                time.sleep(2)
        
        logger.info(f"Finished processing datasets for organization: {org_name}")
    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            logger.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        logger.error(f"Error fetching datasets for organization {org_name}: {e}")
        raise

def update_dataset_cards(org_name):
    try:
        logger.info(f"Updating dataset cards for organization: {org_name}")
        datasets = api.list_datasets(author=org_name)
        
        for dataset in tqdm(datasets, desc="Updating dataset cards"):
            repo_id = dataset.id
            
            # Prepare the new metadata
            new_metadata = {
                "data_source": "",  # Example: set license to Apache-2.0
                "language": ["en"],  # Example: set language to English
                "tags": ["transcript", "podcast"],  # Example: add tags
                # Add more fields as needed
            }
            
            # Update the metadata
            url = metadata_update(
                repo_id=repo_id,
                metadata=new_metadata,
                repo_type="dataset",
                token=token
            )
            
            logger.info(f"Updated metadata for dataset: {repo_id}")
            logger.info(f"Updated metadata URL: {url}")
            time.sleep(1)  # Sleep to avoid rate limiting
        
        logger.info(f"Finished updating metadata for {len(datasets)} datasets")

    except Exception as e:
        if "429 Client Error: Too Many Requests" in str(e):
            logger.error(f"Rate limit reached. Exiting program.")
            print("Rate limit reached. Please try again after 24 hours.")
            sys.exit(1)
        logger.error(f"Error updating dataset metadata for organization {org_name}: {e}")
        raise

def load_original_titles_from_folders(base_path):
    logger.info(f"Loading original titles from folders in {base_path}")
    original_titles = []
    for root, _, files in os.walk(base_path):
        logger.info(f"Processing folder: {root}")
        for file in files:
            if file.endswith('.json') or file.endswith('.txt'):
                original_title = os.path.splitext(file)[0]
                original_titles.append(original_title)
                logger.info(f"Found original title: {original_title}")
    logger.info(f"Found {len(original_titles)} original titles in total")
    return original_titles

def get_truncated_titles(org_name):
    logger.info(f"Getting truncated titles for organization {org_name}")
    datasets = api.list_datasets(author=org_name)
    truncated_titles = {}
    for dataset in datasets:
        truncated_titles[dataset.id] = dataset.id
        logger.info(f"Found truncated title: {dataset.id}")
    logger.info(f"Found {len(truncated_titles)} truncated titles in total")
    return truncated_titles

def match_titles(original_titles, truncated_titles):
    logger.info("Matching original titles with truncated titles")
    matched_titles = {}
    for original_title in original_titles:
        logger.info(f"Matching original title: {original_title}")
        sanitized_title = sanitize_repo_name(original_title)
        best_match = process.extractOne(sanitized_title, truncated_titles.values(), scorer=fuzz.partial_ratio)
        if best_match and best_match[1] > 90:  # Adjust the threshold as needed
            matched_id = [k for k, v in truncated_titles.items() if v == best_match[0]][0]
            matched_titles[matched_id] = original_title
            logger.info(f"Matched {original_title} with {matched_id}")
    logger.info(f"Matched {len(matched_titles)} titles in total")
    return matched_titles

def make_pretty_name(file_name):
    
    # Ensure names like "Dr._" are correctly formatted as "Dr. "
    pretty_name = file_name.replace('Dr._', 'Dr. ')
    pretty_name = re.sub(r'Prof._', 'Prof. ', pretty_name)

    # Replace underscores with spaces using re.sub
    pretty_name = re.sub(r'_', ' ', pretty_name)
    
    # Remove any other out-of-place symbols (e.g., double spaces)
    pretty_name = re.sub(r'\s+', ' ', pretty_name).strip()
    
    return pretty_name

def update_pretty_name(matched_titles):
    for repo_id, original_title in matched_titles.items():
        pretty_name = make_pretty_name(original_title)
        new_metadata = {
            "pretty_name": pretty_name
        }
        metadata_update(
            repo_id=repo_id,
            metadata=new_metadata,
            repo_type="dataset",
            token=token,
            overwrite=True
        )
        print(f"Updated pretty_name for {repo_id} to {pretty_name}")
        time.sleep(2)  # Add a 2-second delay to avoid overloading the API

if __name__ == "__main__":
    dotenv.load_dotenv()
    org_name = os.getenv('HF_ORG_NAME')
    token = os.getenv('HF_TOKEN')
    HF_DATASET_JSON_FILE = os.getenv('HF_DATASET_JSON_FILE')
    api = HfApi()

    parser = argparse.ArgumentParser(description="Process or delete collections or datasets on Hugging Face.")
    parser.add_argument("action", choices=["process", "delete_collection", "delete_dataset", "get_dataset_names", "create_dataset_json", "update_metadata", "update_pretty_name"], help="Action to perform: 'process' to iterate and process folders, 'delete_collection' to delete a collection, 'delete_dataset' to delete a dataset, 'get_dataset_names' to get dataset names, 'create_dataset_json' to create a dataset json file, 'update_metadata' to update dataset metadata, 'update_pretty_name' to update dataset pretty names.")
    parser.add_argument("--subfolder", help="Specify a subfolder to process (optional)")
    parser.add_argument("--folder", help="Specify a folder within the subfolder to process (optional)")
    args = parser.parse_args()

    if args.action == "process":
        datasets_path = os.path.join(os.path.dirname(__file__), '..', 'datasets')
        logger.info(f"Starting to process datasets in path: {datasets_path}")
        if args.subfolder:
            logger.info(f"Processing only subfolder: {args.subfolder}")
        if args.folder:
            logger.info(f"Processing only folder: {args.folder}")
        iterate_and_process_folders(datasets_path, args.subfolder, args.folder)
        logger.info("Completed processing datasets")
    elif args.action == "delete_collection":
        delete_collection_by_slug()
    elif args.action == "delete_dataset":
        delete_datasets_in_org(org_name)
    elif args.action == "get_dataset_names":
        dataset_names = get_all_datasets_in_org(org_name)
        print("Dataset names:")
        for name in dataset_names:
            print(name)
    elif args.action == "create_dataset_json":
        create_dataset_json(org_name, HF_DATASET_JSON_FILE)
    elif args.action == "update_metadata":
        update_dataset_cards(org_name)
    elif args.action == "update_pretty_name":
        base_path = os.path.join(os.path.dirname(__file__), '..', 'datasets')
        original_titles = load_original_titles_from_folders(base_path)
        truncated_titles = get_truncated_titles(org_name)
        matched_titles = match_titles(original_titles, truncated_titles)
        update_pretty_name(matched_titles)