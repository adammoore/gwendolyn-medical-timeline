"""
enex_parser.py

This module provides functions to parse an Evernote export (.enex) file
and extract timeline events from the notes, with PHB integration.
"""

import xml.etree.ElementTree as ET
import re
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib
import os
import improved_phb_details as phb_details
import patient_info
import evernote_utils
import attachment_processor

# Directory to save attachments
ATTACHMENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attachments")

def parse_enex(file_path):
    """
    Parse the Evernote .enex file to extract notes.

    Parameters:
        file_path (str): Path to the .enex file.

    Returns:
        list: A list of dictionaries with note details.
    """
    try:
        # Parse the file with GUIDs
        notes_with_guids = evernote_utils.parse_enex_file_with_guids(file_path)
        notes = []
        
        for xml_note, guid in notes_with_guids:
            # Extract basic note information
            title_elem = xml_note.find('title')
            content_elem = xml_note.find('content')
            created_elem = xml_note.find('created')
            updated_elem = xml_note.find('updated')
            
            title = title_elem.text if title_elem is not None else "No Title"
            content = content_elem.text if content_elem is not None else ""
            created = created_elem.text if created_elem is not None else ""
            updated = updated_elem.text if updated_elem is not None else ""
            
            # Extract tags
            tags = [tag.text for tag in xml_note.findall('tag') if tag.text is not None]
            
            # Skip if not related to Gwendolyn
            if not any(keyword.lower() in title.lower() for keyword in ['gwen', 'gwendolyn']):
                if not any(tag.lower() in ['gwen', 'gwendolyn'] for tag in tags):
                    continue
            
            # Generate a unique ID for this note
            note_id = generate_note_id(title, created)
            
            # Get source file name
            source_file = os.path.basename(file_path)
            
            # Parse the content to extract text
            text_content = extract_text_from_content(content)
            
            # Extract note attributes
            note_attributes = xml_note.find('note-attributes')
            source_url = ""
            author = ""
            source_application = ""
            
            if note_attributes is not None:
                source_url_elem = note_attributes.find('source-url')
                if source_url_elem is not None and source_url_elem.text:
                    source_url = source_url_elem.text
                
                author_elem = note_attributes.find('author')
                if author_elem is not None and author_elem.text:
                    author = author_elem.text
                
                source_app_elem = note_attributes.find('source-application')
                if source_app_elem is not None and source_app_elem.text:
                    source_application = source_app_elem.text
            
            # Generate Evernote links
            evernote_links = evernote_utils.generate_evernote_link(note_id, title, guid)
            
            # Extract and save attachments
            attachments = []
            if os.path.exists(ATTACHMENTS_DIR) or os.makedirs(ATTACHMENTS_DIR, exist_ok=True):
                note_attachments_dir = os.path.join(ATTACHMENTS_DIR, note_id)
                attachments = evernote_utils.extract_and_save_attachments(xml_note, note_attachments_dir)
            
            notes.append({
                "id": note_id,
                "guid": guid,
                "source_file": source_file,
                "title": title,
                "content": content,
                "text_content": text_content,
                "created": created,
                "updated": updated,
                "tags": tags,
                "source_url": source_url,
                "author": author,
                "source_application": source_application,
                "evernote_links": evernote_links,
                "attachments": attachments
            })
        
        return notes
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def extract_text_from_content(content):
    """
    Extract plain text from ENML content.
    
    Parameters:
        content (str): ENML content from Evernote.
        
    Returns:
        str: Plain text content.
    """
    if not content:
        return ""
    
    try:
        # Parse the XML content
        soup = BeautifulSoup(content, 'xml')
        # Extract text content
        text = soup.get_text(strip=True)
        return text
    except Exception as e:
        print(f"Error extracting text from content: {e}")
        return ""

def generate_note_id(title, created):
    """
    Generate a unique ID for a note based on its title and creation date.
    
    Parameters:
        title (str): Note title.
        created (str): Note creation timestamp.
        
    Returns:
        str: Unique ID.
    """
    unique_string = f"{title}_{created}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def extract_events(notes):
    """
    Extract timeline events from a list of notes with PHB integration.

    Parameters:
        notes (list): List of note dictionaries (from parse_enex).

    Returns:
        list: A list of event dictionaries with PHB details.
    """
    events = []
    
    for note in notes:
        # Convert Evernote's created format (e.g., "20200115T123456Z") to datetime
        if note["created"]:
            try:
                created_date = datetime.strptime(note["created"], '%Y%m%dT%H%M%SZ')
                event_date = created_date.strftime('%Y-%m-%d')
            except ValueError:
                continue  # Skip this note if date format is invalid
        else:
            continue  # Skip this note if no date is found
        
        # Calculate Gwen's age at this event
        age = patient_info.get_age_at_date(event_date)
        age_str = patient_info.format_age(age)
        
        # Extract medical information
        medical_info = extract_medical_info(note["title"], note["text_content"])
        
        # Link to PHB categories
        phb_categories = []
        for event in medical_info["events"]:
            categories = phb_details.get_phb_category_for_event(event["content"])
            if categories:
                for category in categories:
                    # Check if this category is already in the list
                    if not any(cat["category"] == category["category"] for cat in phb_categories):
                        phb_categories.append(category)
        
        # Link to PHB supports
        phb_supports = []
        for event in medical_info["events"]:
            supports = phb_details.get_phb_support_for_event(event["content"])
            if supports:
                for support in supports:
                    # Check if this support is already in the list
                    if not any(sup["support"] == support["support"] for sup in phb_supports):
                        phb_supports.append(support)
        
        events.append({
            "id": note["id"],
            "guid": note["guid"],
            "source_file": note["source_file"],
            "date": event_date,
            "age": age_str,
            "title": note["title"],
            "content": note["text_content"],
            "specialty": medical_info["specialty"]["specialty"],
            "specialty_confidence": medical_info["specialty"]["confidence"],
            "personnel": medical_info["personnel"],
            "facilities": medical_info["facilities"],
            "events": medical_info["events"],
            "phb_categories": phb_categories,
            "phb_supports": phb_supports,
            "tags": note["tags"],
            "source_url": note["source_url"],
            "author": note["author"],
            "source_application": note["source_application"],
            "evernote_links": note["evernote_links"],
            "attachments": note["attachments"]
        })
    
    return events

def extract_medical_info(title, content):
    """
    Extract medical information from note title and content.
    
    Parameters:
        title (str): Note title.
        content (str): Note content.
        
    Returns:
        dict: Dictionary with medical information.
    """
    combined_text = title + " " + content
    
    # Determine specialty
    specialty = phb_details.determine_specialty(combined_text, title)
    
    # Extract personnel
    personnel = extract_personnel(combined_text)
    
    # Extract facilities
    facilities = extract_facilities(combined_text)
    
    # Extract significant events
    events = extract_significant_events(content)
    
    # Extract patient identifiers
    identifiers = extract_patient_identifiers(combined_text)
    
    return {
        "specialty": specialty,
        "personnel": personnel,
        "facilities": facilities,
        "events": events,
        "identifiers": identifiers
    }

def extract_personnel(text):
    """
    Extract and categorize medical personnel from text.
    
    Parameters:
        text (str): Text to extract from.
        
    Returns:
        list: List of personnel dictionaries.
    """
    # Define patterns for different types of personnel
    doctor_pattern = r'(?:Dr\.?|Doctor|Prof\.?|Professor|Mr\.?|Mrs\.?|Ms\.?|Miss|Consultant|Specialist)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    nurse_pattern = r'(?:Nurse|Sister|Matron|RN|Staff Nurse)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    therapist_pattern = r'(?:Therapist|Physiotherapist|Physio|OT|Occupational Therapist|Speech|SALT|SLT)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    
    doctors = re.findall(doctor_pattern, text)
    nurses = re.findall(nurse_pattern, text)
    therapists = re.findall(therapist_pattern, text)
    
    personnel = []
    
    # Process doctors
    for name in doctors:
        # Skip if this is Adam Vials Moore (the father, not a doctor)
        if patient_info.is_family_member(name):
            continue
            
        category = phb_details.categorize_personnel(name, "doctor")
        personnel.append({
            "name": name,
            "type": category["type"],
            "specialty": category["specialty"]
        })
    
    # Process nurses
    for name in nurses:
        if patient_info.is_family_member(name):
            continue
            
        category = phb_details.categorize_personnel(name, "nurse")
        personnel.append({
            "name": name,
            "type": category["type"],
            "specialty": category["specialty"]
        })
    
    # Process therapists
    for name in therapists:
        if patient_info.is_family_member(name):
            continue
            
        category = phb_details.categorize_personnel(name, "therapist")
        personnel.append({
            "name": name,
            "type": category["type"],
            "specialty": category["specialty"]
        })
    
    return personnel if personnel else [{"name": "Unknown", "type": "Unknown", "specialty": "Unknown"}]

def extract_facilities(text):
    """
    Extract and categorize medical facilities from text.
    
    Parameters:
        text (str): Text to extract from.
        
    Returns:
        list: List of facility dictionaries.
    """
    # Define patterns for different types of facilities
    hospital_pattern = r'(?:Hospital|Medical Center|Clinic|Centre|Center|NHS Trust|Foundation Trust|Children\'s|Paediatric|Pediatric)(?:[:\s]+)([A-Za-z\s\-\']+)'
    department_pattern = r'(?:Department|Dept|Ward|Unit|Clinic|Service|Team)(?:[:\s]+)([A-Za-z\s\-\']+)'
    
    hospitals = re.findall(hospital_pattern, text)
    departments = re.findall(department_pattern, text)
    
    facilities = []
    
    # Process hospitals
    for name in hospitals:
        category = phb_details.categorize_facility(name)
        facilities.append({
            "name": name,
            "type": category["type"],
            "specialty": category["specialty"]
        })
    
    # Process departments
    for name in departments:
        category = phb_details.categorize_facility(name)
        facilities.append({
            "name": name,
            "type": "Department",
            "specialty": category["specialty"]
        })
    
    return facilities

def extract_significant_events(text):
    """
    Extract significant medical events from text.
    
    Parameters:
        text (str): Text to extract from.
        
    Returns:
        list: List of event dictionaries.
    """
    if not text:
        return []
    
    events = []
    
    # Define patterns for different types of events
    patterns = {
        "Appointment": r'(?:Appointment|Visit|Consultation|Follow-up|Review|Assessment|Evaluation|Examination|Check-up|Checkup)(?:\s+with|\s+at|\s+on|\s+for)?(?:[:\s]+)([^\.]+)',
        "Medication": r'(?:Medication|Prescribed|Taking|Drug|Therapy|Treatment|Dose|Dosage)(?:[:\s]+)([^\.]+)',
        "Procedure": r'(?:Procedure|Surgery|Operation|Intervention|Treatment)(?:[:\s]+)([^\.]+)',
        "Diagnosis": r'(?:Diagnosis|Diagnosed with|Assessment|Condition|Problem|Issue|Concern)(?:[:\s]+)([^\.]+)',
        "Symptom": r'(?:Symptom|Presenting with|Complaining of|Reporting|Experiencing)(?:[:\s]+)([^\.]+)',
        "Result": r'(?:Result|Finding|Outcome|Report|Test|Investigation|Scan|X-ray|MRI|CT|Ultrasound)(?:[:\s]+)([^\.]+)',
        "Plan": r'(?:Plan|Recommendation|Advised|Suggested|Proposed|Next steps|Follow-up|Review)(?:[:\s]+)([^\.]+)'
    }
    
    # Extract events by type
    for event_type, pattern in patterns.items():
        matches = re.findall(pattern, text)
        for match in matches:
            events.append({
                "type": event_type,
                "content": match
            })
    
    # If no structured events were found, extract sentences with medical keywords
    if not events:
        # Keywords that might indicate significant events
        event_keywords = [
            'diagnosis', 'diagnosed', 'surgery', 'operation', 'procedure', 
            'admitted', 'admission', 'discharged', 'discharge', 'emergency',
            'treatment', 'therapy', 'medication', 'prescribed', 'test results',
            'scan', 'mri', 'ct', 'x-ray', 'ultrasound', 'blood test',
            'appointment', 'consultation', 'follow-up', 'review', 'referral',
            'assessment', 'evaluation', 'examination', 'check-up', 'checkup',
            'symptoms', 'pain', 'discomfort', 'difficulty', 'problem',
            'improvement', 'deterioration', 'change', 'progress', 'regress',
            'complication', 'side effect', 'reaction', 'response', 'outcome'
        ]
        
        # Extract sentences containing event keywords
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            for keyword in event_keywords:
                if keyword in sentence.lower():
                    events.append({
                        "type": "General",
                        "content": sentence
                    })
                    break
    
    return events if events else [{"type": "Unknown", "content": "No specific events extracted"}]

def extract_patient_identifiers(text):
    """
    Extract patient identifiers like NHS number, hospital numbers, etc.
    
    Parameters:
        text (str): Text to extract from.
        
    Returns:
        dict: Dictionary with patient identifiers.
    """
    identifiers = {}
    
    # NHS Number pattern (10 digits, often with spaces)
    nhs_pattern = r'(?:NHS|National Health Service|NHS Number|NHS No|NHS #)(?:[:\s]+)([0-9\s]{10,12})'
    nhs_matches = re.findall(nhs_pattern, text)
    if nhs_matches:
        # Clean up the number (remove spaces)
        nhs_number = re.sub(r'\s', '', nhs_matches[0])
        identifiers["nhs_number"] = nhs_number
    
    # Hospital Number pattern (varies by hospital, but often alphanumeric)
    hospital_pattern = r'(?:Hospital Number|Hospital No|Hospital #|Patient Number|Patient ID|MRN|Medical Record Number)(?:[:\s]+)([A-Z0-9\s]{5,12})'
    hospital_matches = re.findall(hospital_pattern, text)
    if hospital_matches:
        hospital_number = hospital_matches[0].strip()
        identifiers["hospital_number"] = hospital_number
    
    # Alder Hey specific pattern
    alder_hey_pattern = r'(?:Alder Hey|Alder Hey Number|Alder Hey ID)(?:[:\s]+)([A-Z0-9\s]{5,12})'
    alder_hey_matches = re.findall(alder_hey_pattern, text)
    if alder_hey_matches:
        alder_hey_number = alder_hey_matches[0].strip()
        identifiers["alder_hey_number"] = alder_hey_number
    
    return identifiers

def get_all_events_from_directory(directory):
    """
    Parse all ENEX files in a directory and extract events.
    
    Parameters:
        directory (str): Directory containing ENEX files.
        
    Returns:
        list: List of all events from all files.
    """
    all_events = []
    
    # Get all ENEX files in the directory
    enex_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.enex')]
    
    for file_path in enex_files:
        print(f"Parsing {file_path}...")
        notes = parse_enex(file_path)
        events = extract_events(notes)
        all_events.extend(events)
    
    # Process all attachments
    print("Processing attachments...")
    all_events = attachment_processor.process_all_attachments(all_events)
    
    # Create vector store
    print("Creating vector store...")
    attachment_processor.create_vector_store(all_events)
    
    # Update patient info with identifiers from events
    updated_patient_info = attachment_processor.update_patient_info_from_events(all_events)
    patient_info.update_patient_info(updated_patient_info)
    
    # Sort events by date
    all_events.sort(key=lambda x: x["date"])
    
    return all_events

def extract_diagnostic_journey(events):
    """
    Extract the diagnostic journey from events.
    
    Parameters:
        events (list): List of events.
        
    Returns:
        list: List of diagnostic events.
    """
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
