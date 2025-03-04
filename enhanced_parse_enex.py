#!/usr/bin/env python3
import os
import re
import base64
import tempfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import io
import phb_details

# Define medical specialties and keywords for classification
SPECIALTIES = {
    'Neurology': ['neuro', 'brain', 'seizure', 'epilepsy', 'neurologist', 'eeg', 'mri brain'],
    'Cardiology': ['heart', 'cardiac', 'cardio', 'cardiologist', 'ecg', 'echo'],
    'Pulmonology': ['lung', 'pulmonary', 'respiratory', 'breathing', 'pulmonologist', 'apnea', 'apnoea', 'sleep study', 'ventilation', 'oxygen'],
    'Gastroenterology': ['stomach', 'intestine', 'gastro', 'gi', 'gastroenterologist', 'reflux', 'gerd', 'feeding', 'tube', 'peg'],
    'Orthopedics': ['bone', 'joint', 'fracture', 'ortho', 'orthopedist', 'orthopedic', 'orthopaedic', 'knee', 'leg', 'hip', 'osteotomy', 'patella'],
    'Endocrinology': ['hormone', 'thyroid', 'diabetes', 'endocrine', 'endocrinologist', 'growth', 'obesity'],
    'Ophthalmology': ['eye', 'vision', 'ophthalmologist', 'glasses', 'sight'],
    'ENT': ['ear', 'nose', 'throat', 'ent', 'hearing', 'audiology'],
    'Dermatology': ['skin', 'rash', 'dermatologist', 'eczema', 'allergy'],
    'Hematology': ['blood', 'anemia', 'hematologist'],
    'Oncology': ['cancer', 'tumor', 'oncologist'],
    'Nephrology': ['kidney', 'renal', 'nephrologist', 'urinary', 'urology', 'bladder'],
    'Urology': ['bladder', 'urinary', 'urologist', 'catheter', 'continence'],
    'Rheumatology': ['arthritis', 'rheumatoid', 'rheumatologist', 'joint pain'],
    'Immunology': ['immune', 'allergy', 'immunologist', 'allergic'],
    'Psychiatry': ['mental', 'psychiatric', 'psychiatrist', 'behavior', 'behaviour', 'asd', 'autism', 'pda'],
    'Pediatrics': ['pediatric', 'pediatrician', 'child', 'children', 'paediatric', 'paediatrician'],
    'General': ['doctor', 'physician', 'gp', 'general practitioner', 'check-up', 'checkup', 'appointment'],
    'Therapy': ['therapy', 'therapist', 'physiotherapy', 'physio', 'occupational therapy', 'ot', 'speech', 'language'],
    'Surgery': ['surgery', 'surgical', 'operation', 'procedure', 'pre-op', 'post-op']
}

# Regular expressions for extracting medical information
DOCTOR_PATTERN = r'(?:Dr\.?|Doctor|Prof\.?|Professor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
NURSE_PATTERN = r'(?:Nurse|Sister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
HOSPITAL_PATTERN = r'(?:Hospital|Medical Center|Clinic|Centre|Center|NHS Trust):\s*([A-Za-z\s]+)'
APPOINTMENT_PATTERN = r'(?:Appointment|Visit|Consultation|Follow-up|Review)(?:\s+with|\s+at|\s+on|\s+for)?\s*([^\.]+)'
DATE_PATTERN = r'(?:Date|On):\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4})'
MEDICATION_PATTERN = r'(?:Medication|Prescribed|Taking):\s*([^\.]+)'
PROCEDURE_PATTERN = r'(?:Procedure|Surgery|Operation):\s*([^\.]+)'
DIAGNOSIS_PATTERN = r'(?:Diagnosis|Diagnosed with|Assessment):\s*([^\.]+)'

def determine_specialty(text):
    """Determine medical specialty based on keywords in text"""
    text = text.lower()
    
    # Check for each specialty's keywords
    specialty_matches = {}
    for specialty, keywords in SPECIALTIES.items():
        for keyword in keywords:
            if keyword in text:
                specialty_matches[specialty] = specialty_matches.get(specialty, 0) + 1
    
    if specialty_matches:
        # Return the specialty with the most keyword matches
        return max(specialty_matches.items(), key=lambda x: x[1])[0]
    
    return "Unknown"

def extract_personnel(text):
    """Extract medical personnel names from text"""
    doctors = re.findall(DOCTOR_PATTERN, text)
    nurses = re.findall(NURSE_PATTERN, text)
    
    personnel = doctors + nurses
    return personnel if personnel else ["Unknown"]

def extract_hospitals(text):
    """Extract hospital or clinic names from text"""
    hospitals = re.findall(HOSPITAL_PATTERN, text)
    return hospitals if hospitals else []

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

def extract_significant_events(text):
    """Extract significant medical events from text"""
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
    significant_events = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        for keyword in event_keywords:
            if keyword in sentence.lower():
                significant_events.append(sentence)
                break
    
    return significant_events if significant_events else ["No specific events extracted"]

def perform_ocr_on_image(image_data):
    """Perform OCR on an image to extract text"""
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
        if 'image' in mime_type:
            return perform_ocr_on_image(data)
        elif 'pdf' in mime_type:
            return perform_ocr_on_pdf(data)
        else:
            return ""
    except Exception as e:
        print(f"Error extracting text from resource: {e}")
        return ""

def parse_enex_file(file_path):
    """Parse an ENEX file and extract notes with their metadata"""
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
                
                # Get created date
                created_str = note.find('created').text if note.find('created') is not None else None
                if created_str:
                    # Format: 20170816T134740Z
                    created_date = datetime.strptime(created_str, '%Y%m%dT%H%M%SZ')
                else:
                    created_date = None
                
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
                specialty = determine_specialty(title + " " + text_content)
                
                # Extract personnel
                personnel = extract_personnel(title + " " + text_content)
                
                # Extract hospitals
                hospitals = extract_hospitals(title + " " + text_content)
                
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
                
                # Extract significant events
                events = extract_significant_events(text_content)
                
                # Link to PHB categories and supports
                phb_categories = []
                for event in events:
                    categories = phb_details.get_phb_category_for_event(event)
                    if categories:
                        phb_categories.extend(categories)
                
                phb_supports = []
                for event in events:
                    supports = phb_details.get_phb_support_for_event(event)
                    if supports:
                        phb_supports.extend(supports)
                
                notes_data.append({
                    'title': title,
                    'date': created_date,
                    'specialty': specialty,
                    'personnel': personnel,
                    'hospitals': hospitals,
                    'appointments': appointments,
                    'dates': dates,
                    'medications': medications,
                    'procedures': procedures,
                    'diagnoses': diagnoses,
                    'events': events,
                    'phb_categories': phb_categories,
                    'phb_supports': phb_supports,
                    'content': text_content[:500] + "..." if len(text_content) > 500 else text_content
                })
                
            except Exception as e:
                print(f"Error processing note: {e}")
        
        return notes_data
    
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return []

def create_timeline(data):
    """Create an interactive timeline visualization using Plotly"""
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Sort by date
    df = df.sort_values('date')
    
    # Create a color map for specialties
    specialties = df['specialty'].unique()
    color_map = {specialty: f'rgb({hash(specialty) % 256}, {(hash(specialty) // 256) % 256}, {(hash(specialty) // 65536) % 256})' 
                for specialty in specialties}
    
    # Create figure
    fig = go.Figure()
    
    # Add events to the timeline
    for i, row in df.iterrows():
        hover_text = f"<b>{row['title']}</b><br>"
        hover_text += f"Date: {row['date'].strftime('%Y-%m-%d')}<br>"
        hover_text += f"Specialty: {row['specialty']}<br>"
        hover_text += f"Personnel: {', '.join(row['personnel'])}<br>"
        
        if row['hospitals']:
            hover_text += f"Hospitals: {', '.join(row['hospitals'])}<br>"
        
        if row['appointments']:
            hover_text += f"Appointments: {', '.join(row['appointments'])}<br>"
        
        if row['medications']:
            hover_text += f"Medications: {', '.join(row['medications'])}<br>"
        
        if row['procedures']:
            hover_text += f"Procedures: {', '.join(row['procedures'])}<br>"
        
        if row['diagnoses']:
            hover_text += f"Diagnoses: {', '.join(row['diagnoses'])}<br>"
        
        hover_text += f"Events: {', '.join(row['events'][:2])}<br>"
        
        # Add PHB categories if available
        if row['phb_categories']:
            phb_cats = [f"{cat['category']} ({cat['severity']})" for cat in row['phb_categories']]
            hover_text += f"PHB Categories: {', '.join(phb_cats)}<br>"
        
        # Add PHB supports if available
        if row['phb_supports']:
            phb_sups = [sup['support'] for sup in row['phb_supports']]
            hover_text += f"PHB Supports: {', '.join(phb_sups)}<br>"
        
        fig.add_trace(go.Scatter(
            x=[row['date']],
            y=[row['specialty']],
            mode='markers',
            marker=dict(
                size=15,
                color=color_map[row['specialty']],
                line=dict(width=2, color='DarkSlateGrey')
            ),
            name=row['title'],
            text=hover_text,
            hoverinfo='text'
        ))
    
    # Update layout
    fig.update_layout(
        title="Gwendolyn Vials Moore - Medical History Timeline",
        xaxis=dict(
            title="Date",
            type='date',
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            title="Medical Specialty",
            categoryorder='category ascending'
        ),
        hovermode='closest',
        height=800,
        template='plotly_dark'
    )
    
    # Save to HTML file
    fig.write_html("gwendolyn_medical_timeline_with_phb.html")
    print("Timeline saved to gwendolyn_medical_timeline_with_phb.html")
    
    # Also save the data as JSON for future reference
    with open('gwendolyn_medical_data_enhanced.json', 'w') as f:
        json.dump([{
            'title': row['title'],
            'date': row['date'].strftime('%Y-%m-%d') if row['date'] else None,
            'specialty': row['specialty'],
            'personnel': row['personnel'],
            'hospitals': row['hospitals'],
            'appointments': row['appointments'],
            'dates': row['dates'],
            'medications': row['medications'],
            'procedures': row['procedures'],
            'diagnoses': row['diagnoses'],
            'events': row['events'],
            'phb_categories': row['phb_categories'],
            'phb_supports': row['phb_supports'],
            'content': row['content']
        } for _, row in df.iterrows()], f, indent=2)
    
    print("Enhanced data saved to gwendolyn_medical_data_enhanced.json")

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
        # Create timeline
        create_timeline(dated_notes)
    else:
        print("No valid notes with dates found.")

if __name__ == "__main__":
    main()
