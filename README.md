# Gwendolyn's Medical Timeline

This application processes Evernote export files (.enex) containing medical records for Gwendolyn Vials Moore and presents them in an interactive timeline format. It includes OCR processing of attachments, semantic search capabilities, and integration with the Personal Health Budget (PHB) framework.

## Features

- **Interactive Timeline**: View all medical events in chronological order
- **Diagnostic Journey**: Track the progression of diagnoses and specialties
- **PHB Integration**: Link events to PHB categories and supports
- **Attachment Processing**: OCR for images and PDFs, text extraction from documents
- **Semantic Search**: Search across all content including attachments
- **Patient Information**: View comprehensive patient details

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

3. Place your Evernote export (.enex) files in the project directory.

## Usage

### Running the Streamlit App

```
streamlit run streamlit_app.py
```

This will start the Streamlit server and open the application in your web browser.

### Running the Flask App (Alternative)

```
python app.py
```

This will start the Flask server on http://localhost:5000.

## Requirements

- Python 3.9+
- Tesseract OCR (for image processing)
- Poppler (for PDF processing)

### Installing Tesseract OCR

- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `apt-get install tesseract-ocr`
- **Windows**: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Installing Poppler

- **macOS**: `brew install poppler`
- **Ubuntu/Debian**: `apt-get install poppler-utils`
- **Windows**: Download and install from [poppler for Windows](http://blog.alivate.com.au/poppler-windows/)

## Project Structure

- `app.py`: Flask application
- `streamlit_app.py`: Streamlit application
- `enex_parser.py`: Functions to parse Evernote export files
- `attachment_processor.py`: OCR and text extraction for attachments
- `improved_phb_details.py`: PHB categories and supports
- `patient_info.py`: Patient information
- `evernote_utils.py`: Utilities for working with Evernote notes
- `attachments/`: Directory for extracted attachments
- `processed_attachments/`: Directory for processed attachment content
- `vector_db/`: Directory for vector database

## Deployment

For sharing with family and medical professionals, you can deploy this application using:

1. **Streamlit Cloud**: https://streamlit.io/cloud
2. **Modal**: https://modal.com/
3. **Heroku**: https://heroku.com/

## License

This project is private and intended for personal use by the Vials Moore family and authorized medical professionals.

## Acknowledgements

- Streamlit for the interactive web framework
- Langchain for vector search capabilities
- Tesseract OCR for image text extraction
