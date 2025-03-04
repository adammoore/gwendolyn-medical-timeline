"""
knowledge_store_reader.py

A module to read data from the knowledge store.
"""

import os
import json
from datetime import datetime

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_STORE_DIR = os.path.join(BASE_DIR, "knowledge_store")

def load_json_file(file_path):
    """
    Load a JSON file.
    
    Parameters:
        file_path (str): Path to the JSON file.
        
    Returns:
        dict or list: The loaded JSON data.
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_events():
    """
    Get all events from the knowledge store.
    
    Returns:
        list: List of events.
    """
    events_path = os.path.join(KNOWLEDGE_STORE_DIR, "events.json")
    events = load_json_file(events_path)
    
    if events is None:
        return []
    
    # Sort events by date
    events.sort(key=lambda x: x.get("date", ""))
    
    return events

def get_notes():
    """
    Get all notes from the knowledge store.
    
    Returns:
        list: List of notes.
    """
    notes_path = os.path.join(KNOWLEDGE_STORE_DIR, "notes.json")
    return load_json_file(notes_path) or []

def get_external_docs():
    """
    Get all external documents from the knowledge store.
    
    Returns:
        list: List of external documents.
    """
    docs_path = os.path.join(KNOWLEDGE_STORE_DIR, "external_docs.json")
    return load_json_file(docs_path) or []

def get_processed_attachments():
    """
    Get all processed attachments from the knowledge store.
    
    Returns:
        list: List of processed attachments.
    """
    attachments_path = os.path.join(KNOWLEDGE_STORE_DIR, "processed_attachments.json")
    return load_json_file(attachments_path) or []

def get_processed_external_docs():
    """
    Get all processed external documents from the knowledge store.
    
    Returns:
        list: List of processed external documents.
    """
    docs_path = os.path.join(KNOWLEDGE_STORE_DIR, "processed_external_docs.json")
    return load_json_file(docs_path) or []

def get_patient_info():
    """
    Get patient information from the knowledge store.
    
    Returns:
        dict: Patient information.
    """
    patient_info_path = os.path.join(KNOWLEDGE_STORE_DIR, "patient_info.json")
    return load_json_file(patient_info_path) or {}

def get_phb_categories():
    """
    Get PHB categories from the knowledge store.
    
    Returns:
        dict: PHB categories.
    """
    phb_path = os.path.join(KNOWLEDGE_STORE_DIR, "phb_categories.json")
    return load_json_file(phb_path) or {}

def get_diagnostic_journey(events=None):
    """
    Extract the diagnostic journey from events.
    
    Parameters:
        events (list): List of events. If None, events will be loaded from the knowledge store.
        
    Returns:
        list: List of diagnostic events.
    """
    if events is None:
        events = get_events()
    
    # Track specialties and diagnoses over time
    specialties = set()
    diagnoses = set()
    diagnostic_events = []
    
    for event in events:
        new_specialty = False
        new_diagnosis = False
        
        # Check if this event introduces a new specialty
        if event["specialty"] not in specialties and event["specialty"] != "Unknown":
            specialties.add(event["specialty"])
            new_specialty = True
        
        # Check if this event introduces a new diagnosis
        for event_item in event["events"]:
            if event_item["type"] == "Diagnosis":
                diagnosis = event_item["content"].strip()
                if diagnosis and diagnosis not in diagnoses:
                    diagnoses.add(diagnosis)
                    new_diagnosis = True
        
        # If this event introduces something new, add it to the diagnostic journey
        if new_specialty or new_diagnosis:
            diagnostic_events.append({
                "id": event["id"],
                "guid": event.get("guid"),
                "date": event["date"],
                "age": event["age"],
                "title": event["title"],
                "specialty": event["specialty"],
                "new_specialty": new_specialty,
                "new_diagnosis": new_diagnosis,
                "current_specialties": list(specialties),
                "diagnoses": [d for d in event["events"] if d["type"] == "Diagnosis"],
                "evernote_links": event.get("evernote_links", {}),
                "attachments": event.get("attachments", [])
            })
    
    return diagnostic_events

def get_knowledge_store_stats():
    """
    Get statistics about the knowledge store.
    
    Returns:
        dict: Statistics about the knowledge store.
    """
    events = get_events()
    notes = get_notes()
    external_docs = get_external_docs()
    processed_attachments = get_processed_attachments()
    processed_external_docs = get_processed_external_docs()
    
    # Count attachments
    attachment_count = sum(len(event.get("attachments", [])) for event in events)
    
    # Count unique personnel
    personnel = set()
    for event in events:
        for person in event.get("personnel", []):
            if person["name"] != "Unknown":
                personnel.add(person["name"])
    
    # Count unique facilities
    facilities = set()
    for event in events:
        for facility in event.get("facilities", []):
            if facility["name"] != "Unknown":
                facilities.add(facility["name"])
    
    # Count unique specialties
    specialties = set()
    for event in events:
        if event["specialty"] != "Unknown":
            specialties.add(event["specialty"])
    
    # Get date range
    if events:
        start_date = min(event["date"] for event in events)
        end_date = max(event["date"] for event in events)
        date_range = f"{start_date} to {end_date}"
    else:
        date_range = "N/A"
    
    # Get last updated time
    try:
        mtime = os.path.getmtime(os.path.join(KNOWLEDGE_STORE_DIR, "events.json"))
        last_updated = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except:
        last_updated = "Unknown"
    
    return {
        "events_count": len(events),
        "notes_count": len(notes),
        "external_docs_count": len(external_docs),
        "attachment_count": attachment_count,
        "personnel_count": len(personnel),
        "facilities_count": len(facilities),
        "specialties_count": len(specialties),
        "date_range": date_range,
        "last_updated": last_updated
    }

def is_knowledge_store_available():
    """
    Check if the knowledge store is available.
    
    Returns:
        bool: True if the knowledge store is available, False otherwise.
    """
    return os.path.exists(KNOWLEDGE_STORE_DIR) and os.path.exists(os.path.join(KNOWLEDGE_STORE_DIR, "events.json"))
