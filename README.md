# 🎯 Quiz Partner

<div align="center">

![Quiz Partner](https://img.shields.io/badge/Quiz-Partner-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green?style=for-the-badge&logo=flask)
![Python](https://img.shields.io/badge/Python-3.13.7-yellow?style=for-the-badge&logo=python)
![SQLite](https://img.shields.io/badge/SQLite-Database-orange?style=for-the-badge&logo=sqlite)

**A modern, professional quiz management system built with Flask**

*Create, manage, and organize quiz modules with an intuitive drag-and-drop interface*

</div>

---

## ✨ Features

### 🎨 **Professional UI**
- Modern gradient design with smooth animations
- Responsive layout that works on all devices
- Clean, intuitive user interface
- Professional typography with Inter font

### 📚 **Module Management**
- Create and organize quiz modules
- Dashboard overview of all modules
- Easy navigation between modules

### 🖼️ **Advanced Question Creation**
- **Multiple Upload Methods:**
  - 🖱️ Drag & Drop images directly
  - 📋 Paste images from clipboard (Ctrl+V)
  - 📁 Traditional file browser
- **Enhanced Features:**
  - Live image preview before submission
  - Question naming system
  - Support for multiple image formats
  - Automatic file management with UUID

### 🔍 **Viewing & Search**
- **Question View:** Clean image-only display
- **Individual Answers:** Click "View Answer" for each question
- **Q&A Overview:** Complete questions and answers view
- **Smart Search:** Find specific content in answers
- **Responsive Navigation:** Easy switching between views

### 🛡️ **File Handling**
- Secure file upload with validation
- Automatic image optimization
- UUID-based naming for uniqueness
- Support: PNG, JPG, JPEG, GIF, BMP, WebP

---

## 🚀 Quick Start

### Prerequisites
- Python 3.7+ installed
- Git (optional, for cloning)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Quiz-partner
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   # Linux/Mac
   source .venv/bin/activate
   
   # Windows
   .venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5000
   ```

---

## 📖 Usage Guide

### 🏠 **Dashboard**
- View all your quiz modules
- Create new modules with descriptive names
- Quick access to module management

### ➕ **Adding Questions**
1. Select a module from dashboard
2. Click "Add Question" 
3. **Upload Methods:**
   - **Drag & Drop:** Simply drag image files onto the upload area
   - **Paste:** Copy image and press Ctrl+V (Cmd+V on Mac)
   - **Browse:** Click to select files traditionally
4. Enter question name and answer
5. Preview your image before submitting

### 👀 **Viewing Content**
- **Questions Only:** Clean image gallery view
- **Individual Answers:** Click "View Answer" on any question
- **Complete Q&A:** View all questions and answers together
- **Search:** Use search bar to find specific content

---

## 🗂️ Project Structure

```
Quiz-partner/
├── 📱 app.py                    # Main Flask application
├── 🗃️ quiz.db                  # SQLite database
├── 📁 uploads/                 # User uploaded images
├── 🎨 static/
│   └── styles.css             # Professional UI styling
├── 📄 templates/               # HTML templates
│   ├── base.html              # Base template with navigation
│   ├── dashboard.html         # Module overview
│   ├── module.html            # Question gallery view
│   ├── add_question.html      # Enhanced upload form
│   ├── answers.html           # Q&A overview with search
│   └── question_answer.html   # Individual question view
├── 📋 requirements.txt         # Python dependencies
├── 📖 README.md               # This file
└── 🚫 .gitignore              # Git ignore rules
```

---

## 🛠️ Technical Details

### **Database Schema**
```sql
modules:
├── id (INTEGER PRIMARY KEY)
├── name (TEXT NOT NULL)
└── created_at (DATETIME DEFAULT CURRENT_TIMESTAMP)

questions:
├── id (INTEGER PRIMARY KEY)
├── module_id (INTEGER FOREIGN KEY)
├── name (TEXT NOT NULL)
├── image_path (TEXT NOT NULL)
├── answer (TEXT NOT NULL)
└── created_at (DATETIME DEFAULT CURRENT_TIMESTAMP)
```

### **API Routes**
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard with all modules |
| `/module/<id>` | GET | View questions (images only) |
| `/module/<id>/add` | GET/POST | Add new question form |
| `/module/<id>/answers` | GET | Q&A view with search |
| `/question/<id>/answer` | GET | Individual question answer |
| `/uploads/<filename>` | GET | Serve uploaded images |

### **Technology Stack**
- **Backend:** Flask 3.0.0, Werkzeug 3.0.1
- **Database:** SQLite with automatic schema management
- **Frontend:** HTML5, Modern CSS3, Vanilla JavaScript
- **File Upload:** Secure handling with validation
- **Styling:** Professional gradients, animations, responsive design

---

## 🎨 UI/UX Features

### **Modern Design Elements**
- Gradient backgrounds and hover effects
- Smooth CSS animations and transitions
- Professional color scheme
- Responsive grid layouts

### **Interactive Elements**
- Drag & drop visual feedback
- Live image previews
- Animated buttons and cards
- Search highlighting

### **Accessibility**
- Keyboard navigation support
- Screen reader friendly
- High contrast text
- Mobile-responsive design

---

## 🔧 Configuration

### **Environment Setup**
```bash
# Development
export FLASK_ENV=development
export FLASK_DEBUG=1

# Production
export FLASK_ENV=production
export FLASK_DEBUG=0
```

### **File Upload Settings**
- Maximum file size: 16MB
- Allowed extensions: PNG, JPG, JPEG, GIF, BMP, WebP
- Upload directory: `uploads/`
- Automatic UUID naming

---

## 📝 Development

### **Adding New Features**
1. Database changes in `app.py`
2. Route handlers for new functionality
3. HTML templates in `templates/`
4. Styling updates in `static/styles.css`

### **File Upload Security**
- File type validation
- Size limits enforced
- Safe filename generation
- Secure file storage

### **Database Management**
```python
# Initialize database
python -c "from app import init_db; init_db()"

# Reset database (caution: loses all data)
rm quiz.db
python app.py
```

---

## 🧪 Testing

### **Manual Testing**
1. Create modules with various names
2. Test all upload methods (drag/drop, paste, browse)
3. Verify image display and answer storage
4. Test search functionality
5. Check responsive design on different screen sizes

### **File Upload Testing**
```bash
# Test different file formats
curl -X POST -F "file=@test.png" http://localhost:5000/module/1/add
curl -X POST -F "file=@test.jpg" http://localhost:5000/module/1/add
```

---

## 🚀 Deployment

### **Local Development**
```bash
python app.py
# Access at http://localhost:5000
```

### **Production Deployment**
1. Set environment variables
2. Use a production WSGI server (gunicorn)
3. Configure reverse proxy (nginx)
4. Set up SSL certificates

```bash
# Example with gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🔒 Security Considerations

### **File Upload Security**
- Whitelist allowed file extensions
- Validate file headers (magic numbers)
- Limit file sizes
- Use UUID for file names
- Store files outside web root when possible

### **Database Security**
- Use parameterized queries (already implemented)
- Regular backups
- Consider encryption for sensitive data

### **Web Security**
- Change default secret key in production
- Use HTTPS in production
- Implement CSRF protection
- Add rate limiting for uploads

---

## 🛠️ Troubleshooting

### **Common Issues**

#### **Installation Problems**
```bash
# Python version issues
python --version  # Should be 3.7+

# Virtual environment activation
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

#### **File Upload Issues**
- Check upload directory permissions
- Verify file size limits
- Ensure supported file format

#### **Database Issues**
```bash
# Reset database (loses all data)
rm quiz.db
python app.py
```

#### **Port Issues**
```bash
# Change port if 5000 is in use
python app.py --port 8080
```

---

## 📊 Performance Tips

### **Image Optimization**
- Compress images before upload
- Consider implementing automatic resize
- Use CDN for production

### **Database Optimization**
- Add indexes for frequently queried columns
- Regular database maintenance
- Consider pagination for large datasets

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Development Guidelines**
- Follow PEP 8 for Python code
- Write clear commit messages
- Add comments for complex logic
- Test thoroughly before submitting

---

## 📚 Resources

### **Documentation**
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLite Documentation](https://sqlite.org/docs.html)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)

### **Related Projects**
- Flask-Upload for advanced file handling
- Flask-WTF for form validation
- Flask-SQLAlchemy for ORM

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- Flask community for the excellent framework
- Contributors and testers
- Modern web design inspiration from various sources

---

<div align="center">

**Built with ❤️ using Flask and modern web technologies**

*Happy Quiz Creating! 🎯*

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com)
[![Flask](https://img.shields.io/badge/Powered%20by-Flask-green?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)

</div>