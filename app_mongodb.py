import os
import html
import re
import secrets
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
import uuid
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
from bson.errors import InvalidId
from functools import wraps

# Load environment variables at the top
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use defaults

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

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'quiz_partner')

# Global MongoDB client
mongo_client = None
mongo_db = None

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_mongodb():
    """Initialize MongoDB connection"""
    global mongo_client, mongo_db
    try:
        print(f"🔗 Connecting to MongoDB...")
        print(f"📍 URI: {MONGODB_URI[:60]}...")
        print(f"📂 Database: {DATABASE_NAME}")
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        # Test connection
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[DATABASE_NAME]
        
        # Create indexes for better performance
        create_indexes()
        
        print("✅ MongoDB connection established!")
        return True
    except ConnectionFailure as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("💡 Make sure MongoDB is running and connection string is correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected error connecting to MongoDB: {e}")
        return False

def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Modules collection indexes
        mongo_db.modules.create_index("name", unique=True)
        mongo_db.modules.create_index("created_at")
        
        # Questions collection indexes
        mongo_db.questions.create_index("module_id")
        mongo_db.questions.create_index("name")
        mongo_db.questions.create_index("created_at")
        mongo_db.questions.create_index([("module_id", 1), ("created_at", -1)])
        
        print("📊 Database indexes created successfully!")
    except Exception as e:
        print(f"⚠️ Warning: Could not create indexes: {e}")

def get_db():
    """Get MongoDB database instance"""
    global mongo_db
    if mongo_db is None:
        if not init_mongodb():
            raise Exception("Could not connect to MongoDB")
    return mongo_db

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

def is_valid_object_id(id_string):
    """Check if string is a valid MongoDB ObjectId"""
    try:
        ObjectId(id_string)
        return True
    except (InvalidId, TypeError):
        return False

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
    try:
        db = get_db()
        
        # Get all modules
        modules = list(db.modules.find().sort("created_at", -1))
        
        # Get all questions with module info
        pipeline = [
            {
                "$lookup": {
                    "from": "modules",
                    "localField": "module_id",
                    "foreignField": "_id",
                    "as": "module_info"
                }
            },
            {
                "$unwind": "$module_info"
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$limit": 12
            }
        ]
        
        all_questions = list(db.questions.aggregate(pipeline))
        
        return render_template('index.html', modules=modules, all_questions=all_questions)
        
    except Exception as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('index.html', modules=[], all_questions=[])

@app.route('/add_module', methods=['POST'])
@login_required
def add_module():
    """Add a new module."""
    try:
        module_name = sanitize_input(request.form.get('module_name', '').strip())
        
        if not module_name:
            flash('Module name is required!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        
        # Create module document
        module_doc = {
            'name': module_name,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            result = db.modules.insert_one(module_doc)
            flash(f'Module "{module_name}" created successfully!', 'success')
        except DuplicateKeyError:
            flash(f'Module "{module_name}" already exists!', 'error')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error creating module: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete_module/<module_id>')
@login_required
def delete_module(module_id):
    """Delete a module and all its questions."""
    try:
        if not is_valid_object_id(module_id):
            flash('Invalid module ID!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        module_object_id = ObjectId(module_id)
        
        # Get all questions for this module to delete their image files
        questions = list(db.questions.find({"module_id": module_object_id}))
        
        # Delete image files
        for question in questions:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], question['image_path'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete all questions in this module
        db.questions.delete_many({"module_id": module_object_id})
        
        # Delete the module
        result = db.modules.delete_one({"_id": module_object_id})
        
        if result.deleted_count > 0:
            flash('Module deleted successfully!', 'success')
        else:
            flash('Module not found!', 'error')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error deleting module: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/module/<module_id>')
@login_required
def module_view(module_id):
    """Show all questions in a module (image only)."""
    try:
        if not is_valid_object_id(module_id):
            flash('Invalid module ID!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        module_object_id = ObjectId(module_id)
        
        # Get module
        module = db.modules.find_one({"_id": module_object_id})
        if not module:
            flash('Module not found!', 'error')
            return redirect(url_for('dashboard'))
        
        # Get questions
        questions = list(db.questions.find({"module_id": module_object_id}).sort("created_at", -1))
        
        return render_template('module.html', module=module, questions=questions)
        
    except Exception as e:
        flash(f'Error loading module: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/module/<module_id>/add', methods=['GET', 'POST'])
@login_required
def add_question(module_id):
    """Add a new question to a module."""
    try:
        if not is_valid_object_id(module_id):
            flash('Invalid module ID!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        module_object_id = ObjectId(module_id)
        
        # Get module
        module = db.modules.find_one({"_id": module_object_id})
        if not module:
            flash('Module not found!', 'error')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            question_name = sanitize_input(request.form.get('question_name', '').strip())
            answer = sanitize_input(request.form.get('answer', '').strip(), max_length=5000)
            
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
                    # Create question document
                    question_doc = {
                        'module_id': module_object_id,
                        'name': question_name,
                        'image_path': filename,
                        'answer': answer,
                        'created_at': datetime.utcnow().isoformat()
                    }
                    
                    # Save question to database
                    db.questions.insert_one(question_doc)
                    flash('Question added successfully!', 'success')
                    return redirect(url_for('module_view', module_id=module_id))
                    
                except Exception as e:
                    # Remove uploaded file if database save fails
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    flash(f'Database error: {str(e)}', 'error')
            else:
                flash('Invalid file type or corrupted image! Please upload a valid image file.', 'error')
        
        return render_template('add_question.html', module=module)
        
    except Exception as e:
        flash(f'Error adding question: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete_question/<question_id>')
@login_required
def delete_question(question_id):
    """Delete a question."""
    try:
        if not is_valid_object_id(question_id):
            flash('Invalid question ID!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        question_object_id = ObjectId(question_id)
        
        # Get question
        question = db.questions.find_one({"_id": question_object_id})
        if not question:
            flash('Question not found!', 'error')
            return redirect(url_for('dashboard'))
        
        module_id = str(question['module_id'])
        
        # Delete image file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], question['image_path'])
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Delete question from database
        result = db.questions.delete_one({"_id": question_object_id})
        
        if result.deleted_count > 0:
            flash('Question deleted successfully!', 'success')
        else:
            flash('Question not found!', 'error')
        
        return redirect(url_for('module_view', module_id=module_id))
        
    except Exception as e:
        flash(f'Error deleting question: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/all-questions')
@login_required
def all_questions():
    """Show all questions from all modules."""
    try:
        db = get_db()
        
        # Get search query
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            # Search in questions with module info
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"name": {"$regex": search_query, "$options": "i"}},
                            {"answer": {"$regex": search_query, "$options": "i"}}
                        ]
                    }
                },
                {
                    "$lookup": {
                        "from": "modules",
                        "localField": "module_id",
                        "foreignField": "_id",
                        "as": "module_info"
                    }
                },
                {
                    "$unwind": "$module_info"
                },
                {
                    "$sort": {"created_at": -1}
                }
            ]
        else:
            # Get all questions with module info
            pipeline = [
                {
                    "$lookup": {
                        "from": "modules",
                        "localField": "module_id",
                        "foreignField": "_id",
                        "as": "module_info"
                    }
                },
                {
                    "$unwind": "$module_info"
                },
                {
                    "$sort": {"created_at": -1}
                }
            ]
        
        questions = list(db.questions.aggregate(pipeline))
        
        return render_template('all_questions.html', questions=questions, search_query=search_query)
        
    except Exception as e:
        flash(f'Error loading questions: {str(e)}', 'error')
        return render_template('all_questions.html', questions=[], search_query='')

@app.route('/question/<question_id>/answer')
@login_required
def question_answer(question_id):
    """Show single question with its answer."""
    try:
        if not is_valid_object_id(question_id):
            flash('Invalid question ID!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        question_object_id = ObjectId(question_id)
        
        # Get question with module info
        pipeline = [
            {"$match": {"_id": question_object_id}},
            {
                "$lookup": {
                    "from": "modules",
                    "localField": "module_id",
                    "foreignField": "_id",
                    "as": "module_info"
                }
            },
            {
                "$unwind": "$module_info"
            }
        ]
        
        questions = list(db.questions.aggregate(pipeline))
        if not questions:
            flash('Question not found!', 'error')
            return redirect(url_for('dashboard'))
        
        question = questions[0]
        return render_template('question_answer.html', question=question)
        
    except Exception as e:
        flash(f'Error loading question: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/module/<module_id>/answers')
@login_required
def answers_view(module_id):
    """Show Q&A view with images and formatted answers."""
    try:
        if not is_valid_object_id(module_id):
            flash('Invalid module ID!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        module_object_id = ObjectId(module_id)
        
        # Get module
        module = db.modules.find_one({"_id": module_object_id})
        if not module:
            flash('Module not found!', 'error')
            return redirect(url_for('dashboard'))
        
        # Get search query
        search_query = request.args.get('search', '').strip()
        
        # Build query
        query = {"module_id": module_object_id}
        if search_query:
            query["$or"] = [
                {"name": {"$regex": search_query, "$options": "i"}},
                {"answer": {"$regex": search_query, "$options": "i"}}
            ]
        
        questions = list(db.questions.find(query).sort("created_at", -1))
        
        return render_template('answers.html', module=module, questions=questions, search_query=search_query)
        
    except Exception as e:
        flash(f'Error loading answers: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/question/<question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_answer(question_id):
    """Edit the answer for a question."""
    try:
        if not is_valid_object_id(question_id):
            flash('Invalid question ID!', 'error')
            return redirect(url_for('dashboard'))
        
        db = get_db()
        question_object_id = ObjectId(question_id)
        
        # Get question with module info
        pipeline = [
            {"$match": {"_id": question_object_id}},
            {
                "$lookup": {
                    "from": "modules",
                    "localField": "module_id",
                    "foreignField": "_id",
                    "as": "module_info"
                }
            },
            {
                "$unwind": "$module_info"
            }
        ]
        
        questions = list(db.questions.aggregate(pipeline))
        if not questions:
            flash('Question not found!', 'error')
            return redirect(url_for('dashboard'))
        
        question = questions[0]
        
        if request.method == 'POST':
            new_answer = sanitize_input(request.form.get('answer', '').strip(), max_length=5000)
            question_name = sanitize_input(request.form.get('question_name', '').strip())
            
            if not new_answer:
                flash('Answer cannot be empty!', 'error')
                return render_template('edit_answer.html', question=question)
            
            if not question_name:
                question_name = 'Untitled Question'
            
            # Update the question answer and name
            result = db.questions.update_one(
                {"_id": question_object_id},
                {
                    "$set": {
                        "answer": new_answer,
                        "name": question_name,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            if result.modified_count > 0:
                flash('Answer updated successfully!', 'success')
                return redirect(url_for('question_answer', question_id=question_id))
            else:
                flash('No changes were made!', 'info')
        
        return render_template('edit_answer.html', question=question)
        
    except Exception as e:
        flash(f'Error editing answer: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        # Simple database ping
        db.command('ping')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500

@app.context_processor
def inject_auth():
    """Inject authentication status into all templates"""
    return dict(is_logged_in=is_logged_in())

if __name__ == '__main__':
    # Initialize MongoDB connection
    if not init_mongodb():
        print("❌ Could not connect to MongoDB. Please check your connection string.")
        print("💡 Set MONGODB_URI environment variable with your MongoDB Atlas connection string")
        exit(1)
    
    # Environment variables are already loaded at the top
    
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    port = int(os.environ.get('PORT', '5001'))
    
    print(f"🚀 Starting Quiz Partner with MongoDB backend...")
    print(f"🌐 Server will run on http://0.0.0.0:{port}")
    print(f"🗄️ Database: {DATABASE_NAME}")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)