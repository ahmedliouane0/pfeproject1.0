M2M-100 Translation Microservice
A standalone FastAPI-based multilingual translation and language detection microservice powered by Facebook's M2M-100 model and FastText Language Identification (LID). This service provides intelligent language detection and translation capabilities through REST API endpoints, designed to be integrated with any application or system requiring multilingual support.
🚀 Features

Multi-language Translation: Translate text between 30+ languages using the M2M-100 model
Intelligent Language Detection: Automatic language detection using FastText LID model
Entity-based Translation: Translate specific text entities while preserving context
Content Analysis: Detect foreign language words within articles or documents
GPU Acceleration: Automatic GPU utilization when available for faster processing
RESTful API: Clean, documented REST endpoints with Pydantic models
Microservice Architecture: Standalone service designed for integration with any application
Production Ready: Comprehensive logging, error handling, and health checks

🔧 Supported Languages
The API supports translation between the following languages:
English, French, German, Spanish, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Norwegian, Danish, Finnish, Polish, Czech, Hungarian, Croatian, Serbian, Slovenian, Slovak, Lithuanian, Latvian, Estonian, Ukrainian, Greek
📋 Requirements

Python 3.8+
PyTorch
Transformers (Hugging Face)
FastText
FastAPI
Uvicorn

🛠️ Installation

Clone the repository
bashgit clone https://github.com/yourusername/m2m100-translation-service.git
cd m2m100-translation-service

Create a virtual environment
bashpython -m venv translation-env
source translation-env/bin/activate  # On Windows: translation-env\Scripts\activate

Install dependencies
bashpip install -r requirements.txt

Run the application
bashpython main.py


The API will be available at http://localhost:8002
📦 Dependencies
Create a requirements.txt file with the following dependencies:
txtfastapi>=0.104.0
uvicorn>=0.24.0
torch>=2.0.0
transformers>=4.35.0
fasttext-wheel>=0.9.2
pydantic>=2.4.0
requests>=2.31.0
tqdm>=4.66.0
🔗 Integration
This microservice is designed to be integrated with web applications, content management systems, and other services requiring translation capabilities.
Example Integration Projects

Django Applications: Integrate with Django apps for multilingual content management
Content Management Systems: Add translation capabilities to CMS platforms
API Gateways: Use as a translation service behind API gateways
Batch Processing: Integrate with data processing pipelines for bulk translation
