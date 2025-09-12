import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect('quiz_platform.db')
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
    conn = sqlite3.connect('quiz_platform.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def dashboard():
    """Dashboard page showing all modules."""
    conn = get_db_connection()
    modules = conn.execute(
        'SELECT * FROM modules ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return render_template('index.html', modules=modules)

@app.route('/add_module', methods=['POST'])
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
        question_name = request.form.get('question_name', '').strip()
        answer = request.form.get('answer', '').strip()
        
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
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Save question to database
            conn.execute(
                'INSERT INTO questions (module_id, name, image_path, answer) VALUES (?, ?, ?, ?)',
                (module_id, question_name, filename, answer)
            )
            conn.commit()
            conn.close()
            
            flash('Question added successfully!', 'success')
            return redirect(url_for('module_view', module_id=module_id))
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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
