"""
knowledge_store_manager.py

A module to manage the knowledge store, including editing and merging functionality.
This module separates categorization and entities from the main knowledge store.
"""

import os
import json
import shutil
import uuid
from datetime import datetime
import knowledge_store_reader as ks
import attachment_processor

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_STORE_DIR = os.path.join(BASE_DIR, "knowledge_store")
CATEGORIES_DIR = os.path.join(KNOWLEDGE_STORE_DIR, "categories")
ENTITIES_DIR = os.path.join(KNOWLEDGE_STORE_DIR, "entities")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")

# Ensure directories exist
os.makedirs(CATEGORIES_DIR, exist_ok=True)
os.makedirs(ENTITIES_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

def save_json_file(data, file_path):
    """
    Save data to a JSON file.
    
    Parameters:
        data (dict or list): The data to save.
        file_path (str): Path to the JSON file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False

def backup_knowledge_store():
    """
    Create a backup of the knowledge store.
    
    Returns:
        str: Path to the backup directory, or None if backup failed.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BASE_DIR, f"knowledge_store_backup_{timestamp}")
    
    # Make sure the backup directory doesn't already exist
    counter = 1
    original_backup_dir = backup_dir
    while os.path.exists(backup_dir):
        backup_dir = f"{original_backup_dir}_{counter}"
        counter += 1
    
    try:
        shutil.copytree(KNOWLEDGE_STORE_DIR, backup_dir)
        return backup_dir
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

# Event management functions
def get_event(event_id):
    """
    Get a specific event by ID.
    
    Parameters:
        event_id (str): The event ID.
        
    Returns:
        dict: The event, or None if not found.
    """
    events = ks.get_events()
    event = next((e for e in events if e["id"] == event_id), None)
    return event

def update_event(event_id, updated_data):
    """
    Update an event with new data.
    
    Parameters:
        event_id (str): The event ID.
        updated_data (dict): The updated event data.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    # Create a backup first
    backup_dir = backup_knowledge_store()
    if not backup_dir:
        return False
    
    # Get all events
    events = ks.get_events()
    
    # Find the event to update
    for i, event in enumerate(events):
        if event["id"] == event_id:
            # Update the event
            events[i] = updated_data
            
            # Save the updated events
            events_path = os.path.join(KNOWLEDGE_STORE_DIR, "events.json")
            if save_json_file(events, events_path):
                return True
            else:
                # Restore from backup if save failed
                shutil.rmtree(KNOWLEDGE_STORE_DIR)
                shutil.copytree(backup_dir, KNOWLEDGE_STORE_DIR)
                return False
    
    return False

def merge_events(event_id1, event_id2):
    """
    Merge two events into one.
    
    Parameters:
        event_id1 (str): The first event ID.
        event_id2 (str): The second event ID.
        
    Returns:
        str: The ID of the merged event, or None if merge failed.
    """
    # Create a backup first
    backup_dir = backup_knowledge_store()
    if not backup_dir:
        return None
    
    # Get all events
    events = ks.get_events()
    
    # Find the events to merge
    event1 = next((e for e in events if e["id"] == event_id1), None)
    event2 = next((e for e in events if e["id"] == event_id2), None)
    
    if not event1 or not event2:
        return None
    
    # Create a merged event
    merged_event = {
        "id": event1["id"],  # Keep the ID of the first event
        "guid": event1.get("guid"),
        "date": event1["date"],  # Keep the date of the first event
        "age": event1["age"],
        "title": f"{event1['title']} + {event2['title']}",
        "content": f"{event1['content']}\n\n{event2['content']}",
        "specialty": event1["specialty"],
        "evernote_links": {**event1.get("evernote_links", {}), **event2.get("evernote_links", {})},
    }
    
    # Merge attachments
    merged_event["attachments"] = event1.get("attachments", []) + event2.get("attachments", [])
    
    # Merge personnel
    merged_personnel = event1.get("personnel", []).copy()
    for person in event2.get("personnel", []):
        if not any(p["name"] == person["name"] for p in merged_personnel):
            merged_personnel.append(person)
    merged_event["personnel"] = merged_personnel
    
    # Merge facilities
    merged_facilities = event1.get("facilities", []).copy()
    for facility in event2.get("facilities", []):
        if not any(f["name"] == facility["name"] for f in merged_facilities):
            merged_facilities.append(facility)
    merged_event["facilities"] = merged_facilities
    
    # Merge events
    merged_event_items = event1.get("events", []).copy()
    for event_item in event2.get("events", []):
        if not any(e["content"] == event_item["content"] for e in merged_event_items):
            merged_event_items.append(event_item)
    merged_event["events"] = merged_event_items
    
    # Merge PHB categories
    merged_phb_categories = event1.get("phb_categories", []).copy()
    for category in event2.get("phb_categories", []):
        if not any(cat["category"] == category["category"] for cat in merged_phb_categories):
            merged_phb_categories.append(category)
    merged_event["phb_categories"] = merged_phb_categories
    
    # Merge PHB supports
    merged_phb_supports = event1.get("phb_supports", []).copy()
    for support in event2.get("phb_supports", []):
        if not any(sup["support"] == support["support"] for sup in merged_phb_supports):
            merged_phb_supports.append(support)
    merged_event["phb_supports"] = merged_phb_supports
    
    # Merge patient identifiers
    merged_identifiers = {**event1.get("patient_identifiers", {}), **event2.get("patient_identifiers", {})}
    merged_event["patient_identifiers"] = merged_identifiers
    
    # Update the events list
    new_events = [e for e in events if e["id"] != event_id1 and e["id"] != event_id2]
    new_events.append(merged_event)
    
    # Save the updated events
    events_path = os.path.join(KNOWLEDGE_STORE_DIR, "events.json")
    if save_json_file(new_events, events_path):
        return merged_event["id"]
    else:
        # Restore from backup if save failed
        shutil.rmtree(KNOWLEDGE_STORE_DIR)
        shutil.copytree(backup_dir, KNOWLEDGE_STORE_DIR)
        return None

# Category management functions
def get_categories():
    """
    Get all categories.
    
    Returns:
        dict: Dictionary of categories.
    """
    categories_path = os.path.join(CATEGORIES_DIR, "categories.json")
    
    if os.path.exists(categories_path):
        with open(categories_path, 'r') as f:
            return json.load(f)
    else:
        # Initialize with PHB categories
        phb_categories = ks.get_phb_categories()
        save_json_file(phb_categories, categories_path)
        return phb_categories

def update_category(category_name, updated_data):
    """
    Update a category with new data.
    
    Parameters:
        category_name (str): The category name.
        updated_data (dict): The updated category data.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    categories = get_categories()
    
    # Update the category
    categories[category_name] = updated_data
    
    # Save the updated categories
    categories_path = os.path.join(CATEGORIES_DIR, "categories.json")
    return save_json_file(categories, categories_path)

def add_category(category_name, category_data):
    """
    Add a new category.
    
    Parameters:
        category_name (str): The category name.
        category_data (dict): The category data.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    categories = get_categories()
    
    # Check if category already exists
    if category_name in categories:
        return False
    
    # Add the new category
    categories[category_name] = category_data
    
    # Save the updated categories
    categories_path = os.path.join(CATEGORIES_DIR, "categories.json")
    return save_json_file(categories, categories_path)

def delete_category(category_name):
    """
    Delete a category.
    
    Parameters:
        category_name (str): The category name.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    categories = get_categories()
    
    # Check if category exists
    if category_name not in categories:
        return False
    
    # Delete the category
    del categories[category_name]
    
    # Save the updated categories
    categories_path = os.path.join(CATEGORIES_DIR, "categories.json")
    return save_json_file(categories, categories_path)

# Entity management functions
def get_entities():
    """
    Get all entities.
    
    Returns:
        dict: Dictionary of entities.
    """
    entities_path = os.path.join(ENTITIES_DIR, "entities.json")
    
    if os.path.exists(entities_path):
        with open(entities_path, 'r') as f:
            return json.load(f)
    else:
        # Initialize with empty entities
        entities = {
            "personnel": {},
            "facilities": {},
            "specialties": {}
        }
        save_json_file(entities, entities_path)
        return entities

def update_entity(entity_type, entity_name, updated_data):
    """
    Update an entity with new data.
    
    Parameters:
        entity_type (str): The entity type (personnel, facilities, specialties).
        entity_name (str): The entity name.
        updated_data (dict): The updated entity data.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    entities = get_entities()
    
    # Check if entity type exists
    if entity_type not in entities:
        return False
    
    # Update the entity
    entities[entity_type][entity_name] = updated_data
    
    # Save the updated entities
    entities_path = os.path.join(ENTITIES_DIR, "entities.json")
    return save_json_file(entities, entities_path)

def add_entity(entity_type, entity_name, entity_data):
    """
    Add a new entity.
    
    Parameters:
        entity_type (str): The entity type (personnel, facilities, specialties).
        entity_name (str): The entity name.
        entity_data (dict): The entity data.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    entities = get_entities()
    
    # Check if entity type exists
    if entity_type not in entities:
        return False
    
    # Check if entity already exists
    if entity_name in entities[entity_type]:
        return False
    
    # Add the new entity
    entities[entity_type][entity_name] = entity_data
    
    # Save the updated entities
    entities_path = os.path.join(ENTITIES_DIR, "entities.json")
    return save_json_file(entities, entities_path)

def delete_entity(entity_type, entity_name):
    """
    Delete an entity.
    
    Parameters:
        entity_type (str): The entity type (personnel, facilities, specialties).
        entity_name (str): The entity name.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    entities = get_entities()
    
    # Check if entity type exists
    if entity_type not in entities:
        return False
    
    # Check if entity exists
    if entity_name not in entities[entity_type]:
        return False
    
    # Delete the entity
    del entities[entity_type][entity_name]
    
    # Save the updated entities
    entities_path = os.path.join(ENTITIES_DIR, "entities.json")
    return save_json_file(entities, entities_path)

# Document upload and processing functions
def handle_uploaded_file(file, file_type="document"):
    """
    Handle an uploaded file.
    
    Parameters:
        file: The uploaded file object.
        file_type (str): The type of file (document, image, etc.).
        
    Returns:
        dict: Information about the uploaded file, or None if upload failed.
    """
    try:
        # Generate a unique ID for this file
        file_id = str(uuid.uuid4())
        
        # Create a directory for this upload
        upload_dir = os.path.join(UPLOADS_DIR, file_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, 'wb') as f:
            f.write(file.read())
        
        # Determine mime type based on file extension
        _, ext = os.path.splitext(file.filename)
        mime_type = get_mime_type(ext)
        
        # Create file info
        file_info = {
            "id": file_id,
            "file_name": file.filename,
            "file_path": file_path,
            "mime_type": mime_type,
            "upload_time": datetime.now().isoformat(),
            "file_type": file_type
        }
        
        # Save file info
        info_path = os.path.join(upload_dir, "info.json")
        save_json_file(file_info, info_path)
        
        return file_info
    except Exception as e:
        print(f"Error handling uploaded file: {e}")
        return None

def get_mime_type(extension):
    """
    Get mime type based on file extension.
    """
    extension = extension.lower()
    
    if extension in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif extension == '.png':
        return 'image/png'
    elif extension == '.pdf':
        return 'application/pdf'
    elif extension in ['.doc', '.docx']:
        return 'application/msword'
    elif extension == '.txt':
        return 'text/plain'
    elif extension == '.enex':
        return 'application/enex+xml'
    else:
        return 'application/octet-stream'

def process_uploaded_file(file_info):
    """
    Process an uploaded file.
    
    Parameters:
        file_info (dict): Information about the uploaded file.
        
    Returns:
        dict: Processed file information, or None if processing failed.
    """
    try:
        # Process the file based on its type
        if file_info["mime_type"].startswith("image/"):
            # Process image
            processed_info = attachment_processor.process_image(file_info["file_path"])
        elif file_info["mime_type"] == "application/pdf":
            # Process PDF
            processed_info = attachment_processor.process_pdf(file_info["file_path"])
        elif file_info["mime_type"] in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                      "application/msword"]:
            # Process DOCX
            processed_info = attachment_processor.process_docx(file_info["file_path"])
        elif file_info["mime_type"] == "application/enex+xml":
            # Process ENEX file
            from index_documents import index_enex_files
            processed_info = "ENEX file will be processed during the next indexing run."
        else:
            # For other file types, just note the type
            file_size = os.path.getsize(file_info["file_path"]) / 1024  # Size in KB
            processed_info = f"[{file_info['mime_type']}: {file_size:.1f} KB] No text extraction available for this file type."
        
        # Update file info with processed info
        file_info["processed_info"] = processed_info
        file_info["processed_time"] = datetime.now().isoformat()
        
        # Save updated file info
        upload_dir = os.path.join(UPLOADS_DIR, file_info["id"])
        info_path = os.path.join(upload_dir, "info.json")
        save_json_file(file_info, info_path)
        
        return file_info
    except Exception as e:
        print(f"Error processing uploaded file: {e}")
        return None

def add_uploaded_file_to_knowledge_store(file_info, event_id=None):
    """
    Add an uploaded file to the knowledge store.
    
    Parameters:
        file_info (dict): Information about the uploaded file.
        event_id (str): The ID of the event to associate the file with, or None to create a new event.
        
    Returns:
        str: The ID of the event the file was added to, or None if addition failed.
    """
    try:
        # Create a backup first
        backup_dir = backup_knowledge_store()
        if not backup_dir:
            return None
        
        # Copy the file to the attachments directory
        file_id = file_info["id"]
        attachment_dir = os.path.join(ATTACHMENTS_DIR, file_id)
        os.makedirs(attachment_dir, exist_ok=True)
        
        dest_path = os.path.join(attachment_dir, file_info["file_name"])
        shutil.copy2(file_info["file_path"], dest_path)
        
        # Create attachment info
        attachment = {
            "file_name": file_info["file_name"],
            "file_path": dest_path,
            "mime_type": file_info["mime_type"],
            "upload_time": file_info["upload_time"]
        }
        
        # Add processed info if available
        if "processed_info" in file_info:
            attachment["extracted_text"] = file_info["processed_info"]
            attachment["processed_at"] = file_info["processed_time"]
        
        # If event_id is provided, add the attachment to that event
        if event_id:
            events = ks.get_events()
            event = next((e for e in events if e["id"] == event_id), None)
            
            if not event:
                return None
            
            # Add the attachment to the event
            if "attachments" not in event:
                event["attachments"] = []
            
            event["attachments"].append(attachment)
            
            # Update the event
            for i, e in enumerate(events):
                if e["id"] == event_id:
                    events[i] = event
                    break
            
            # Save the updated events
            events_path = os.path.join(KNOWLEDGE_STORE_DIR, "events.json")
            if save_json_file(events, events_path):
                return event_id
            else:
                # Restore from backup if save failed
                shutil.rmtree(KNOWLEDGE_STORE_DIR)
                shutil.copytree(backup_dir, KNOWLEDGE_STORE_DIR)
                return None
        else:
            # Create a new event
            new_event = {
                "id": file_id,
                "guid": str(uuid.uuid4()),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "age": "Unknown",
                "title": f"Uploaded: {file_info['file_name']}",
                "content": f"This event was created from an uploaded file: {file_info['file_name']}",
                "specialty": "Unknown",
                "attachments": [attachment]
            }
            
            # Add the new event to the events list
            events = ks.get_events()
            events.append(new_event)
            
            # Save the updated events
            events_path = os.path.join(KNOWLEDGE_STORE_DIR, "events.json")
            if save_json_file(events, events_path):
                return new_event["id"]
            else:
                # Restore from backup if save failed
                shutil.rmtree(KNOWLEDGE_STORE_DIR)
                shutil.copytree(backup_dir, KNOWLEDGE_STORE_DIR)
                return None
    except Exception as e:
        print(f"Error adding uploaded file to knowledge store: {e}")
        return None

# Vector store management functions
def rebuild_vector_store():
    """
    Rebuild the vector store from all events.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        events = ks.get_events()
        vector_store = attachment_processor.create_vector_store(events)
        return vector_store is not None
    except Exception as e:
        print(f"Error rebuilding vector store: {e}")
        return False

# Initialize the knowledge store if needed
def initialize_knowledge_store():
    """
    Initialize the knowledge store if it doesn't exist.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(KNOWLEDGE_STORE_DIR):
        os.makedirs(KNOWLEDGE_STORE_DIR, exist_ok=True)
        
        # Create empty events file
        events_path = os.path.join(KNOWLEDGE_STORE_DIR, "events.json")
        save_json_file([], events_path)
        
        # Create empty notes file
        notes_path = os.path.join(KNOWLEDGE_STORE_DIR, "notes.json")
        save_json_file([], notes_path)
        
        # Create empty external_docs file
        docs_path = os.path.join(KNOWLEDGE_STORE_DIR, "external_docs.json")
        save_json_file([], docs_path)
        
        # Create empty processed_attachments file
        attachments_path = os.path.join(KNOWLEDGE_STORE_DIR, "processed_attachments.json")
        save_json_file([], attachments_path)
        
        # Create empty processed_external_docs file
        external_docs_path = os.path.join(KNOWLEDGE_STORE_DIR, "processed_external_docs.json")
        save_json_file([], external_docs_path)
        
        # Initialize categories
        get_categories()
        
        # Initialize entities
        get_entities()
        
        return True
    
    return True

# Initialize the knowledge store
initialize_knowledge_store()
