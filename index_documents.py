"""
index_documents.py

A script to index documents from Evernote export files and external documents,
creating a knowledge store that can be used by the main application.
"""

import os
import sys
import json
import hashlib
import shutil
from datetime import datetime
import argparse
from tqdm import tqdm

# Import our modules
from enex_parser import parse_enex
import attachment_processor
import improved_phb_details as phb_details
import patient_info
import evernote_utils

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENEX_DIR = BASE_DIR
DOCS_DIR = os.path.join(BASE_DIR, "docs")
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")
KNOWLEDGE_STORE_DIR = os.path.join(BASE_DIR, "knowledge_store")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db")

# Ensure directories exist
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
os.makedirs(KNOWLEDGE_STORE_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

def index_enex_files():
    """
    Index all ENEX files in the ENEX_DIR.
    """
    print("Indexing ENEX files...")
    
    # Get all ENEX files in the directory
    enex_files = [os.path.join(ENEX_DIR, f) for f in os.listdir(ENEX_DIR) if f.endswith('.enex')]
    
    all_notes = []
    
    for file_path in tqdm(enex_files, desc="Parsing ENEX files"):
        print(f"Parsing {file_path}...")
        notes = parse_enex(file_path)
        all_notes.extend(notes)
    
    # Save all notes to knowledge store
    notes_path = os.path.join(KNOWLEDGE_STORE_DIR, "notes.json")
    with open(notes_path, 'w') as f:
        json.dump(all_notes, f)
    
    print(f"Indexed {len(all_notes)} notes from {len(enex_files)} ENEX files.")
    return all_notes

def index_external_documents():
    """
    Index all documents in the DOCS_DIR.
    """
    print("Indexing external documents...")
    
    # Get all files in the docs directory
    doc_files = []
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if not file.startswith('.'):  # Skip hidden files
                doc_files.append(os.path.join(root, file))
    
    all_docs = []
    
    for file_path in tqdm(doc_files, desc="Processing documents"):
        # Generate a unique ID for this document
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        
        # Determine mime type based on file extension
        _, ext = os.path.splitext(file_path)
        mime_type = get_mime_type(ext)
        
        # Copy file to attachments directory
        doc_dir = os.path.join(ATTACHMENTS_DIR, file_hash)
        os.makedirs(doc_dir, exist_ok=True)
        
        dest_path = os.path.join(doc_dir, os.path.basename(file_path))
        if not os.path.exists(dest_path):
            shutil.copy2(file_path, dest_path)
        
        # Create document entry
        doc = {
            "id": file_hash,
            "file_name": os.path.basename(file_path),
            "file_path": dest_path,
            "mime_type": mime_type,
            "source": "external",
            "indexed_at": datetime.now().isoformat()
        }
        
        all_docs.append(doc)
    
    # Save all documents to knowledge store
    docs_path = os.path.join(KNOWLEDGE_STORE_DIR, "external_docs.json")
    with open(docs_path, 'w') as f:
        json.dump(all_docs, f)
    
    print(f"Indexed {len(all_docs)} external documents.")
    return all_docs

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
    else:
        return 'application/octet-stream'

def process_all_documents(notes, external_docs):
    """
    Process all documents using the attachment processor.
    """
    print("Processing all documents...")
    
    # Extract attachments from notes
    attachments = []
    for note in tqdm(notes, desc="Extracting attachments from notes"):
        if "attachments" in note and note["attachments"]:
            for attachment in note["attachments"]:
                attachments.append({
                    "note_id": note["id"],
                    "attachment": attachment
                })
    
    # Process attachments
    processed_attachments = []
    for item in tqdm(attachments, desc="Processing note attachments"):
        processed_attachment = attachment_processor.process_attachment(item["attachment"])
        processed_attachments.append({
            "note_id": item["note_id"],
            "attachment": processed_attachment
        })
    
    # Process external documents
    processed_external_docs = []
    for doc in tqdm(external_docs, desc="Processing external documents"):
        processed_doc = attachment_processor.process_attachment(doc)
        processed_external_docs.append(processed_doc)
    
    # Save processed attachments to knowledge store
    attachments_path = os.path.join(KNOWLEDGE_STORE_DIR, "processed_attachments.json")
    with open(attachments_path, 'w') as f:
        json.dump(processed_attachments, f)
    
    # Save processed external documents to knowledge store
    external_docs_path = os.path.join(KNOWLEDGE_STORE_DIR, "processed_external_docs.json")
    with open(external_docs_path, 'w') as f:
        json.dump(processed_external_docs, f)
    
    print(f"Processed {len(processed_attachments)} note attachments and {len(processed_external_docs)} external documents.")
    return processed_attachments, processed_external_docs

def create_events(notes, processed_attachments):
    """
    Create events from notes and processed attachments.
    """
    print("Creating events...")
    
    # Create a lookup for processed attachments by note_id
    attachment_lookup = {}
    for item in processed_attachments:
        note_id = item["note_id"]
        if note_id not in attachment_lookup:
            attachment_lookup[note_id] = []
        attachment_lookup[note_id].append(item["attachment"])
    
    # Create events from notes
    from enex_parser import extract_events
    events = extract_events(notes)
    
    # Update events with processed attachments
    for event in events:
        note_id = event["id"]
        if note_id in attachment_lookup:
            event["attachments"] = attachment_lookup[note_id]
    
    # Update events with information from attachments
    events = attachment_processor.process_all_attachments(events)
    
    # Save events to knowledge store
    events_path = os.path.join(KNOWLEDGE_STORE_DIR, "events.json")
    with open(events_path, 'w') as f:
        json.dump(events, f)
    
    print(f"Created {len(events)} events.")
    return events

def create_vector_store(events, processed_external_docs):
    """
    Create a vector store from events and processed external documents.
    """
    print("Creating vector store...")
    
    # Create vector store
    vector_store = attachment_processor.create_vector_store(events)
    
    if vector_store:
        print("Vector store created successfully.")
    else:
        print("Failed to create vector store.")

def update_patient_info(events):
    """
    Update patient information from events.
    """
    print("Updating patient information...")
    
    # Update patient info
    updated_info = attachment_processor.update_patient_info_from_events(events)
    patient_info.update_patient_info(updated_info)
    
    # Save updated patient info to knowledge store
    patient_info_path = os.path.join(KNOWLEDGE_STORE_DIR, "patient_info.json")
    with open(patient_info_path, 'w') as f:
        json.dump(patient_info.PATIENT_INFO, f)
    
    print("Patient information updated.")

def update_phb_info():
    """
    Update PHB information with the new text.
    """
    print("Updating PHB information...")
    
    # Update PHB categories with new text
    phb_categories = phb_details.PHB_CATEGORIES.copy()
    
    # Update Respiratory category
    phb_categories["Respiratory"]["description"] = "Severe, frequent, hard-to-predict apnoea not related to seizures"
    phb_categories["Respiratory"]["details"] = [
        "Documented history of central and obstructive sleep apnoea, ventilation, and respiratory arrests",
        "At least 5 risk of death full respiratory arrests, including prolonged periods of mechanically assisted breathing",
        "Early childhood spent with CPAP assisted ventilation at night",
        "Upper and lower respiratory infections - critical risk of death incident following RSV infection",
        "Collapsed lungs due to respiratory complications",
        "Failed fit to fly test – requiring 2l flow of oxygen for anything but the very shortest of flights",
        "Weaned off ventilation but deterioration has led to request for another sleep study",
        "Remains under specialist respiratory and sleep teams",
        "Respiratory health supported by prophylactic antibiotics (Azithromycin)"
    ]
    
    # Update Nutrition category
    phb_categories["Nutrition"]["description"] = "Problems with intake of food and drink"
    phb_categories["Nutrition"]["details"] = [
        "Vomiting and reflux due to gastric issues (including GERD) and atypical anatomy",
        "Oval epiglottis which can lead to needing tube feeding, thickeners or drinking through a straw",
        "Significant damage from reflux (stone cobbling burns observed)",
        "Continually monitored medication regime",
        "Needs to eat as soon as she wakes up to avoid reflux/vomiting",
        "Prefers drinking through a straw to reduce choking risk",
        "Significant dietary and behavioral complexities requiring coordinated specialist input",
        "Currently classed as obese, severely impacting self-directed activities and movement",
        "Food obsession manifesting as impulsive grabbing of food and drink",
        "PICA – will try to chew the first thing available when hungry"
    ]
    
    # Update Mobility category
    phb_categories["Mobility"]["description"] = "Mobility Impairments"
    phb_categories["Mobility"]["details"] = [
        "Multiple major orthopaedic surgeries (osteotomy and patella stabilization)",
        "Atypical anatomy (flat bones, only partial kneecap, one leg longer than the other)",
        "Persistent lower-limb instability and severe pain",
        "Pending further specialist surgery on both legs in a unique procedure",
        "Previous procedures include severed hamstring, moved ligaments, surgically broken leg, and reshaped hip",
        "Regularly requires 2:1 assistance for transfers/positioning to prevent harm or dislocation",
        "Relies on a bespoke NHS wheelchair",
        "Neurology identified significant changes between head and neck joints, increasing injury risk"
    ]
    
    # Update Continence category
    phb_categories["Continence"]["description"] = "Continence & Toileting Needs"
    phb_categories["Continence"]["details"] = [
        "Cannot wipe or clean herself independently",
        "Has regular accidents",
        "Cared for by both the continence team and urology nurses",
        "Recurrent UTIs and PDA-related avoidance behaviours worsen these issues",
        "Suffers from gynae infections",
        "Monthly bleeds on and off since approximately age 7",
        "No capacity to change pads or manage personal hygiene",
        "Requires consistent, personalised care that respects dignity while managing challenging and avoidant behavior"
    ]
    
    # Save updated PHB categories to knowledge store
    phb_path = os.path.join(KNOWLEDGE_STORE_DIR, "phb_categories.json")
    with open(phb_path, 'w') as f:
        json.dump(phb_categories, f)
    
    print("PHB information updated.")

def main():
    """
    Main function to run the indexing script.
    """
    parser = argparse.ArgumentParser(description="Index documents for Gwendolyn's Medical Timeline")
    parser.add_argument("--enex-only", action="store_true", help="Only index ENEX files")
    parser.add_argument("--docs-only", action="store_true", help="Only index external documents")
    parser.add_argument("--update-phb", action="store_true", help="Update PHB information")
    args = parser.parse_args()
    
    # Check OCR status
    ocr_status = attachment_processor.get_ocr_status()
    print("OCR Status:")
    print(f"  Tesseract available: {ocr_status['tesseract_available']}")
    print(f"  PDF to Image available: {ocr_status['pdf_image_available']}")
    print(f"  OpenCV available: {ocr_status['cv2_available']}")
    print(f"  DOCX processing available: {ocr_status['docx_available']}")
    print(f"  PDF processing available: {ocr_status['pdf_available']}")
    print(f"  Vector DB available: {ocr_status['vector_db_available']}")
    print()
    
    notes = []
    external_docs = []
    
    if args.update_phb:
        update_phb_info()
        return
    
    if not args.docs_only:
        notes = index_enex_files()
    
    if not args.enex_only:
        external_docs = index_external_documents()
    
    processed_attachments, processed_external_docs = process_all_documents(notes, external_docs)
    events = create_events(notes, processed_attachments)
    create_vector_store(events, processed_external_docs)
    update_patient_info(events)
    
    print("Indexing complete!")
    print(f"Indexed {len(notes)} notes, {len(external_docs)} external documents, and created {len(events)} events.")
    print(f"Knowledge store created at: {KNOWLEDGE_STORE_DIR}")
    print(f"Vector store created at: {VECTOR_DB_DIR}")

if __name__ == "__main__":
    main()
