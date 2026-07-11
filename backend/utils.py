import os
import tempfile

import PyPDF2
from docx import Document

try:
    from groq import Groq
except Exception:
    Groq = None

try:
    from .config import Config
except ImportError:
    from config import Config


groq_client = Groq(api_key=Config.GROQ_API_KEY) if Groq and Config.GROQ_API_KEY else None


def extract_text_from_file(file_storage):
    filename = file_storage.filename.lower()
    content = ""

    try:
        if filename.endswith(".txt"):
            content = file_storage.read().decode("utf-8", errors="ignore")

        elif filename.endswith(".pdf"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                file_storage.save(tmp.name)
                tmp.close()
                with open(tmp.name, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        content += page.extract_text() or ""
                os.unlink(tmp.name)

        elif filename.endswith(".docx"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                file_storage.save(tmp.name)
                tmp.close()
                doc = Document(tmp.name)
                content = "\n".join([para.text for para in doc.paragraphs])
                os.unlink(tmp.name)

        else:
            content = f"[Unsupported file type: {filename}]"

    except Exception as e:
        content = f"[Error reading file: {str(e)}]"

    return content


def generate_chat_title(user_message: str) -> str:
    try:
        if not groq_client:
            title = user_message.strip()
            return title[:50] + ("..." if len(title) > 50 else "")

        system_prompt = (
            "Generate a concise, descriptive title (max 5 words) for a conversation "
            "that starts with the following message. Return ONLY the title, no quotes or extra text."
        )
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=20,
        )
        title = response.choices[0].message.content.strip()
        return title[:100] + ("..." if len(title) > 100 else "")

    except Exception:
        title = user_message[:50]
        return title + ("..." if len(user_message) > 50 else "")


def get_ai_response(chat_history, user_message, file_content=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Allumina AI, a helpful assistant. "
                "You respond in the same language the user writes in. "
                "You can output structured formats like tables, code blocks, JSON, etc. when requested. "
                "Always format code with proper markdown syntax. "
                "Be concise but thorough."
            ),
        }
    ]

    for msg in chat_history:
        messages.append({"role": msg.role, "content": msg.content})

    content = user_message
    if file_content:
        content += f"\n\n[Attached file content:]\n{file_content}"

    messages.append({"role": "user", "content": content})

    if not groq_client:
        return "GROQ_API_KEY is missing. Add it in your environment file."

    try:
        response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, an error occurred: {str(e)}"
