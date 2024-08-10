import os
import dotenv
import argparse
from datasets import load_dataset, Dataset
from huggingface_hub import HfApi, HfFolder, list_collections, create_collection, add_collection_item
import json

dotenv.load_dotenv()

def upload_datasets_to_huggingface(org_name):
    datasets_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")
    token = HfFolder.get_token()
    
    if not token:
        raise ValueError("You need to be logged in to Hugging Face to upload datasets.")
    
    collections = get_hf_collection_slugs(org_name)
    
    for folder_name in os.listdir(datasets_folder):
        folder_path = os.path.join(datasets_folder, folder_name)
        if os.path.isdir(folder_path):
            collection_slug = next((slug for title, slug in collections.items() if folder_name in slug), None)
            if collection_slug:
                upload_folder_datasets(folder_path, folder_name, org_name, token, collection_slug)
            else:
                print(f"No collection found for folder: {folder_name}")

def upload_folder_datasets(folder_path, folder_name, org_name, token, collection_slug):
    for subfolder in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path):
            for file in os.listdir(subfolder_path):
                file_path = os.path.join(subfolder_path, file)
                dataset = load_dataset_from_file(file_path)
                dataset_name = os.path.splitext(file)[0]
                dataset.push_to_hub(f"{org_name}/{dataset_name}", token=token)
                add_collection_item(
                    collection_slug=collection_slug,
                    item_id=dataset_name,
                    item_type="dataset",
                    token=token,
                    exists_ok=True
                )
                print(f"Uploaded {dataset_name} to {collection_slug}")

def load_dataset_from_file(file_path):
    if file_path.endswith('.csv'):
        return load_dataset('csv', data_files=file_path)
    elif file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            return Dataset.from_dict({"data": data})
        else:
            return Dataset.from_dict(data)
    elif file_path.endswith('.txt'):
        with open(file_path, 'r') as f:
            content = f.read()
        return Dataset.from_dict({"text": [content]})
    else:
        raise ValueError(f"Unsupported file extension for file: {file_path}")

def list_datasets(org_name):
    api = HfApi()
    datasets = api.list_datasets(author=org_name, expand=["author", 
                                                          "cardData",
                                                          "createdAt" 
                                                          ])
    datasets_list = list(datasets)
    for dataset in datasets_list:
        print(dataset)

def create_collections_from_folders(org_name):
    datasets_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")
    api = HfApi()
    token = HfFolder.get_token()
    
    if not token:
        raise ValueError("You need to be logged in to Hugging Face to create collections.")
    
    for folder in os.listdir(datasets_folder):
        folder_path = os.path.join(datasets_folder, folder)
        if os.path.isdir(folder_path):
            create_collection(
                title=folder,
                namespace=org_name,
                description=None,
                private=False,
                exists_ok=True,
                token=token
            )
            print(f"Created or updated collection: {org_name}/{folder}")

def get_hf_collection_slugs(org_name):
    collections = list_collections(owner=org_name, limit=10)
    collection_dict = {collection.title: collection.slug for collection in collections}
    for slug in collection_dict.values():
        print(slug)
    return collection_dict

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a specific function in the script.")
    parser.add_argument("function", choices=["upload_datasets_to_huggingface", "list_datasets", "create_collections_from_folders", "list_collections"], help="Function to run")
    parser.add_argument("org_name", help="Organization name on Hugging Face")
    args = parser.parse_args()
    
    if args.function == "upload_datasets_to_huggingface":
        upload_datasets_to_huggingface(args.org_name)
    elif args.function == "list_datasets":
        list_datasets(args.org_name)
    elif args.function == "create_collections_from_folders":
        create_collections_from_folders(args.org_name)
    elif args.function == "list_collections":
        get_hf_collection_slugs(args.org_name)