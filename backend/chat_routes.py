from flask import Blueprint, request, jsonify, session

try:
    from .models import db, Chat, Message
    from .utils import generate_chat_title, get_ai_response, extract_text_from_file
except ImportError:
    from models import db, Chat, Message
    from utils import generate_chat_title, get_ai_response, extract_text_from_file

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chats", methods=["GET"])
def list_chats():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    chats = Chat.query.filter_by(user_id=session["user_id"]).order_by(Chat.created_at.desc()).all()
    return jsonify([
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat()
        }
        for c in chats
    ]), 200


@chat_bp.route("/chats", methods=["POST"])
def create_chat():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    message_text = request.form.get("message", "").strip()
    if not message_text:
        return jsonify({"error": "Message is required."}), 400

    file_content = None
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "":
            file_content = extract_text_from_file(file)

    title = generate_chat_title(message_text)
    chat = Chat(user_id=session["user_id"], title=title)
    db.session.add(chat)
    db.session.flush()

    ai_reply = get_ai_response([], message_text, file_content)

    user_msg = Message(chat_id=chat.id, role="user", content=message_text)
    assistant_msg = Message(chat_id=chat.id, role="assistant", content=ai_reply)
    db.session.add(user_msg)
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        "chat_id": chat.id,
        "title": chat.title,
        "user_message": {
            "id": user_msg.id,
            "content": message_text,
            "role": "user"
        },
        "assistant_message": {
            "id": assistant_msg.id,
            "content": ai_reply,
            "role": "assistant"
        }
    }), 201


@chat_bp.route("/chats/<int:chat_id>/messages", methods=["GET"])
def get_messages(chat_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    messages = [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        }
        for m in chat.messages
    ]
    return jsonify({"chat_id": chat.id, "title": chat.title, "messages": messages}), 200


@chat_bp.route("/chats/<int:chat_id>/messages", methods=["POST"])
def send_message(chat_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    message_text = request.form.get("message", "").strip()
    if not message_text:
        return jsonify({"error": "Message is required."}), 400

    file_content = None
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "":
            file_content = extract_text_from_file(file)

    history = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()
    ai_reply = get_ai_response(history, message_text, file_content)

    user_msg = Message(chat_id=chat.id, role="user", content=message_text)
    assistant_msg = Message(chat_id=chat.id, role="assistant", content=ai_reply)
    db.session.add(user_msg)
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        "user_message": {
            "id": user_msg.id,
            "content": message_text,
            "role": "user"
        },
        "assistant_message": {
            "id": assistant_msg.id,
            "content": ai_reply,
            "role": "assistant"
        }
    }), 201


@chat_bp.route("/chats/<int:chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    db.session.delete(chat)
    db.session.commit()
    return jsonify({"message": "Chat deleted."}), 200
