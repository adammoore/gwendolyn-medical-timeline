import os
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Define medical specialties and keywords for classification
SPECIALTIES = {
    'Neurology': ['neuro', 'brain', 'seizure', 'epilepsy', 'neurologist'],
    'Cardiology': ['heart', 'cardiac', 'cardio', 'cardiologist'],
    'Pulmonology': ['lung', 'pulmonary', 'respiratory', 'breathing', 'pulmonologist'],
    'Gastroenterology': ['stomach', 'intestine', 'gastro', 'gi', 'gastroenterologist'],
    'Orthopedics': ['bone', 'joint', 'fracture', 'ortho', 'orthopedist'],
    'Endocrinology': ['hormone', 'thyroid', 'diabetes', 'endocrine', 'endocrinologist'],
    'Ophthalmology': ['eye', 'vision', 'ophthalmologist'],
    'ENT': ['ear', 'nose', 'throat', 'ent'],
    'Dermatology': ['skin', 'rash', 'dermatologist'],
    'Hematology': ['blood', 'anemia', 'hematologist'],
    'Oncology': ['cancer', 'tumor', 'oncologist'],
    'Nephrology': ['kidney', 'renal', 'nephrologist'],
    'Urology': ['bladder', 'urinary', 'urologist'],
    'Rheumatology': ['arthritis', 'rheumatoid', 'rheumatologist'],
    'Immunology': ['immune', 'allergy', 'immunologist'],
    'Psychiatry': ['mental', 'psychiatric', 'psychiatrist'],
    'Pediatrics': ['pediatric', 'pediatrician', 'child', 'children'],
    'General': ['doctor', 'physician', 'gp', 'general practitioner']
}

def determine_specialty(text):
    """Determine medical specialty based on keywords in text"""
    text = text.lower()
    
    # Check for each specialty's keywords
    for specialty, keywords in SPECIALTIES.items():
        for keyword in keywords:
            if keyword in text:
                return specialty
    
    return "Unknown"

def extract_personnel(text):
    """Extract medical personnel names from text"""
    # Simple pattern for Dr. LastName or Doctor LastName
    doctor_pattern = r'(?:Dr\.|Doctor)\s+([A-Z][a-z]+)'
    doctors = re.findall(doctor_pattern, text)
    
    # Simple pattern for Nurse LastName
    nurse_pattern = r'(?:Nurse)\s+([A-Z][a-z]+)'
    nurses = re.findall(nurse_pattern, text)
    
    personnel = doctors + nurses
    return personnel if personnel else ["Unknown"]

def extract_significant_events(text):
    """Extract significant medical events from text"""
    # Keywords that might indicate significant events
    event_keywords = [
        'diagnosis', 'diagnosed', 'surgery', 'operation', 'procedure', 
        'admitted', 'admission', 'discharged', 'discharge', 'emergency',
        'treatment', 'therapy', 'medication', 'prescribed', 'test results',
        'scan', 'mri', 'ct', 'x-ray', 'ultrasound', 'blood test'
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
                    except Exception as e:
                        print(f"Error parsing content XML: {e}")
                        text_content = "Error extracting content"
                else:
                    text_content = ""
                
                # Determine medical specialty
                specialty = determine_specialty(title + " " + text_content)
                
                # Extract personnel
                personnel = extract_personnel(title + " " + text_content)
                
                # Extract significant events
                events = extract_significant_events(text_content)
                
                notes_data.append({
                    'title': title,
                    'date': created_date,
                    'specialty': specialty,
                    'personnel': personnel,
                    'events': events,
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
        hover_text += f"Events: {', '.join(row['events'][:2])}<br>"
        
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
    fig.write_html("gwendolyn_medical_timeline.html")
    print("Timeline saved to gwendolyn_medical_timeline.html")
    
    # Also save the data as JSON for future reference
    with open('gwendolyn_medical_data.json', 'w') as f:
        json.dump([{
            'title': row['title'],
            'date': row['date'].strftime('%Y-%m-%d') if row['date'] else None,
            'specialty': row['specialty'],
            'personnel': row['personnel'],
            'events': row['events'],
            'content': row['content']
        } for _, row in df.iterrows()], f, indent=2)
    
    print("Data saved to gwendolyn_medical_data.json")

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
