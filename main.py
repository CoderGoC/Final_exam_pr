from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loader import db
from routes import auth, user_page, promts


desc = """
# Project: ChatBot Service

A **FastAPI-powered chatbot platform** offering features like secure user authentication, personalized chatbot interactions, and model management. Users can create and use their own chatbots powered by OpenAI (via RAG) or the free LLAMA model. The project is open-source and welcomes contributions.

---

## Features:
1. **User Authentication**:
   - Secure registration and token-based login.
2. **Chatbot Interaction**:
   - Document-based AI queries.
   - Chat history and custom models.
3. **Prompt Management**:
   - Efficient prompt handling.
4. **Database Management**:
   - Automated table creation for users, models, chats, and messages.
5. **CORS Support**:
   - Cross-origin requests enabled.

---

## Middleware:
**CORS Middleware**:
- Allows requests from any origin, methods, and headers with credential support.

---

## API Routes:
- **Authentication (`/auth`)**: User registration, login, and token management.
- **User (`/user`)**: Personalized user functionalities.
- **Prompts (`/promts`)**: Manage chatbot prompts.

---

## Database Tables:
1. **Users**: Stores user credentials.
2. **Models**: AI model metadata.
3. **Chats**: Chat session data.
4. **Messages**: Chat history.

---
"""


app = FastAPI(title="ChatBot Service",
            description=desc,
            version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(user_page.router, prefix="/user", tags=["User"])
app.include_router(promts.router, prefix="/promts", tags=["Promts"])

db.create_user_table()
db.create_table_models()
db.create_chats_table()
db.create_table_chat_messages()