# PHP Playground - AI-Powered Educational Grading System

## 📝 Development Log

[View detailed development progress and insights →](https://www.notion.so/arthur-blog/job-php-and-agents-26b59c53972880749f95debb3e1ab89f?source=copy_link)

## 🌟 Features

### Professor Interface
- **Question Management**: Create questions with reading materials
- **Bootstrap UI**: Modern, responsive web interface

### Student Interface
- **Interactive Testing**: Answer questions with AI feedback
- **Random Questions**: Get randomly selected questions from the question bank

### AI Grading Engine
- **Semantic Analysis**: Uses sentence transformers for meaning-based comparison
- **LLM Integration**: Powered by Ollama (Llama3) for advanced text analysis
- **Detailed Feedback**: Provides specific, actionable feedback to students

## 🏗️ Architecture

```
├── Frontend (PHP)
│   ├── professor.php    # Question management interface
│   ├── student.php      # Student testing interface
│   └── course_work.json # Question database
├── Backend (Python)
│   ├── backend.py       # Flask API server
│   ├── grader.py        # AI grading engine
│   └── requirements.txt # Python dependencies
└── AI Components
    ├── Sentence Transformers (MPA/sambert)
    ├── Ollama (Llama3:8b)
    └── Semantic similarity analysis
```

## 📋 Prerequisites


- **Python 3.10** with pip
- **Ollama** with Llama3:8b model


## 🚀 Installation

### 1. Clone the Repository

### 2. Install Python Dependencies
```bash
# Create virtual environment 
python -m venv venv
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Setup Ollama
```bash
# Install Ollama (visit https://ollama.ai for installation instructions)
# Pull the Llama3 model
ollama run llama3:8b
```



## 🎯 Usage

### Starting the System


#### 1. Start Python Backend
```bash
# Navigate to project directory and activate venv if created

venv\Scripts\activate

# Start Flask server
python backend.py
```
The backend will be available at `http://localhost:5000`

#### 3. Start PHP Frontend
```bash
# For Professor interface
php -S localhost:8000
```
access with /student.php and /professor.php

## 🔧 API Endpoints

The Python backend provides several REST API endpoints:


### `POST /process`
Grade a student answer
```json
// Request
{
  "text": "student answer text",
  "question_id": 1
}

// Response
{
  "status": "success",
  "score": 2,
  "max_score": 3,
  "feedback": "Detailed feedback message",
  "detailed_scores": [1, 1, 0]
}
```

## 🧠 AI Grading Process

The grading system uses a sophisticated multi-step approach:

1. **Rubric Analysis**: Extracts scoring criteria and point distribution
2. **Answer Segmentation**: Splits both student and model answers into logical parts
3. **Semantic Matching**: Uses sentence transformers to find semantic similarities
4. **Feedback Generation**: Creates personalized, actionable feedback




### Frontend Configuration
- **API Endpoint**: Default `http://localhost:5000/process`


**CORS Issues**
- Ensure Flask-CORS is installed and configured
- Check browser console for detailed error messages

**JSON Parsing Errors**
- Verify `course_work.json` format
- Check for unescaped quotes in question content

## 📊 Performance Notes

- **First Run**: Initial model loading may take 30-60 seconds
- **Grading Speed**: Typically 10-30 seconds per answer depending on GPU

