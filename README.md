# Markdown Merge Application

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Available-brightgreen)](https://md-merge.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-18.0%2B-blue)](https://reactjs.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-lightgrey)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A sophisticated web application that intelligently processes ZIP files containing Markdown documents. The application automatically merges large collections of Markdown files, removes metadata, monitors word counts, and provides real-time progress tracking through an intuitive web interface.

## Live Demo

**Frontend**: [https://md-merge.vercel.app/](https://md-merge.vercel.app/)

> **Note**: The live demo currently shows the frontend interface. For full functionality including file processing, you'll need to run the backend locally (see [Local Development](#-local-development) section).

## Features

### Core Functionality
- **Intelligent File Processing**: Automatically handles ZIP files containing Markdown documents
- **Smart Merging Logic**: 
  - ≤50 files: Returns original files unchanged
  - \>50 files: Merges into batches of 49 files each
- **Metadata Removal**: Strips YAML frontmatter from all Markdown files
- **Word Count Monitoring**: Adds `_OVER50000WORDS` suffix to files exceeding 50,000 words
- **Real-time Progress**: Server-Sent Events (SSE) provide live processing updates

### User Experience
- **Progress Visualization**: Real-time progress bar with file count updates
- **Automatic Downloads**: Processed files download automatically upon completion
- **Manual Download Fallback**: Backup download link for reliability
- **Comprehensive Error Handling**: User-friendly error messages and validation

### Technical Features
- **Robust Architecture**: Separate frontend and backend for scalability
- **Cross-Origin Support**: CORS-enabled for flexible deployment
- **Session Management**: Unique session tracking for concurrent users
- **Memory Efficient**: Streaming file processing with temporary storage
- **Comprehensive Testing**: Full test suite covering edge cases

## Architecture

### Frontend (React)
- **Framework**: React 18 with hooks for state management
- **Styling**: Modern CSS with responsive design
- **Real-time Updates**: EventSource API for SSE communication
- **File Handling**: Modern File API with drag-and-drop support
- **Deployment**: Vercel for global CDN and automatic deployments

### Backend (Flask)
- **Framework**: Flask with modular endpoint design
- **File Processing**: Comprehensive ZIP and Markdown handling
- **Progress Tracking**: Server-Sent Events for real-time updates
- **Session Management**: UUID-based session tracking
- **Error Handling**: Robust validation and error responses

### Data Flow
```
User Upload → ZIP Validation → File Extraction → Markdown Processing → 
Metadata Removal → Smart Merging → Word Count Analysis → ZIP Creation → 
Automated Download
```

## Technology Stack

### Frontend
- **React** - Component-based UI framework
- **Modern JavaScript** - ES6+ features and async/await
- **CSS3** - Responsive design with Flexbox/Grid
- **EventSource API** - Real-time server communication

### Backend
- **Python 3.8+** - Core programming language
- **Flask** - Lightweight web framework
- **Flask-CORS** - Cross-origin resource sharing
- **zipfile** - ZIP archive processing
- **tempfile** - Secure temporary file handling

### Development & Testing
- **pytest** - Comprehensive testing framework
- **Vercel** - Frontend hosting and deployment
- **Git** - Version control and collaboration

## Requirements

### System Requirements
- Python 3.8 or higher
- Node.js 16.0 or higher (for frontend development)
- Modern web browser with ES6+ support

### Python Dependencies
```
Flask>=2.0.1
Flask-CORS>=3.0.10
pytest>=7.0.0
```

### Browser Compatibility
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## Local Development

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Yuvraj-Sandhu/MD-merge
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask backend**
   ```bash
   python app.py
   ```
   
   The backend will be available at `http://localhost:5000`

### Frontend Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:5173`

## Testing

The application includes comprehensive unit tests covering all major functionality and edge cases.

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest test_app.py

# Run tests with coverage
pytest --cov=app
```

### Test Coverage

Our test suite covers:

- **File Upload Validation**: ZIP format validation and error handling
- **Processing Logic**: Different file count scenarios (0, <50, =50, >50)
- **Metadata Removal**: YAML frontmatter stripping
- **Word Count Analysis**: Large file detection and warnings
- **Edge Cases**: Empty files, nested directories, invalid archives
- **Error Handling**: Malformed ZIP files and invalid requests

### Test Cases

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| `test_zero_md_files` | ZIP with no Markdown files | Returns empty ZIP |
| `test_less_than_50_files` | ZIP with <50 Markdown files | Returns original files |
| `test_exactly_50_files` | ZIP with exactly 50 files | Returns original files |
| `test_more_than_50_files` | ZIP with >50 files | Returns merged files |
| `test_metadata_removed` | Files with YAML frontmatter | Metadata stripped |
| `test_word_count_warning` | Files with >50k words | Filename warning added |
| `test_invalid_zip` | Malformed ZIP file | Returns 400 error |
| `test_nested_directories` | Complex directory structure | All files processed |
| `test_empty_content` | Empty Markdown files | Handles gracefully |
| `test_upload_non_zip` | Non-ZIP file upload | Returns validation error |

## Project Structure

```
MD-merge/
│
├── backend/                  # Backend Directory
│   ├── app.py                # Flask backend application
│   ├── test_app.py           # Comprehensive test suite
│   └── requirements.txt      # Python dependencies
│
├── public/
│
├── src/
│   ├── App.jsx          # Main React component
│   └── App.css          # Styling
│
├── package.json         # Frontend dependencies
│
└── README.md            # This file
```

## API Documentation

### Endpoints

#### `POST /upload/<session_id>`

Upload and process a ZIP file containing Markdown documents.

**Parameters:**
- `session_id` (string): Unique session identifier for progress tracking

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: ZIP file in 'file' field

**Response:**
- Success (200): Processed ZIP file download
- Error (400): JSON error message

**Example:**
```bash
curl -X POST \
  -F "file=@documents.zip" \
  http://localhost:5000/upload/123e4567-e89b-12d3-a456-426614174000
```

#### `GET /progress/<session_id>`

Get real-time progress updates via Server-Sent Events.

**Parameters:**
- `session_id` (string): Session identifier to track

**Response:**
- Content-Type: text/event-stream
- Data: JSON progress updates

**Example Response:**
```
data: {"total_files": 100, "current_index": 1, "done": false}
data: {"total_files": 100, "current_index": 2, "done": false}
data: {"total_files": 100, "current_index": 100, "done": true}
```

## Usage Examples

### Basic Usage

1. **Visit the application**: Navigate to the hosted frontend
2. **Upload a ZIP file**: Drag and drop or click to select a ZIP file containing Markdown documents
3. **Monitor progress**: Watch the real-time progress bar during processing
4. **Download results**: Processed files download automatically

### Processing Scenarios

#### Small Collection (≤50 files)
```
Input: documents.zip (30 .md files)
Output: merged_files.zip (30 .md files)
Processing: Individual files returned unchanged
```

#### Large Collection (>50 files)
```
Input: large_docs.zip (150 .md files)
Output: merged_files.zip (4 merged files)
Processing: 
- merged_part1.md (49 files)
- merged_part2.md (49 files)
- merged_part3.md (49 files)
- merged_part4.md (3 files)
```

#### High Word Count Warning
```
Input: verbose_docs.zip (100 files, 75,000 words total)
Output: merged_files.zip
Processing:
- merged_part1_OVER50000WORDS.md (49 files, 60,000 words)
- merged_part2.md (49 files, 15,000 words)
- merged_part3.md (2 files, minimal content)
```

## Error Handling

The application provides comprehensive error handling for various scenarios:

### Client-Side Errors
- **No file selected**: Clear validation message
- **Invalid file type**: File extension validation
- **Upload failure**: Network error handling
- **Connection issues**: Automatic retry logic

### Server-Side Errors
- **Invalid ZIP format**: Malformed archive detection
- **Processing errors**: Graceful degradation
- **Memory issues**: Efficient streaming processing
- **Session management**: Automatic cleanup

### Error Response Format
```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": "Additional technical details"
}
```

## Security Considerations

### File Upload Security
- **File type validation**: Only ZIP files accepted
- **Size limits**: Configurable upload size restrictions
- **Temporary storage**: Secure cleanup of temporary files
- **Path traversal protection**: Safe file extraction

### Session Management
- **UUID generation**: Cryptographically secure session IDs
- **Session isolation**: Separate processing contexts
- **Automatic cleanup**: Memory leak prevention
- **Resource limits**: Processing time and memory bounds

## Additional Resources

### Related Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/learn)
- [Server-Sent Events Guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---