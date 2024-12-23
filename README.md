# Chat-Bot-API Documentation

## Overview
Chat-Bot-API is a sophisticated chatbot framework built on **FastAPI**, offering a cutting-edge, AI-driven conversational experience. Leveraging **Retrieval-Augmented Generation (RAG)** with OpenAI and free **LLAMA models**, this platform empowers users with intelligent document-based interactions and custom AI model support. The system is designed to be modular, scalable, and open-source, enabling seamless integration and customization for various use cases.

---

## Purpose and Objectives
The Chat-Bot-API is focused on achieving the following goals:
- **Streamlined AI Interactions**: Facilitate intuitive and efficient user engagement with AI models and document retrieval.
- **Personalized Experiences**: Deliver tailored chatbot interactions for diverse user needs.
- **Open Access AI**: Democratize advanced AI technologies through free-to-use models and open-source code.
- **Collaborative Development**: Encourage contributions and adaptations by offering a flexible and extensible architecture.

---

## Key Features
1. **User Authentication**:
   - Secure, token-based user registration and login.
   - Persistent session tracking for uninterrupted interactions.

2. **AI-Powered Chat**:
   - Personalized chatbot experiences driven by OpenAI and LLAMA models.
   - Advanced document querying through RAG integration.

3. **Custom Model Management**:
   - Upload and manage user-specific models with metadata and visibility controls.

4. **Chat History Management**:
   - Save, retrieve, and organize extensive conversation logs.

5. **CORS Middleware**:
   - Pre-configured cross-origin resource sharing for broad API compatibility.

6. **Open Source**:
   - Fully transparent and modifiable codebase to foster innovation.

---

## Installation

### Prerequisites
1. **Python**: Version 3.10 or higher.
2. **MySQL**: An active MySQL database.
3. **Git**: For cloning the repository.

### Steps
1. **Clone the Repository**:
   ```python
   git clone https://github.com/CoderGoC/last_exam.git
   cd Chat-Bot-API
   ```

2. **Set Up a Virtual Environment**:
   ```python
   python -m venv env
   source env/bin/activate  # macOS/Linux
   env\Scripts\activate     # Windows
   ```

3. **Install Dependencies**:
   ```python
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the `data` directory and include:
   ```env
   MYSQL_HOST=<MySQL Host>
   MYSQL_USER=<MySQL Username>
   MYSQL_PASSWORD=<MySQL Password>
   MYSQL_DATABASE=<Database Name>
   REPLICATE_API=<Replicate API Key>
   ```

5. **Launch the Application**:
   ```python
   uvicorn main:app --reload
   ```

6. **Access API Documentation**:
   Open `http://127.0.0.1:8000/docs` in your browser for an interactive Swagger UI.

---

## Core Workflow
1. **User Interaction**:
   - Authenticate via token-based login.
   - Access personalized chatbots linked to individual accounts.
   - Chatbots process queries using AI and document retrieval.

2. **AI Model Utilization**:
   - Combines OpenAI and LLAMA models for RAG and general conversations.
   - Supports user-uploaded models for custom scenarios.

3. **Data Storage**:
   - Stores user profiles, chat logs, and model metadata securely in MySQL.

4. **API Accessibility**:
   - Ensures compatibility across different domains through CORS middleware.

---

## Directory Structure
```python
Chat-Bot-API/
│
├── data/               # Configuration and environment settings
│   ├── config.py
│
├── db/                 # Database connection scripts
│   ├── database.py
│
├── models/             # AI model handling
│   ├── llm.py
│
├── routes/             # API route definitions
│   ├── auth.py
│   ├── prompts.py
│   ├── user_page.py
│
├── functions/          # Utility functions
│   ├── functions.py
│
├── main.py             # Application entry point
├── loader.py           # Component initialization
├── requirements.txt    # Python dependencies
├── README.md           # Documentation (current file)
│
└── .env                # Environment variables file
```

---

## Project Motivation
The Chat-Bot-API was developed to bridge the gap between cutting-edge AI technologies and accessibility. By combining RAG with open models, the project empowers users to interact seamlessly with documents and conversational AI, promoting open-source collaboration and democratizing AI capabilities.

---

## Contribution Guidelines
Contributions are welcome! Follow these steps to get involved:
1. Fork the repository.
2. Create a feature branch:
   ```python
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```python
   git commit -m "Add new feature"
   ```
4. Push the branch:
   ```python
   git push origin feature-name
   ```
5. Open a pull request targeting the `main` branch.

---

## License
This project is licensed under the MIT License. For more details, see the [LICENSE](LICENSE) file.

---

### Thank you for your interest and contributions to this project!
