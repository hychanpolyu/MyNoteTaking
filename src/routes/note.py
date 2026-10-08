import uuid
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from src.auth import login_required
from src.models.note import Note, NoteAttachment, db
from src.translator import SUPPORTED_LANGUAGES, translate_note

note_bp = Blueprint('note', __name__)

ALLOWED_ATTACHMENT_EXTENSIONS = {
    'doc', 'docx', 'gif', 'jpeg', 'jpg', 'md', 'pdf', 'png', 'txt', 'webp', 'xlsx', 'zip'
}


def _is_allowed_attachment(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ATTACHMENT_EXTENSIONS


@note_bp.route('/notes/<int:note_id>/attachments', methods=['POST'])
@login_required
def upload_attachment(user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=user.id).first_or_404()
    uploaded_file = request.files.get('file')
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({'error': 'Please choose an image or document'}), 400
    if not _is_allowed_attachment(uploaded_file.filename):
        return jsonify({'error': 'This file type is not supported'}), 400

    original_name = secure_filename(uploaded_file.filename)
    file_data = uploaded_file.read()
    stored_name = uuid.uuid4().hex
    attachment = NoteAttachment(
        note=note,
        original_name=original_name,
        stored_name=stored_name,
        content_type=uploaded_file.mimetype or 'application/octet-stream',
        size=len(file_data),
        data=file_data,
    )
    db.session.add(attachment)
    db.session.commit()
    return jsonify(attachment.to_dict()), 201


@note_bp.route('/attachments/<int:attachment_id>', methods=['GET'])
@login_required
def download_attachment(user, attachment_id):
    attachment = NoteAttachment.query.join(Note).filter(
        NoteAttachment.id == attachment_id,
        Note.user_id == user.id,
    ).first_or_404()
    if attachment.data is None:
        return jsonify({'error': 'This attachment is no longer available'}), 410
    return send_file(
        BytesIO(attachment.data),
        mimetype=attachment.content_type,
        as_attachment=False,
        download_name=attachment.original_name,
    )


@note_bp.route('/attachments/<int:attachment_id>', methods=['DELETE'])
@login_required
def delete_attachment(user, attachment_id):
    attachment = NoteAttachment.query.join(Note).filter(
        NoteAttachment.id == attachment_id,
        Note.user_id == user.id,
    ).first_or_404()
    db.session.delete(attachment)
    db.session.commit()
    return '', 204

@note_bp.route('/translate', methods=['POST'])
@login_required
def translate(_user):
    """Translate a note title and content into the selected language."""
    data = request.get_json(silent=True) or {}
    title = data.get('title', '')
    content = data.get('content', '')
    target_language = data.get('target_language', '')

    if not isinstance(title, str) or not isinstance(content, str):
        return jsonify({'error': 'Title and content must be text'}), 400
    if target_language not in SUPPORTED_LANGUAGES:
        return jsonify({'error': 'Please select a supported target language'}), 400
    if not title.strip() and not content.strip():
        return jsonify({'error': 'Please enter a title or content to translate'}), 400

    try:
        return jsonify(translate_note(title, content, target_language))
    except Exception as error:
        return jsonify({'error': str(error)}), 502

@note_bp.route('/notes', methods=['GET'])
@login_required
def get_notes(user):
    """Get all notes, ordered by most recently updated"""
    notes = Note.query.filter_by(user_id=user.id).order_by(Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
@login_required
def create_note(user):
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        note = Note(title=data['title'], content=data['content'], user_id=user.id)
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
@login_required
def get_note(user, note_id):
    """Get a specific note by ID"""
    note = Note.query.filter_by(id=note_id, user_id=user.id).first_or_404()
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(user, note_id):
    """Update a specific note"""
    try:
        note = Note.query.filter_by(id=note_id, user_id=user.id).first_or_404()
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(user, note_id):
    """Delete a specific note"""
    try:
        note = Note.query.filter_by(id=note_id, user_id=user.id).first_or_404()
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
@login_required
def search_notes(user):
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        Note.user_id == user.id,
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])

