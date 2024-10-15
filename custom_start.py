'''
This script performs ReCODE Chat custom start-up operations.
This reduces the amount of internal hacking that must be done to OpenWebUI.
'''
import os
import json
import uuid
import base64
import mimetypes
import asyncio
from pathlib import Path

# By setting the secret key, we enable the population
# of the env.py and confi.py in the OpenWebUI app.  
os.environ["WEBUI_SECRET_KEY"] = "..."

from open_webui.config import VECTOR_DB 
from open_webui.apps.retrieval.vector.main import VectorItem
from open_webui.apps.retrieval.vector.dbs.qdrant import QdrantClient
from open_webui.apps.webui.models.knowledge import Knowledges, KnowledgeResponse, KnowledgeForm, KnowledgeUpdateForm
from open_webui.apps.webui.models.models import Models, ModelForm
from open_webui.apps.webui.models.files import Files, FileForm, FileModel
from open_webui.utils.misc import calculate_sha256_string

RECODE_USER_ID = "ReCODE"
RECODE_FILENAME_PREFIX = "RECODE_FILE_"
RECODE_KNOWLEDGE_PREFIX = "RECODE_KNOWLEDGE_"  # CTRL f before changing this, 
RECODE_MODELS_JSON_FILE = "recode_models.json"

RECODE_KNOWLEDGE_TO_MODEL_MAP = {
    "RECODE_KNOWLEDGE_diagnostic_and_therapeutic_electrophysiology_studies": "recode-electrophysiology",
}

##################################
#
# Import Prompts
#
##################################
# TODO

##################################
#
# Import Functions
#
##################################
# TODO

##################################
#
# Qdrant Setup
#
##################################
qdrant_client = QdrantClient()

async def check_qdrant_contents():
    collections = await qdrant_client.async_client.get_collections()
    collections = collections.collections
    collection_num = len(collections)
    print(f"Number of Qdrant collections: {collection_num}")

    total_points = 0
    for collection in collections:
        collection_name = collection.name
        collection_info = await qdrant_client.async_client.get_collection(collection_name)
        points_count = collection_info.points_count
        print(f"Collection '{collection_name}': {points_count} points")
        total_points += points_count if points_count is not None else 0
    print(f"Total number of points across all collections: {total_points}")
    return collection_num, total_points

async def reset_qdrant():
    '''Reset the database; delete all collections.'''
    await check_qdrant_contents()
    await qdrant_client.reset()
    num_collections, total_points = await check_qdrant_contents()
    assert num_collections == 0 and total_points == 0, "Qdrant database not reset."

def get_unstructured_json_files(directory: str) -> list[Path]:
    '''Get all unstructured JSON files in a directory.'''
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"{directory} does not exist.")
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory.")

    return list(directory.glob("*.json"))

def load_unstructured_json(filepath: str):
    '''Load an unstructured JSON file.'''
    with open(filepath, "r") as f:
        return json.load(f)

def get_text_content_from_json(json_data) -> str:
    text_content = ""
    for item in json_data:
        text_content += item["text"] + " "
    return text_content

def convert_json_to_vector_item(json_data) -> list[VectorItem]:
    '''Convert JSON data to a VectorItem.'''
    items = []
    for item in json_data:
        items.append(VectorItem(
            id=item["element_id"],
            text=item["text"],
            vector=item["embeddings"],
            metadata=item["metadata"]
        ))
    return items

async def create_collections(knowledges: list[KnowledgeResponse]) -> list[str]:
    '''
    Create collections from knowledge collections.
    
    If the knowledge collection is named `RECODE_KNOWLEDGE_recode`, 
    the Qdrant collection will be named `open_webui_RECODE_KNOWLEDGE_recode`.
    '''
    collection_names = []
    for knowledge in knowledges:
        # Qdrant collection will be named after the knowledge collection.
        collection_name = f"file-{knowledge.id}"
        collection_names.append(qdrant_client._get_collection_name(collection_name))
        
        # Get and validate the file from the knowledge collection.
        assert len(knowledge.data.get("file_ids")) == 1, f"Knowledge '{knowledge.name}' has more than one file unexpectedly."
        file = Files.get_file_by_id(knowledge.data.get("file_ids")[0])
        assert file is not None, f"File ID '{knowledge.data.get('file_ids')[0]}' not found."
        assert Path(file.meta.get("path")).exists(), f"File '{file.meta.get('path')}' does not exist."
        assert Path(file.meta.get("path")).suffix == ".json", f"File '{file.meta.get('path')}' is not a JSON file."
        
        # Load the file and get its text content.
        loaded_file = load_unstructured_json(file.meta.get("path"))
        text_content = get_text_content_from_json(loaded_file)

        # Update the file's content with the text content.
        Files.update_file_data_by_id(file.id, {"content": text_content})
        hash = calculate_sha256_string(text_content)
        Files.update_file_hash_by_id(file.id, hash)

        # Create and insert into the collection.
        print(f"Creating collection: {qdrant_client._get_collection_name(collection_name)}")
        vec_items = convert_json_to_vector_item(loaded_file)
        await qdrant_client.insert(collection_name, vec_items)
        assert await qdrant_client.has_collection(collection_name)
    
    return collection_names

async def refresh_qdrant_collections(knowledges: list[KnowledgeResponse]) -> list[str]:
    '''Refresh Qdrant collections from knowledge collections.'''
    await reset_qdrant()
    collection_names = await create_collections(knowledges)
    num_collections, total_points = await check_qdrant_contents()
    assert num_collections == len(collection_names), "Qdrant collections not refreshed."
    assert total_points > 0, "Qdrant collections not refreshed."
    return collection_names

##################################
#
# File Table Setup
#
##################################
def get_recode_file_name(name: str) -> str:
    return f"{RECODE_FILENAME_PREFIX}{name}"

def delete_recode_files() -> list[FileModel]:
    '''Delete all ReCODE files (by prefix).'''
    files = Files.get_files()
    recode_files = [file for file in files if file.filename.startswith(RECODE_FILENAME_PREFIX)]
    recode_file_ids = [file.id for file in recode_files]
    successes = [Files.delete_file_by_id(file_id) for file_id in recode_file_ids]
    assert all(successes), "Not all ReCODE files were deleted."
    print(f"Deleted {len(recode_files)} ReCODE files.")
    return Files.get_files()

def insert_new_recode_json_file(user_id: str, file: Path) -> FileModel:
    '''Insert a new file into the database.'''
    assert file.exists(), f"File '{file}' does not exist."
    assert file.suffix == ".json", f"File '{file}' is not a JSON file."
    
    # Get the file's metadata.
    id = str(uuid.uuid4())
    name = file.stem
    filename = get_recode_file_name(name)
    file_path = str(file)

    # Create a new file insertion form.
    form_data = FileForm(
        id=id,
        filename=filename,
        meta={
            "name": name,
            "content_type": "application/json",
            "size": os.path.getsize(file_path),
            "path": file_path
        }
    )
    
    # Insert the file and validate it.
    file = Files.insert_new_file(user_id, form_data)
    assert file is not None
    Files.update_file_data_by_id(file.id, {"type": "collection"})
    return file

def refresh_recode_files(files: list[Path]) -> list[FileModel]:
    '''
    Refresh ReCODE files in the database.
    
    If a file is named `recode.json`, the file will be named `RECODE_FILE_recode`.
    '''
    
    # Start fresh by deleting all ReCODE files.
    post_delete_files = delete_recode_files()

    # Insert new ReCODE files.
    new_files = []
    for file in files:
        new_file = insert_new_recode_json_file(RECODE_USER_ID, file)
        assert new_file is not None, f"ReCODE file '{file}' not inserted."
        new_files.append(new_file)

    # Check that the ReCODE files were inserted as expected.
    post_insert_files = Files.get_files()
    assert len(post_insert_files) > len(post_delete_files), "ReCODE files not inserted."
    assert len(post_insert_files) == len(files) + len(post_delete_files), "ReCODE files not inserted."
    return new_files

##################################
#
# Knowledge Table Setup
#
##################################
def get_knowledge_name(collection_name: str) -> str:
    return f"{RECODE_KNOWLEDGE_PREFIX}{collection_name}"

def get_knowledge_contents(print_str: str | None = None) -> list[KnowledgeResponse]:
    knowledge_items = Knowledges.get_knowledge_items()
    if print_str:
        print(f"{print_str}: {len(knowledge_items)}")
        print(knowledge_items)
    return knowledge_items

def insert_new_knowledge(user_id: str, knowledge_name: str, knowledge_description: str, data: dict = None) -> KnowledgeResponse:
    # Create a new knowledge collection (no data yet).
    form_data = KnowledgeForm(
        name=knowledge_name,
        description=knowledge_description,
        data=data
    )
    
    # Insert the knowledge and validate it.
    knowledge = Knowledges.insert_new_knowledge(user_id, form_data)
    assert knowledge is not None
    return knowledge

def delete_recode_knowledge() -> list[KnowledgeResponse]:
    '''Delete all ReCODE knowledge collections (by prefix).'''
    knowledge_items = get_knowledge_contents("Knowledge count before deletion")

    # Get the UUIDs of the ReCODE knowledge collections.
    ids_to_delete = []
    for knowledge in knowledge_items:
        if knowledge.name.startswith(RECODE_KNOWLEDGE_PREFIX):
            ids_to_delete.append(knowledge.id)

    # Delete the ReCODE knowledge collections.
    successes = []  
    for id_to_delete in ids_to_delete:
        successes.append(Knowledges.delete_knowledge_by_id(id_to_delete))

    assert all(successes), "Not all ReCODE knowledge collections were deleted."
    return get_knowledge_contents("Knowledge count after deletion")

def refresh_knowledge_collections(recode_files: list[FileModel]) -> list[KnowledgeResponse]:
    '''
    Fresh insert ReCODE knowledge collections. Files are associated with knowledge collections by file ID.
    First, delete all ReCODE knowledge collections.
    Then, insert new ReCODE knowledge collections anew.

    If a file is named `recode.json`, the knowledge collection will be named `RECODE_KNOWLEDGE_recode`.
    '''

    # Start fresh by deleting all ReCODE knowledge collections.
    post_delete_knowledge = delete_recode_knowledge()

    # Insert new ReCODE knowledge collections.
    new_knowledge_collections = []
    for file in recode_files:
        knowledge_name = file.meta.get("name")
        
        # Create a new knowledge collection and add the file ID.
        new_knowledge = insert_new_knowledge(
            user_id=RECODE_USER_ID, 
            knowledge_name=get_knowledge_name(knowledge_name), 
            knowledge_description=f"ReCODE Knowledge - {knowledge_name}",
            data={"file_ids": [file.id]}
        )

        new_knowledge_collections.append(new_knowledge)
        assert new_knowledge is not None, f"ReCODE knowledge '{knowledge_name}' not inserted."

    # Check that the ReCODE knowledge collections were inserted as expected.
    post_insert_knowledge = get_knowledge_contents("Knowledge count after insertion")
    assert len(post_insert_knowledge) > len(post_delete_knowledge), "ReCODE knowledge not inserted."
    assert len(post_insert_knowledge) == len(recode_files) + len(post_delete_knowledge), "ReCODE knowledge not inserted."
    return new_knowledge_collections


##################################
#
# Knowledge Preprocessing Main 
#   (File + Knowledge + Qdrant)
#
##################################
async def recode_knowledge_preprocess(recode_knowledge_dir: str = "recode_knowledge"):
    json_files = get_unstructured_json_files(recode_knowledge_dir)
    print(f"JSON files:{json_files}")

    # Refresh cycle ReCODE files.
    print("Refreshing ReCODE files.")
    recode_files = refresh_recode_files(json_files)
    print(f"ReCODE files:{recode_files}")

    # Refresh cycle ReCODE knowledge collections.
    print("Refreshing ReCODE knowledge collections.")
    recode_knowledges = refresh_knowledge_collections(recode_files)
    print(f"ReCODE knowledge collections:{recode_knowledges}")

    # Process the files into Qdrant collections.
    print("Refreshing Qdrant collections.")
    collection_names = await refresh_qdrant_collections(recode_knowledges)
    print(f"ReCODE knowledge collections:{collection_names}")

    return recode_files, recode_knowledges, collection_names


##################################
#
# Model Insertion
#
##################################
def create_recode_models_json(recode_knowledges: list[KnowledgeResponse]) -> list[dict]:
    '''Create a JSON file for ReCODE models.'''

    with open(RECODE_MODELS_JSON_FILE, "r") as f: 
        models_data = json.load(f)
    
    # For each knowledge, insert the corresponding model if it is in the mapping.
    for knowledge in recode_knowledges:
        if knowledge.name in RECODE_KNOWLEDGE_TO_MODEL_MAP:
            model_name = RECODE_KNOWLEDGE_TO_MODEL_MAP[knowledge.name]

            for model in models_data:
                if model["id"] == model_name:
                    model["info"]["meta"]["knowledge"] = [knowledge.model_dump()]
                    break
    
    print(f"ReCODE models updated: {models_data}")
    return models_data

def insert_models(models_data: list[dict]):
    '''Insert models into the database.'''

    # Delete all models.
    models = Models.get_all_models()
    model_ids = [model.id for model in models]
    successes = [Models.delete_model_by_id(model_id) for model_id in model_ids]
    assert all(successes), "Not all models were deleted."

    for spec in models_data:
        if spec["info"]["params"]["system"].startswith("@"):
            filename = spec["info"]["params"]["system"][1:]
            spec["info"]["params"]["system"] = open(filename, "r").read()
        if spec["info"]["meta"]["profile_image_url"].startswith("@"):
            filename = spec["info"]["meta"]["profile_image_url"][1:]
            mimetype, _ = mimetypes.guess_type(filename)
            data = open(filename, "rb").read()
            spec["info"]["meta"]["profile_image_url"] = f"data:{mimetype};base64,{base64.b64encode(data).decode('utf-8')}"

        form_data = ModelForm(**spec["info"])
        if model := Models.get_model_by_id(form_data.id):
            print(f"Updating model: {model.id}")
            Models.update_model_by_id(form_data.id, form_data)
        else:
            print(f"Inserting model: {form_data.id}")
            Models.insert_new_model(form_data, "custom-start")


##################################
#
# Main
#
##################################
async def main():
    if VECTOR_DB == "qdrant":
        recode_files, recode_knowledges, collection_names = await recode_knowledge_preprocess()
        models_data = create_recode_models_json(recode_knowledges)
        insert_models(models_data)

if __name__ == "__main__":
    asyncio.run(main())
