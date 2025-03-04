"""
attachment_processor.py

This module provides functions to process attachments from Evernote notes,
including OCR for images and PDFs, text extraction from documents,
and vector storage for enhanced search capabilities.
"""

import os
import re
import sys
import numpy as np
from PIL import Image
import json
import hashlib
from datetime import datetime
import improved_phb_details as phb_details
import patient_info

# Check for OCR-related libraries
TESSERACT_AVAILABLE = False
PDF_IMAGE_AVAILABLE = False
CV2_AVAILABLE = False
DOCX_AVAILABLE = False
PDF_AVAILABLE = False
VECTOR_DB_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    print("Warning: pytesseract not available. OCR functionality will be limited.")

try:
    import pdf2image
    PDF_IMAGE_AVAILABLE = True
except ImportError:
    print("Warning: pdf2image not available. PDF processing will be limited.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    print("Warning: OpenCV not available. Image processing will be limited.")

try:
    import docx2txt
    DOCX_AVAILABLE = True
except ImportError:
    print("Warning: docx2txt not available. DOCX processing will be limited.")

try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    print("Warning: pypdf not available. PDF processing will be limited.")

# Set up vector database
try:
    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    VECTOR_DB_AVAILABLE = True
except ImportError:
    print("Warning: Vector database libraries not available. Search functionality will be limited.")

# Directory for processed attachment content
PROCESSED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_attachments")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Vector DB path
VECTOR_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_db")
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

# Initialize embeddings model if available
embeddings = None
text_splitter = None
if VECTOR_DB_AVAILABLE:
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        # Text splitter for chunking documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    except Exception as e:
        print(f"Warning: Could not initialize embeddings model: {e}")
        VECTOR_DB_AVAILABLE = False

def extract_text_from_image_basic(image_path):
    """
    Extract text from an image using basic PIL functionality.
    This is a fallback when OCR is not available.
    
    Parameters:
        image_path (str): Path to the image file.
        
    Returns:
        str: A message indicating OCR is not available.
    """
    try:
        # Just verify the image can be opened
        img = Image.open(image_path)
        width, height = img.size
        return f"[Image: {width}x{height}] OCR text extraction not available. Install pytesseract for OCR functionality."
    except Exception as e:
        return f"Error opening image: {str(e)}"

def process_image(image_path):
    """
    Process an image file using OCR to extract text.
    
    Parameters:
        image_path (str): Path to the image file.
        
    Returns:
        str: Extracted text from the image.
    """
    if not TESSERACT_AVAILABLE or not CV2_AVAILABLE:
        return extract_text_from_image_basic(image_path)
    
    try:
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            # Try with PIL if OpenCV fails
            img = Image.open(image_path)
            img = np.array(img)
            
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        # Apply thresholding to preprocess the image
        _, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Perform OCR
        text = pytesseract.image_to_string(threshold)
        
        return text
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return f"Error processing image: {str(e)}"

def extract_text_from_pdf_basic(pdf_path):
    """
    Extract text from a PDF using basic functionality.
    This is a fallback when full PDF processing is not available.
    
    Parameters:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Basic information about the PDF.
    """
    try:
        # Just verify the PDF exists
        file_size = os.path.getsize(pdf_path) / 1024  # Size in KB
        return f"[PDF: {file_size:.1f} KB] Full text extraction not available. Install pypdf and pdf2image for PDF processing."
    except Exception as e:
        return f"Error accessing PDF: {str(e)}"

def process_pdf(pdf_path):
    """
    Process a PDF file to extract text, using OCR if needed.
    
    Parameters:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        str: Extracted text from the PDF.
    """
    if not PDF_AVAILABLE:
        return extract_text_from_pdf_basic(pdf_path)
    
    try:
        # First try to extract text directly
        pdf = PdfReader(pdf_path)
        text = ""
        
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        
        # If no text was extracted and OCR is available, use OCR
        if not text.strip() and TESSERACT_AVAILABLE and PDF_IMAGE_AVAILABLE and CV2_AVAILABLE:
            try:
                # Convert PDF to images
                images = pdf2image.convert_from_path(pdf_path)
                
                # Process each image with OCR
                for i, img in enumerate(images):
                    # Convert PIL Image to numpy array
                    img_np = np.array(img)
                    
                    # Convert to grayscale
                    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                    
                    # Apply thresholding
                    _, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # Perform OCR
                    page_text = pytesseract.image_to_string(threshold)
                    text += f"Page {i+1}:\n{page_text}\n\n"
            except Exception as e:
                # If PDF to image conversion fails, add a note
                text += f"\n[Note: Could not perform OCR on this PDF: {str(e)}]"
        
        # If still no text, provide a message
        if not text.strip():
            num_pages = len(pdf.pages)
            text = f"[PDF: {num_pages} pages] No extractable text found. Install poppler and tesseract for OCR functionality."
        
        return text
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return f"Error processing PDF: {str(e)}"

def extract_text_from_docx_basic(docx_path):
    """
    Extract basic information about a DOCX file.
    This is a fallback when DOCX processing is not available.
    
    Parameters:
        docx_path (str): Path to the DOCX file.
        
    Returns:
        str: Basic information about the DOCX.
    """
    try:
        # Just verify the DOCX exists
        file_size = os.path.getsize(docx_path) / 1024  # Size in KB
        return f"[DOCX: {file_size:.1f} KB] Text extraction not available. Install docx2txt for DOCX processing."
    except Exception as e:
        return f"Error accessing DOCX: {str(e)}"

def process_docx(docx_path):
    """
    Process a DOCX file to extract text.
    
    Parameters:
        docx_path (str): Path to the DOCX file.
        
    Returns:
        str: Extracted text from the DOCX file.
    """
    if not DOCX_AVAILABLE:
        return extract_text_from_docx_basic(docx_path)
    
    try:
        text = docx2txt.process(docx_path)
        return text
    except Exception as e:
        print(f"Error processing DOCX {docx_path}: {e}")
        return f"Error processing DOCX: {str(e)}"

def process_attachment(attachment):
    """
    Process an attachment based on its file type.
    
    Parameters:
        attachment (dict): Attachment information dictionary.
        
    Returns:
        dict: Processed attachment with extracted text.
    """
    file_path = attachment["file_path"]
    mime_type = attachment["mime_type"]
    file_name = attachment["file_name"]
    
    # Skip if file doesn't exist
    if not os.path.exists(file_path):
        attachment["extracted_text"] = "File not found"
        return attachment
    
    # Check if we've already processed this attachment
    hash_obj = hashlib.md5(file_path.encode())
    file_hash = hash_obj.hexdigest()
    processed_path = os.path.join(PROCESSED_DIR, f"{file_hash}.json")
    
    if os.path.exists(processed_path):
        # Load previously processed data
        with open(processed_path, 'r') as f:
            processed_data = json.load(f)
        
        # Update the attachment with the processed data
        attachment.update(processed_data)
        return attachment
    
    # Process based on file type
    extracted_text = ""
    
    if mime_type.startswith("image/"):
        extracted_text = process_image(file_path)
    elif mime_type == "application/pdf":
        extracted_text = process_pdf(file_path)
    elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                      "application/msword"]:
        extracted_text = process_docx(file_path)
    else:
        # For other file types, just note the type
        file_size = os.path.getsize(file_path) / 1024  # Size in KB
        extracted_text = f"[{mime_type}: {file_size:.1f} KB] No text extraction available for this file type."
    
    # Extract medical information
    medical_info = {}
    if extracted_text:
        medical_info = extract_medical_info(file_name, extracted_text)
    
    # Create processed data
    processed_data = {
        "extracted_text": extracted_text,
        "processed_at": datetime.now().isoformat(),
        "medical_info": medical_info,
        "ocr_available": TESSERACT_AVAILABLE,
        "pdf_processing_available": PDF_AVAILABLE and PDF_IMAGE_AVAILABLE
    }
    
    # Save processed data
    with open(processed_path, 'w') as f:
        json.dump(processed_data, f)
    
    # Update the attachment with the processed data
    attachment.update(processed_data)
    
    return attachment

def extract_medical_info(title, content):
    """
    Extract medical information from attachment content.
    
    Parameters:
        title (str): Attachment title.
        content (str): Extracted text content.
        
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
    
    return {
        "specialty": specialty,
        "personnel": personnel,
        "facilities": facilities,
        "events": events,
        "identifiers": identifiers,
        "phb_categories": phb_categories,
        "phb_supports": phb_supports
    }

def extract_personnel(text):
    """
    Extract and categorize medical personnel from text.
    
    Parameters:
        text (str): Text to extract from.
        
    Returns:
        list: List of personnel dictionaries.
    """
    # Define patterns for different types of personnel - improved to catch more variations
    doctor_pattern = r'(?:Dr\.?|Doctor|Prof\.?|Professor|Mr\.?|Mrs\.?|Ms\.?|Miss|Consultant|Specialist|Surgeon|Physician)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+[A-Z][a-z]+)?)'
    nurse_pattern = r'(?:Nurse|Sister|Matron|RN|Staff Nurse|Nursing)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+[A-Z][a-z]+)?)'
    therapist_pattern = r'(?:Therapist|Physiotherapist|Physio|OT|Occupational Therapist|Speech|SALT|SLT|Psychologist)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s+[A-Z][a-z]+)?)'
    
    # Find all matches
    doctors = re.findall(doctor_pattern, text)
    nurses = re.findall(nurse_pattern, text)
    therapists = re.findall(therapist_pattern, text)
    
    # Normalize names to avoid duplicates with different formats
    doctors = [normalize_name(name) for name in doctors]
    nurses = [normalize_name(name) for name in nurses]
    therapists = [normalize_name(name) for name in therapists]
    
    # Remove duplicates
    doctors = list(set(doctors))
    nurses = list(set(nurses))
    therapists = list(set(therapists))
    
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
    
    return personnel

# Helper function to normalize names
def normalize_name(name):
    """
    Normalize a name by removing extra spaces, titles, etc.
    
    Parameters:
        name (str): The name to normalize.
        
    Returns:
        str: The normalized name.
    """
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove titles
    titles = ["dr", "dr.", "doctor", "prof", "prof.", "professor", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "miss"]
    for title in titles:
        if name.startswith(title + " "):
            name = name[len(title) + 1:]
    
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Capitalize first letter of each word
    name = name.title()
    
    return name

def extract_facilities(text):
    """
    Extract and categorize medical facilities from text.
    
    Parameters:
        text (str): Text to extract from.
        
    Returns:
        list: List of facility dictionaries.
    """
    # Define patterns for different types of facilities - improved to catch more variations
    hospital_pattern = r'(?:Hospital|Medical Center|Medical Centre|Clinic|Centre|Center|NHS Trust|Foundation Trust|Children\'s|Paediatric|Pediatric)(?:[:\s]+)([A-Za-z\s\-\']+)'
    department_pattern = r'(?:Department|Dept|Ward|Unit|Clinic|Service|Team|Division)(?:[:\s]+)([A-Za-z\s\-\']+)'
    
    # Find all matches
    hospitals = re.findall(hospital_pattern, text)
    departments = re.findall(department_pattern, text)
    
    # Clean up facility names
    hospitals = [name.strip() for name in hospitals if len(name.strip()) > 2]
    departments = [name.strip() for name in departments if len(name.strip()) > 2]
    
    # Remove duplicates
    hospitals = list(set(hospitals))
    departments = list(set(departments))
    
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

def process_all_attachments(events):
    """
    Process all attachments in all events.
    
    Parameters:
        events (list): List of events with attachments.
        
    Returns:
        list: Updated events with processed attachments.
    """
    updated_events = []
    
    for event in events:
        # Process attachments
        if "attachments" in event and event["attachments"]:
            processed_attachments = []
            for attachment in event["attachments"]:
                processed_attachment = process_attachment(attachment)
                processed_attachments.append(processed_attachment)
            
            event["attachments"] = processed_attachments
            
            # Update event with information from attachments
            update_event_with_attachment_info(event)
        
        updated_events.append(event)
    
    return updated_events

def update_event_with_attachment_info(event):
    """
    Update an event with information extracted from its attachments.
    
    Parameters:
        event (dict): Event to update.
    """
    for attachment in event["attachments"]:
        if "medical_info" not in attachment:
            continue
        
        medical_info = attachment["medical_info"]
        
        # Add personnel
        if "personnel" in medical_info and medical_info["personnel"]:
            if "personnel" not in event:
                event["personnel"] = []
            
            for person in medical_info["personnel"]:
                # Check if this person is already in the event
                if not any(p["name"] == person["name"] for p in event["personnel"]):
                    event["personnel"].append(person)
        
        # Add facilities
        if "facilities" in medical_info and medical_info["facilities"]:
            if "facilities" not in event:
                event["facilities"] = []
            
            for facility in medical_info["facilities"]:
                # Check if this facility is already in the event
                if not any(f["name"] == facility["name"] for f in event["facilities"]):
                    event["facilities"].append(facility)
        
        # Add events
        if "events" in medical_info and medical_info["events"]:
            if "events" not in event:
                event["events"] = []
            
            for med_event in medical_info["events"]:
                # Check if this event is already in the event
                if not any(e["content"] == med_event["content"] for e in event["events"]):
                    event["events"].append(med_event)
        
        # Add PHB categories
        if "phb_categories" in medical_info and medical_info["phb_categories"]:
            if "phb_categories" not in event:
                event["phb_categories"] = []
            
            for category in medical_info["phb_categories"]:
                # Check if this category is already in the event
                if not any(cat["category"] == category["category"] for cat in event["phb_categories"]):
                    event["phb_categories"].append(category)
        
        # Add PHB supports
        if "phb_supports" in medical_info and medical_info["phb_supports"]:
            if "phb_supports" not in event:
                event["phb_supports"] = []
            
            for support in medical_info["phb_supports"]:
                # Check if this support is already in the event
                if not any(sup["support"] == support["support"] for sup in event["phb_supports"]):
                    event["phb_supports"].append(support)
        
        # Add patient identifiers
        if "identifiers" in medical_info and medical_info["identifiers"]:
            if "patient_identifiers" not in event:
                event["patient_identifiers"] = {}
            
            for key, value in medical_info["identifiers"].items():
                if key not in event["patient_identifiers"]:
                    event["patient_identifiers"][key] = value

def create_vector_store(events):
    """
    Create a vector store from all events and their attachments.
    
    Parameters:
        events (list): List of events with processed attachments.
        
    Returns:
        FAISS: Vector store for semantic search.
    """
    if not VECTOR_DB_AVAILABLE:
        print("Vector database functionality not available. Install langchain, langchain-community, and faiss-cpu.")
        return None
    
    documents = []
    
    for event in events:
        # Add event content
        event_text = f"Title: {event['title']}\nDate: {event['date']}\nContent: {event['content']}"
        documents.append({"content": event_text, "metadata": {"id": event["id"], "type": "event"}})
        
        # Add attachment content
        if "attachments" in event and event["attachments"]:
            for i, attachment in enumerate(event["attachments"]):
                if "extracted_text" in attachment and attachment["extracted_text"]:
                    attachment_text = f"Attachment: {attachment['file_name']}\nContent: {attachment['extracted_text']}"
                    documents.append({
                        "content": attachment_text, 
                        "metadata": {
                            "id": event["id"], 
                            "type": "attachment", 
                            "attachment_index": i
                        }
                    })
    
    # Split documents into chunks
    texts = []
    metadatas = []
    
    for doc in documents:
        chunks = text_splitter.split_text(doc["content"])
        for chunk in chunks:
            texts.append(chunk)
            metadatas.append(doc["metadata"])
    
    # Create vector store
    try:
        vector_store = FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)
        
        # Save vector store
        vector_store.save_local(VECTOR_DB_PATH)
        
        return vector_store
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

def load_vector_store():
    """
    Load the vector store from disk.
    
    Returns:
        FAISS: Vector store for semantic search.
    """
    if not VECTOR_DB_AVAILABLE:
        return None
    
    try:
        if os.path.exists(os.path.join(VECTOR_DB_PATH, "index.faiss")):
            return FAISS.load_local(VECTOR_DB_PATH, embeddings)
    except Exception as e:
        print(f"Error loading vector store: {e}")
    
    return None

def semantic_search(query, k=5):
    """
    Perform a semantic search on the vector store.
    
    Parameters:
        query (str): Search query.
        k (int): Number of results to return.
        
    Returns:
        list: List of search results.
    """
    vector_store = load_vector_store()
    if not vector_store:
        return []
    
    try:
        results = vector_store.similarity_search(query, k=k)
        return results
    except Exception as e:
        print(f"Error performing semantic search: {e}")
        return []

def update_patient_info_from_events(events):
    """
    Update patient information from events.
    
    Parameters:
        events (list): List of events with processed attachments.
        
    Returns:
        dict: Updated patient information.
    """
    # Start with existing patient info
    updated_info = patient_info.PATIENT_INFO.copy()
    
    # Add identifiers
    identifiers = {}
    
    for event in events:
        if "patient_identifiers" in event:
            for key, value in event["patient_identifiers"].items():
                if key not in identifiers:
                    identifiers[key] = value
    
    if identifiers:
        updated_info["identifiers"] = identifiers
    
    return updated_info

def get_ocr_status():
    """
    Get the status of OCR and PDF processing capabilities.
    
    Returns:
        dict: Status information.
    """
    return {
        "tesseract_available": TESSERACT_AVAILABLE,
        "pdf_image_available": PDF_IMAGE_AVAILABLE,
        "cv2_available": CV2_AVAILABLE,
        "docx_available": DOCX_AVAILABLE,
        "pdf_available": PDF_AVAILABLE,
        "vector_db_available": VECTOR_DB_AVAILABLE
    }
