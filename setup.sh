#!/bin/bash

# Install system dependencies
apt-get update
apt-get install -y tesseract-ocr poppler-utils

# Create necessary directories
mkdir -p knowledge_store
mkdir -p docs
