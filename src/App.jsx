/**
 *                React Frontend for Markdown Merge Application
 * ================================================================================================
 * 
 * A React component that provides a user interface for uploading ZIP files
 * containing Markdown documents, displaying real-time processing progress,
 * and automatically downloading the processed results.
 * 
 * Features:
 * - File upload with drag-and-drop interface
 * - Real-time progress tracking via Server-Sent Events (SSE)
 * - Automatic file download upon completion
 * - Comprehensive error handling and user feedback
 * - Responsive UI with loading states
 * 
 * Architecture:
 * - Uses React hooks for state management
 * - Communicates with Flask backend via REST API and SSE
 * - Handles file operations and blob downloads
 * - Provides immediate user feedback for all operations
 */

import { useState } from 'react'
import './App.css'

function App() {
  // ==========================================================================
  // STATE MANAGEMENT
  // ==========================================================================

  // File handling state
  // Stores the selected ZIP file from the file input
  const [selectedFile, setSelectedFile] = useState(null);
  // Upload process state
  const [uploading, setUploading] = useState(false);
  // Progress tracking state
  const [progress, setProgress] = useState(0);
  // Progress message showing current file count being processed
  const [progressMessage, setProgressMessage] = useState('');
  // Download state
  const [downloadUrl, setDownloadUrl] = useState('');
  // messages for success, errors and feedback
  const [message, setMessage] = useState('');

  // ==========================================================================
  // EVENT HANDLERS
  // ==========================================================================

  /**
   * Handle file selection from input element.
   * 
   * Triggered when user selects a file via the file input or drag-and-drop.
   * Resets all previous state to ensure clean UI state for new upload.
   * 
   * @param {Event} e - File input change event
   */
  const handleFileChange = (e) => {
    // Store the selected file
    setSelectedFile(e.target.files[0]);
    // Reset all previous store states
    setDownloadUrl('');
    setMessage('');
    setProgress(0);
    setProgressMessage('');
  };

  /**
   * Handle the complete upload and processing workflow.
   * 
   * This function orchestrates the entire file processing workflow:
   * 1. Validates file selection
   * 2. Generates unique session ID for tracking
   * 3. Establishes SSE connection for progress updates
   * 4. Uploads file to backend
   * 5. Handles response and initiates download
   * 6. Manages error states and cleanup
   * 
   * Uses modern browser APIs:
   * - crypto.randomUUID() for session management
   * - EventSource for real-time progress updates
   * - Fetch API for file upload
   * - Blob API for file download handling
   */
  const handleUpload = async () => {

    // ========================================================================
    // INPUT VALIDATION
    // ========================================================================
    
    // Ensure a file has been selected before proceeding
    if (!selectedFile) {
      setMessage('Please select a ZIP file first.');
      return;
    }

    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    // Generate unique session ID for this upload operation
    // This allows the backend to track progress for this specific request
    const sessionId = crypto.randomUUID();
    // Set initial upload state
    setUploading(true);
    setMessage('');
    setProgress(0);
    setProgressMessage('');
    setDownloadUrl('');

    // Prepare form data for multipart upload
    const formData = new FormData();
    formData.append('file', selectedFile);

    // ========================================================================
    // REAL TIME PROGRESS TRACKING
    // ========================================================================
    
    // Establish Server-Sent Events connection for real-time progress updates
    const eventSource = new EventSource(`http://localhost:5000/progress/${sessionId}`);

    /**
     * Handle incoming progress updates from the server.
     * 
     * The server sends JSON data with processing status:
     * - total_files: Total number of files to process
     * - current_index: Current file being processed
     * - done: Boolean indicating completion
     */
    eventSource.onmessage = (event) => {
      try {
        // Parse JSON data from server
        const data = JSON.parse(event.data);
        const { total_files, current_index, done } = data;

        // Update progress bar and message
        if (total_files > 0) {
          // Calculate percentage completion
          const percent = Math.floor((current_index / total_files) * 100);
          setProgress(percent);
          // Update progress message
          setProgressMessage(`Merging file ${current_index} of ${total_files}...`);
        }

        // Close SSE connection when processing is complete
        if (done) {
          eventSource.close();
        }
      } catch (err) {
        // Handle JSON or connection errors
        console.error('Error parsing SSE data:', err);
      }
    };

    // ========================================================================
    // FILE UPLOAD AND PROCESSING
    // ========================================================================
    
    try {
      // Send file to backend for processing
      const response = await fetch(`http://localhost:5000/upload/${sessionId}`, {
        method: 'POST',
        body: formData,
      });

      // Check if upload was success
      if (!response.ok) {
        throw new Error('Upload failed');
      }

      // ================================================================
      // DOWNLOAD HANDLING
      // ================================================================
      
      // Backend responds with processed ZIP file as binary data
      const blob = await response.blob();
      // Create downloadable URL from blob data
      const url = window.URL.createObjectURL(blob);
      setDownloadUrl(url);
      // Notify user of successfull processing
      setMessage('File processed successfully! Your download should start automatically.');

      // ================================================================
      // AUTOMATIC DOWNLOAD
      // ================================================================
      
      // Trigger download without user interaction
      const a = document.createElement('a');
      a.href = url;
      a.download = 'merged_files.zip';
      document.body.appendChild(a);
      a.click();
      a.remove();

    } catch (err) {
      // Displaying user firendly error handling message
      setMessage('Error processing file: ' + err.message);
    } finally {
      // Reset uploading state regardless of success or failure
      setUploading(false);
    }
  };

  return (
    <div className='app-container'>
      {/* Application Header */}
      <h1 className='app-title'>Markdown ZIP Merge</h1>

      <div className='upload-form'>
        {/* Form Header */}
        <span className="form-title">Upload your file</span>
        <p className="form-paragraph">Should be a zip file</p>

        {/* File input section */}
        <div className='file-input-container'>
          <span className="drop-title">Drop file here</span>
          or
          <input
            type="file"
            accept=".zip"                   // Restrict to zip files only
            onChange={handleFileChange}     // Handle file selection
            disabled={uploading}            // Disable during processing
            className='file-input'
          />
        </div>

        {/* Progress display only shown during upload */}
        {uploading && (
          <div className='progress-container'>
            {/* Progress bar */}
            <progress value={progress} max="100" />
            {/* Percentage display */}
            <div>{progress}%</div>
            {/* Progress message */}
            <p>{progressMessage}</p>
          </div>
        )}

        {/* Status Message */}
        {message && <p className='message'>{message}</p>}

        {/* Manual download link */}
        {downloadUrl && (
          <p className="download-link">
            Or download manually: <a className='link' href={downloadUrl} download="merged_files.zip">Download ZIP file</a>
          </p>
        )}

        {/* Upload button */}
        <button
          onClick={handleUpload}
          disabled={uploading || !selectedFile} // Diabled if uploading or no file selected
          className="upload-button"
        >
          {uploading ? 'Processing...' : 'Upload & Merge'}
        </button>
      </div>
    </div>
  );
}

export default App;
