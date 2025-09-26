import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
import uuid
from functools import wraps
import secrets
import html
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Authentication credentials
ADMIN_USERNAME = "killer"
ADMIN_PASSWORD = "cheater"

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file):
    """Validate that the uploaded file is actually an image."""
    try:
        # Read the first few bytes to check file signature
        file.seek(0)
        header = file.read(32)
        file.seek(0)  # Reset file pointer
        
        # Check common image file signatures
        image_signatures = [
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'\xff\xd8\xff',        # JPEG
            b'GIF87a',              # GIF87a
            b'GIF89a',              # GIF89a
            b'BM',                  # BMP
            b'RIFF',                # WebP (part of RIFF)
        ]
        
        for signature in image_signatures:
            if header.startswith(signature):
                return True
                
        # Special check for WebP (RIFF + WEBP)
        if header.startswith(b'RIFF') and b'WEBP' in header[:16]:
            return True
            
        return False
    except Exception:
        return False

def sanitize_input(text, max_length=1000):
    """Sanitize user input to prevent XSS and limit length."""
    if not text:
        return ""
    
    # Remove any HTML tags and escape special characters
    text = html.escape(text.strip())
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'javascript:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'<script',
        r'</script>',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_logged_in():
    """Check if user is logged in"""
    return session.get('logged_in', False)

def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect('Crime_platform.db')
    cursor = conn.cursor()
    
    # Create modules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            name TEXT NOT NULL DEFAULT 'Untitled Question',
            image_path TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (module_id) REFERENCES modules (id) ON DELETE CASCADE
        )
    ''')
    
    # Add name column to existing questions table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE questions ADD COLUMN name TEXT NOT NULL DEFAULT "Untitled Question"')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect('Crime_platform.db', timeout=20.0)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Welcome! You have been logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Dashboard page showing all modules."""
    conn = get_db_connection()
    modules = conn.execute(
        'SELECT * FROM modules ORDER BY created_at DESC'
    ).fetchall()
    
    # Get all questions for the dashboard display
    all_questions = conn.execute('''
        SELECT q.*, m.name as module_name, m.id as module_id 
        FROM questions q 
        JOIN modules m ON q.module_id = m.id 
        ORDER BY q.created_at DESC
    ''').fetchall()
    
    conn.close()
    return render_template('index.html', modules=modules, all_questions=all_questions)

@app.route('/add_module', methods=['POST'])
@login_required
def add_module():
    """Add a new module."""
    module_name = request.form.get('module_name', '').strip()
    
    if not module_name:
        flash('Module name is required!', 'error')
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO modules (name) VALUES (?)', (module_name,))
        conn.commit()
        flash(f'Module "{module_name}" created successfully!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Module "{module_name}" already exists!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/delete_module/<int:module_id>')
def delete_module(module_id):
    """Delete a module and all its questions."""
    conn = get_db_connection()
    
    # Get all questions for this module to delete their image files
    questions = conn.execute(
        'SELECT image_path FROM questions WHERE module_id = ?', (module_id,)
    ).fetchall()
    
    # Delete image files
    for question in questions:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], question['image_path'])
        if os.path.exists(image_path):
            os.remove(image_path)
    
    # Delete module (CASCADE will delete questions)
    conn.execute('DELETE FROM modules WHERE id = ?', (module_id,))
    conn.commit()
    conn.close()
    
    flash('Module deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/module/<int:module_id>')
def module_view(module_id):
    """Show all questions in a module (image only)."""
    conn = get_db_connection()
    
    module = conn.execute(
        'SELECT * FROM modules WHERE id = ?', (module_id,)
    ).fetchone()
    
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('dashboard'))
    
    questions = conn.execute(
        'SELECT * FROM questions WHERE module_id = ? ORDER BY created_at DESC',
        (module_id,)
    ).fetchall()
    
    conn.close()
    return render_template('module.html', module=module, questions=questions)

@app.route('/module/<int:module_id>/add', methods=['GET', 'POST'])
def add_question(module_id):
    """Add a new question to a module."""
    conn = get_db_connection()
    
    module = conn.execute(
        'SELECT * FROM modules WHERE id = ?', (module_id,)
    ).fetchone()
    
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        question_name = sanitize_input(request.form.get('question_name', ''), 200)
        answer = sanitize_input(request.form.get('answer', ''), 5000)
        
        if not question_name:
            question_name = 'Untitled Question'
        
        if 'image' not in request.files:
            flash('No image file selected!', 'error')
            return render_template('add_question.html', module=module)
        
        file = request.files['image']
        
        if file.filename == '':
            flash('No image file selected!', 'error')
            return render_template('add_question.html', module=module)
        
        if not answer:
            flash('Answer is required!', 'error')
            return render_template('add_question.html', module=module)
        
        if file and allowed_file(file.filename) and validate_image(file):
            # Additional file size check
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                flash(f'File too large! Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.', 'error')
                return render_template('add_question.html', module=module)
            
            # Generate unique filename
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                # Save question to database
                conn.execute(
                    'INSERT INTO questions (module_id, name, image_path, answer) VALUES (?, ?, ?, ?)',
                    (module_id, question_name, filename, answer)
                )
                conn.commit()
                flash('Question added successfully!', 'success')
                return redirect(url_for('module_view', module_id=module_id))
            except sqlite3.Error as e:
                # Remove uploaded file if database save fails
                if os.path.exists(file_path):
                    os.remove(file_path)
                flash(f'Database error: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Invalid file type! Please upload an image file.', 'error')
    
    conn.close()
    return render_template('add_question.html', module=module)

@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    """Delete a question."""
    conn = get_db_connection()
    
    question = conn.execute(
        'SELECT * FROM questions WHERE id = ?', (question_id,)
    ).fetchone()
    
    if question:
        module_id = question['module_id']
        
        # Delete image file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], question['image_path'])
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Delete question from database
        conn.execute('DELETE FROM questions WHERE id = ?', (question_id,))
        conn.commit()
        
        flash('Question deleted successfully!', 'success')
        conn.close()
        return redirect(url_for('module_view', module_id=module_id))
    
    conn.close()
    flash('Question not found!', 'error')
    return redirect(url_for('dashboard'))

@app.route('/all-questions')
def all_questions():
    """Show all questions from all modules."""
    conn = get_db_connection()
    
    # Get search query
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        questions = conn.execute('''
            SELECT q.*, m.name as module_name, m.id as module_id 
            FROM questions q 
            JOIN modules m ON q.module_id = m.id 
            WHERE q.name LIKE ? OR q.answer LIKE ? 
            ORDER BY q.created_at DESC
        ''', (f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        questions = conn.execute('''
            SELECT q.*, m.name as module_name, m.id as module_id 
            FROM questions q 
            JOIN modules m ON q.module_id = m.id 
            ORDER BY q.created_at DESC
        ''').fetchall()
    
    conn.close()
    return render_template('all_questions.html', questions=questions, search_query=search_query)

@app.route('/question/<int:question_id>/answer')
def question_answer(question_id):
    """Show single question with its answer."""
    conn = get_db_connection()
    
    question = conn.execute('''
        SELECT q.*, m.name as module_name, m.id as module_id 
        FROM questions q 
        JOIN modules m ON q.module_id = m.id 
        WHERE q.id = ?
    ''', (question_id,)).fetchone()
    
    if not question:
        flash('Question not found!', 'error')
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('question_answer.html', question=question)

@app.route('/module/<int:module_id>/answers')
def answers_view(module_id):
    """Show Q&A view with images and formatted answers."""
    conn = get_db_connection()
    
    module = conn.execute(
        'SELECT * FROM modules WHERE id = ?', (module_id,)
    ).fetchone()
    
    if not module:
        flash('Module not found!', 'error')
        return redirect(url_for('dashboard'))
    
    # Get search query
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        questions = conn.execute(
            'SELECT * FROM questions WHERE module_id = ? AND (name LIKE ? OR answer LIKE ?) ORDER BY created_at DESC',
            (module_id, f'%{search_query}%', f'%{search_query}%')
        ).fetchall()
    else:
        questions = conn.execute(
            'SELECT * FROM questions WHERE module_id = ? ORDER BY created_at DESC',
            (module_id,)
        ).fetchall()
    
    conn.close()
    return render_template('answers.html', module=module, questions=questions, search_query=search_query)

@app.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
def edit_answer(question_id):
    """Edit the answer for a question."""
    conn = get_db_connection()
    
    question = conn.execute('''
        SELECT q.*, m.name as module_name, m.id as module_id 
        FROM questions q 
        JOIN modules m ON q.module_id = m.id 
        WHERE q.id = ?
    ''', (question_id,)).fetchone()
    
    if not question:
        flash('Question not found!', 'error')
        conn.close()
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        new_answer = request.form.get('answer', '').strip()
        question_name = request.form.get('question_name', '').strip()
        
        if not new_answer:
            flash('Answer cannot be empty!', 'error')
            conn.close()
            return render_template('edit_answer.html', question=question)
        
        if not question_name:
            question_name = 'Untitled Question'
        
        # Update the question answer and name
        conn.execute(
            'UPDATE questions SET answer = ?, name = ? WHERE id = ?',
            (new_answer, question_name, question_id)
        )
        conn.commit()
        conn.close()
        
        flash('Answer updated successfully!', 'success')
        return redirect(url_for('question_answer', question_id=question_id))
    
    conn.close()
    return render_template('edit_answer.html', question=question)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.context_processor
def inject_auth():
    """Inject authentication status into all templates"""
    return dict(is_logged_in=is_logged_in())

if __name__ == '__main__':
    init_db()
    # Load environment variables
    from dotenv import load_dotenv
    try:
        load_dotenv()
    except ImportError:
        pass  # dotenv not available, use defaults
    
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    port = int(os.environ.get('PORT', '5001'))
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
