#!/usr/bin/env python3
import os
import re
import base64
import tempfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
import hashlib
import improved_phb_details as phb_details
import traceback

# Try to import OCR libraries, but continue if not available
try:
    import pytesseract
    from PIL import Image
    import io
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

# Define more comprehensive patterns for extracting medical information
DOCTOR_PATTERN = r'(?:Dr\.?|Doctor|Prof\.?|Professor|Mr\.?|Mrs\.?|Ms\.?|Miss|Consultant|Specialist)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
NURSE_PATTERN = r'(?:Nurse|Sister|Matron|RN|Staff Nurse)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
THERAPIST_PATTERN = r'(?:Therapist|Physiotherapist|Physio|OT|Occupational Therapist|Speech|SALT|SLT)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
HOSPITAL_PATTERN = r'(?:Hospital|Medical Center|Clinic|Centre|Center|NHS Trust|Foundation Trust|Children\'s|Paediatric|Pediatric)(?:[:\s]+)([A-Za-z\s\-\']+)'
DEPARTMENT_PATTERN = r'(?:Department|Dept|Ward|Unit|Clinic|Service|Team)(?:[:\s]+)([A-Za-z\s\-\']+)'
APPOINTMENT_PATTERN = r'(?:Appointment|Visit|Consultation|Follow-up|Review|Assessment|Evaluation|Examination|Check-up|Checkup)(?:\s+with|\s+at|\s+on|\s+for)?(?:[:\s]+)([^\.]+)'
DATE_PATTERN = r'(?:Date|On|Dated)(?:[:\s]+)(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4})'
MEDICATION_PATTERN = r'(?:Medication|Prescribed|Taking|Drug|Therapy|Treatment|Dose|Dosage)(?:[:\s]+)([^\.]+)'
PROCEDURE_PATTERN = r'(?:Procedure|Surgery|Operation|Intervention|Treatment)(?:[:\s]+)([^\.]+)'
DIAGNOSIS_PATTERN = r'(?:Diagnosis|Diagnosed with|Assessment|Condition|Problem|Issue|Concern)(?:[:\s]+)([^\.]+)'
SYMPTOM_PATTERN = r'(?:Symptom|Presenting with|Complaining of|Reporting|Experiencing)(?:[:\s]+)([^\.]+)'
RESULT_PATTERN = r'(?:Result|Finding|Outcome|Report|Test|Investigation|Scan|X-ray|MRI|CT|Ultrasound)(?:[:\s]+)([^\.]+)'
PLAN_PATTERN = r'(?:Plan|Recommendation|Advised|Suggested|Proposed|Next steps|Follow-up|Review)(?:[:\s]+)([^\.]+)'

def determine_specialty(text, title=""):
    """
    Determine medical specialty based on comprehensive analysis of text content.
    Returns the specialty and a confidence score.
    """
    if not text:
        return {"specialty": "Unknown", "confidence": 0}
    
    combined_text = (text + " " + title).lower()
    
    # Check for explicit mentions of departments or specialties
    department_matches = re.findall(DEPARTMENT_PATTERN, combined_text)
    for dept in department_matches:
        dept = dept.lower()
        for specialty, keywords in phb_details.PHB_CATEGORIES.items():
            for keyword in keywords["keywords"]:
                if keyword in dept:
                    return {"specialty": specialty, "confidence": 90}
    
    # Count keyword matches for each specialty
    specialty_scores = {}
    for specialty, info in phb_details.PHB_CATEGORIES.items():
        match_count = 0
        for keyword in info["keywords"]:
            if keyword in combined_text:
                match_count += 1
        
        if match_count > 0:
            # Calculate confidence score based on matches and keyword density
            confidence = min(100, (match_count / len(info["keywords"])) * 100 * 2)
            specialty_scores[specialty] = confidence
    
    if specialty_scores:
        # Return the specialty with the highest confidence
        best_specialty = max(specialty_scores.items(), key=lambda x: x[1])
        return {"specialty": best_specialty[0], "confidence": round(best_specialty[1], 1)}
    
    return {"specialty": "Unknown", "confidence": 0}

def extract_personnel(text):
    """
    Extract and categorize medical personnel from text.
    Returns a list of personnel with their type, name, and specialty.
    """
    doctors = re.findall(DOCTOR_PATTERN, text)
    nurses = re.findall(NURSE_PATTERN, text)
    therapists = re.findall(THERAPIST_PATTERN, text)
    
    personnel = []
    
    # Process doctors
    for name in doctors:
        category = phb_details.categorize_personnel(name, "doctor")
        personnel.append({
            "name": name,
            "type": category["type"],
            "specialty": category["specialty"]
        })
    
    # Process nurses
    for name in nurses:
        category = phb_details.categorize_personnel(name, "nurse")
        personnel.append({
            "name": name,
            "type": category["type"],
            "specialty": category["specialty"]
        })
    
    # Process therapists
    for name in therapists:
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
    Returns a list of facilities with their type and specialty.
    """
    hospitals = re.findall(HOSPITAL_PATTERN, text)
    departments = re.findall(DEPARTMENT_PATTERN, text)
    
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

def extract_appointments(text):
    """Extract appointment details from text"""
    appointments = re.findall(APPOINTMENT_PATTERN, text)
    return appointments if appointments else []

def extract_dates(text):
    """Extract dates from text"""
    dates = re.findall(DATE_PATTERN, text)
    return dates if dates else []

def extract_medications(text):
    """Extract medication information from text"""
    medications = re.findall(MEDICATION_PATTERN, text)
    return medications if medications else []

def extract_procedures(text):
    """Extract procedure information from text"""
    procedures = re.findall(PROCEDURE_PATTERN, text)
    return procedures if procedures else []

def extract_diagnoses(text):
    """Extract diagnosis information from text"""
    diagnoses = re.findall(DIAGNOSIS_PATTERN, text)
    return diagnoses if diagnoses else []

def extract_symptoms(text):
    """Extract symptom information from text"""
    symptoms = re.findall(SYMPTOM_PATTERN, text)
    return symptoms if symptoms else []

def extract_results(text):
    """Extract test result information from text"""
    results = re.findall(RESULT_PATTERN, text)
    return results if results else []

def extract_plans(text):
    """Extract treatment plan information from text"""
    plans = re.findall(PLAN_PATTERN, text)
    return plans if plans else []

def extract_significant_events(text):
    """
    Extract significant medical events from text using comprehensive pattern matching.
    Returns a list of events with their type and content.
    """
    if not text:
        return []
    
    events = []
    
    # Extract events by type
    event_types = {
        "Appointment": extract_appointments(text),
        "Medication": extract_medications(text),
        "Procedure": extract_procedures(text),
        "Diagnosis": extract_diagnoses(text),
        "Symptom": extract_symptoms(text),
        "Result": extract_results(text),
        "Plan": extract_plans(text)
    }
    
    # Add extracted events to the list
    for event_type, items in event_types.items():
        for item in items:
            events.append({
                "type": event_type,
                "content": item
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

def perform_ocr_on_image(image_data):
    """Perform OCR on an image to extract text"""
    if not HAS_OCR:
        return ""
    
    try:
        # Convert base64 image data to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Perform OCR
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error performing OCR: {e}")
        return ""

def perform_ocr_on_pdf(pdf_data):
    """Perform OCR on a PDF to extract text"""
    if not HAS_OCR or not HAS_PDF2IMAGE:
        return ""
    
    try:
        # Save PDF data to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(pdf_data)
            temp_pdf_path = temp_pdf.name
        
        # Convert PDF to images
        images = convert_from_path(temp_pdf_path)
        
        # Perform OCR on each image
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image) + "\n\n"
        
        # Clean up temporary file
        os.unlink(temp_pdf_path)
        
        return text
    except Exception as e:
        print(f"Error performing OCR on PDF: {e}")
        return ""

def extract_text_from_resource(resource, mime_type):
    """Extract text from a resource using OCR if necessary"""
    if not resource:
        return ""
    
    try:
        # Get the base64-encoded data
        data_elem = resource.find('data')
        if data_elem is None or data_elem.text is None:
            return ""
        
        # Decode the base64 data
        data = base64.b64decode(data_elem.text)
        
        # Process based on mime type
        if 'image' in mime_type and HAS_OCR:
            return perform_ocr_on_image(data)
        elif 'pdf' in mime_type and HAS_OCR and HAS_PDF2IMAGE:
            return perform_ocr_on_pdf(data)
        else:
            return ""
    except Exception as e:
        print(f"Error extracting text from resource: {e}")
        return ""

def generate_note_id(note):
    """Generate a unique ID for a note based on its content"""
    try:
        # Get title and created date
        title = note.find('title').text if note.find('title') is not None else "Untitled"
        created = note.find('created').text if note.find('created') is not None else ""
        
        # Create a unique string
        unique_string = f"{title}_{created}"
        
        # Generate a hash
        note_id = hashlib.md5(unique_string.encode()).hexdigest()
        
        return note_id
    except Exception as e:
        print(f"Error generating note ID: {e}")
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()

def parse_enex_file(file_path):
    """
    Parse an ENEX file and extract notes with their metadata.
    Returns a list of notes with comprehensive medical information.
    """
    print(f"Parsing {file_path}...")
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        notes_data = []
        
        for note in root.findall('.//note'):
            try:
                title = note.find('title').text if note.find('title') is not None else "Untitled"
                
                # Skip if not related to Gwendolyn
                if not any(keyword.lower() in title.lower() for keyword in ['gwen', 'gwendolyn']):
                    # Check tags for Gwen-related content
                    tags = [tag.text for tag in note.findall('tag') if tag.text is not None]
                    if not any(tag.lower() in ['gwen', 'gwendolyn'] for tag in tags):
                        continue
                
                # Generate a unique ID for this note
                note_id = generate_note_id(note)
                
                # Get source file name
                source_file = os.path.basename(file_path)
                
                # Get created date
                created_str = note.find('created').text if note.find('created') is not None else None
                if created_str:
                    # Format: 20170816T134740Z
                    created_date = datetime.strptime(created_str, '%Y%m%dT%H%M%SZ')
                else:
                    created_date = None
                
                # Get updated date
                updated_str = note.find('updated').text if note.find('updated') is not None else None
                if updated_str:
                    # Format: 20170816T134740Z
                    updated_date = datetime.strptime(updated_str, '%Y%m%dT%H%M%SZ')
                else:
                    updated_date = None
                
                # Get tags
                tags = [tag.text for tag in note.findall('tag') if tag.text is not None]
                
                # Initialize text content
                text_content = ""
                
                # Get content
                content_elem = note.find('content')
                if content_elem is not None and content_elem.text is not None:
                    # Extract the CDATA content
                    cdata_content = content_elem.text
                    
                    # Parse the XML content inside CDATA
                    try:
                        soup = BeautifulSoup(cdata_content, 'xml')
                        # Extract text content
                        text_content = soup.get_text(strip=True)
                        
                        # Check for media elements that might need OCR
                        media_elements = soup.find_all('en-media')
                        for media in media_elements:
                            if media.get('hash'):
                                # Find the corresponding resource
                                media_hash = media.get('hash')
                                media_type = media.get('type', '')
                                
                                # Find the resource with this hash
                                for resource in note.findall('.//resource'):
                                    resource_data = resource.find('data')
                                    if resource_data is not None and resource_data.text is not None:
                                        # Check if this is the right resource
                                        resource_hash_elem = resource.find('.//resource-attributes/source-url')
                                        if resource_hash_elem is not None and media_hash in resource_hash_elem.text:
                                            # Extract text using OCR
                                            ocr_text = extract_text_from_resource(resource, media_type)
                                            if ocr_text:
                                                text_content += "\n\n" + ocr_text
                    except Exception as e:
                        print(f"Error parsing content XML: {e}")
                        text_content = "Error extracting content"
                
                # Process resources directly if not already processed
                if not text_content or len(text_content) < 100:  # If text content is empty or very short
                    for resource in note.findall('.//resource'):
                        resource_attributes = resource.find('resource-attributes')
                        if resource_attributes is not None:
                            mime = resource.find('mime')
                            if mime is not None and mime.text is not None:
                                mime_type = mime.text
                                ocr_text = extract_text_from_resource(resource, mime_type)
                                if ocr_text:
                                    text_content += "\n\n" + ocr_text
                
                # Determine medical specialty
                specialty_info = determine_specialty(text_content, title)
                specialty = specialty_info["specialty"]
                specialty_confidence = specialty_info["confidence"]
                
                # Extract personnel
                personnel = extract_personnel(title + " " + text_content)
                
                # Extract facilities
                facilities = extract_facilities(title + " " + text_content)
                
                # Extract appointments
                appointments = extract_appointments(title + " " + text_content)
                
                # Extract dates
                dates = extract_dates(title + " " + text_content)
                
                # Extract medications
                medications = extract_medications(title + " " + text_content)
                
                # Extract procedures
                procedures = extract_procedures(title + " " + text_content)
                
                # Extract diagnoses
                diagnoses = extract_diagnoses(title + " " + text_content)
                
                # Extract symptoms
                symptoms = extract_symptoms(title + " " + text_content)
                
                # Extract results
                results = extract_results(title + " " + text_content)
                
                # Extract plans
                plans = extract_plans(title + " " + text_content)
                
                # Extract significant events
                events = extract_significant_events(text_content)
                
                # Link to PHB categories
                phb_categories = []
                for event in events:
                    categories = phb_details.get_phb_category_for_event(event["content"])
                    if categories:
                        for category in categories:
                            # Check if this category is already in the list
                            if not any(cat["category"] == category["category"] for cat in phb_categories):
                                phb_categories.append(category)
                
                # Link to PHB supports
                phb_supports = []
                for event in events:
                    supports = phb_details.get_phb_support_for_event(event["content"])
                    if supports:
                        for support in supports:
                            # Check if this support is already in the list
                            if not any(sup["support"] == support["support"] for sup in phb_supports):
                                phb_supports.append(support)
                
                notes_data.append({
                    'id': note_id,
                    'source_file': source_file,
                    'title': title,
                    'date': created_date,
                    'updated': updated_date,
                    'tags': tags,
                    'specialty': specialty,
                    'specialty_confidence': specialty_confidence,
                    'personnel': personnel,
                    'facilities': facilities,
                    'appointments': appointments,
                    'dates': dates,
                    'medications': medications,
                    'procedures': procedures,
                    'diagnoses': diagnoses,
                    'symptoms': symptoms,
                    'results': results,
                    'plans': plans,
                    'events': events,
                    'phb_categories': phb_categories,
                    'phb_supports': phb_supports,
                    'content': text_content[:500] + "..." if len(text_content) > 500 else text_content,
                    'full_content': text_content
                })
                
            except Exception as e:
                print(f"Error processing note: {e}")
                traceback.print_exc()
        
        return notes_data
    
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        traceback.print_exc()
        return []

def save_data(data, filename):
    """Save data to a JSON file with proper date handling"""
    # Convert datetime objects to strings
    serializable_data = []
    for item in data:
        serializable_item = {}
        for key, value in item.items():
            if isinstance(value, datetime):
                serializable_item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                serializable_item[key] = value
        serializable_data.append(serializable_item)
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(serializable_data, f, indent=2)
    
    print(f"Data saved to {filename}")

def main():
    # Directory containing ENEX files
    enex_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get all ENEX files
    enex_files = [os.path.join(enex_dir, f) for f in os.listdir(enex_dir) if f.endswith('.enex')]
    
    all_notes = []
    
    # Parse each ENEX file
    for enex_file in enex_files:
        notes = parse_enex_file(enex_file)
        all_notes.extend(notes)
    
    print(f"Total notes extracted: {len(all_notes)}")
    
    # Filter out notes without dates
    dated_notes = [note for note in all_notes if note['date'] is not None]
    print(f"Notes with valid dates: {len(dated_notes)}")
    
    if dated_notes:
        # Save the comprehensive data
        save_data(dated_notes, 'gwendolyn_medical_data_comprehensive.json')
    else:
        print("No valid notes with dates found.")

if __name__ == "__main__":
    main()
