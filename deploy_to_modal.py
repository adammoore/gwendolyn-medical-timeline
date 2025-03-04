"""
deploy_to_modal.py

Script to deploy the Streamlit app to Modal.
"""

import shlex
import subprocess
from pathlib import Path
import modal

# Define container dependencies
image = modal.Image.debian_slim(python_version="3.9").pip_install(
    "streamlit>=1.42.0",
    "pandas>=2.0.0",
    "plotly>=5.0.0",
    "pillow>=9.0.0",
    "beautifulsoup4>=4.9.0",
    "pytesseract>=0.3.0",
    "pdf2image>=1.16.0",
    "opencv-python-headless>=4.5.0",
    "docx2txt>=0.8",
    "pypdf>=3.0.0",
    "python-docx>=0.8.0",
    "langchain>=0.3.0",
    "langchain-community>=0.3.0",
    "faiss-cpu>=1.7.0",
    "sentence-transformers>=2.2.0",
    "chromadb>=0.4.0"
)

# Install system dependencies
image = image.apt_install("tesseract-ocr", "poppler-utils")

app = modal.App(name="gwendolyn-medical-timeline", image=image)

# Mount the necessary files
streamlit_script_local_path = Path(__file__).parent / "streamlit_app.py"
streamlit_script_remote_path = Path("/root/streamlit_app.py")

enex_parser_local_path = Path(__file__).parent / "enex_parser.py"
enex_parser_remote_path = Path("/root/enex_parser.py")

attachment_processor_local_path = Path(__file__).parent / "attachment_processor.py"
attachment_processor_remote_path = Path("/root/attachment_processor.py")

improved_phb_details_local_path = Path(__file__).parent / "improved_phb_details.py"
improved_phb_details_remote_path = Path("/root/improved_phb_details.py")

patient_info_local_path = Path(__file__).parent / "patient_info.py"
patient_info_remote_path = Path("/root/patient_info.py")

evernote_utils_local_path = Path(__file__).parent / "evernote_utils.py"
evernote_utils_remote_path = Path("/root/evernote_utils.py")

# Mount the attachments directory
attachments_local_path = Path(__file__).parent / "attachments"
attachments_remote_path = Path("/root/attachments")

# Create mounts
mounts = [
    modal.Mount.from_local_file(streamlit_script_local_path, streamlit_script_remote_path),
    modal.Mount.from_local_file(enex_parser_local_path, enex_parser_remote_path),
    modal.Mount.from_local_file(attachment_processor_local_path, attachment_processor_remote_path),
    modal.Mount.from_local_file(improved_phb_details_local_path, improved_phb_details_remote_path),
    modal.Mount.from_local_file(patient_info_local_path, patient_info_remote_path),
    modal.Mount.from_local_file(evernote_utils_local_path, evernote_utils_remote_path),
]

# Add attachments mount if the directory exists
if attachments_local_path.exists():
    mounts.append(modal.Mount.from_local_dir(attachments_local_path, attachments_remote_path))

# Define the web server function
@app.function(
    allow_concurrent_inputs=100,
    mounts=mounts,
)
@modal.web_server(8000)
def run():
    target = shlex.quote(str(streamlit_script_remote_path))
    cmd = f"streamlit run {target} --server.port 8000 --server.enableCORS=false --server.enableXsrfProtection=false"
    subprocess.Popen(cmd, shell=True)

if __name__ == "__main__":
    app.serve()
