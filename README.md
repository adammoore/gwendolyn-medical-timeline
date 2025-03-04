# Gwendolyn's Medical Timeline

This application processes Evernote export files (.enex) containing medical records for Gwendolyn Vials Moore and presents them in an interactive timeline format. It includes OCR processing of attachments, semantic search capabilities, and integration with the Personal Health Budget (PHB) framework.

## Features

- **Interactive Timeline**: View all medical events in chronological order
- **Diagnostic Journey**: Track the progression of diagnoses and specialties
- **PHB Integration**: Link events to PHB categories and supports
- **Attachment Processing**: OCR for images and PDFs, text extraction from documents
- **Semantic Search**: Search across all content including attachments
- **Patient Information**: View comprehensive patient details
- **Medical Practitioners View**: See all medical practitioners and their associated documents
- **Medical Facilities View**: See all medical facilities and their associated documents

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install system dependencies:
   - **Tesseract OCR**:
     - macOS: `brew install tesseract`
     - Ubuntu/Debian: `apt-get install tesseract-ocr`
     - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   
   - **Poppler** (for PDF processing):
     - macOS: `brew install poppler`
     - Ubuntu/Debian: `apt-get install poppler-utils`
     - Windows: Download from [poppler for Windows](http://blog.alivate.com.au/poppler-windows/)

4. Place your Evernote export (.enex) files in the project directory.

5. Run the indexing script to create the knowledge store:
   ```
   python index_documents.py
   ```

## Usage

### Running the Streamlit App

```
streamlit run streamlit_app.py
```

This will start the Streamlit server and open the application in your web browser.

## Project Structure

- `streamlit_app.py`: Streamlit application
- `index_documents.py`: Script to index documents and create the knowledge store
- `knowledge_store_reader.py`: Module to read data from the knowledge store
- `attachment_processor.py`: OCR and text extraction for attachments
- `improved_phb_details.py`: PHB categories and supports
- `patient_info.py`: Patient information
- `evernote_utils.py`: Utilities for working with Evernote notes
- `knowledge_store/`: Directory for the knowledge store
- `docs/`: Directory for external documents

## Deployment

This application can be deployed using Streamlit Cloud:

1. Push the repository to GitHub
2. Connect to Streamlit Cloud: https://streamlit.io/cloud
3. Point to the GitHub repository and the `streamlit_app.py` file

## License

This project is private and intended for personal use by the Vials Moore family and authorized medical professionals.
