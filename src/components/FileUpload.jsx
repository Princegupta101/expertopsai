import { useState, useRef } from 'react'
import { useAuth0 } from '@auth0/auth0-react'
import apiClient from '../utils/apiClient'

const FileUpload = () => {
  const { getAccessTokenSilently } = useAuth0()
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [uploadSuccess, setUploadSuccess] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileSelect = async (file) => {
    if (!file) return

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    if (!allowedTypes.includes(file.type)) {
      setUploadError('Invalid file type. Only JPG, PNG, and GIF images are allowed.')
      return
    }

    // Validate file size (5MB)
    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      setUploadError('File size exceeds 5MB limit.')
      return
    }

    setUploading(true)
    setUploadError(null)
    setUploadSuccess(null)

    try {
      const token = await getAccessTokenSilently()
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiClient.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      })

      setUploadSuccess(`File "${file.name}" uploaded successfully!`)
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
      // Refresh the file list by dispatching a custom event
      window.dispatchEvent(new CustomEvent('fileUploaded'))
      
    } catch (error) {
      console.error('Upload error:', error)
      setUploadError(
        error.response?.data?.detail || 
        'Failed to upload file. Please try again.'
      )
    } finally {
      setUploading(false)
    }
  }

  const handleFileInputChange = (event) => {
    const file = event.target.files[0]
    handleFileSelect(file)
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (event) => {
    event.preventDefault()
    setDragOver(false)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setDragOver(false)
    
    const files = event.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div 
      className={`file-upload ${dragOver ? 'drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <h3>Upload Image</h3>
      
      <div className="file-input-wrapper">
        <input
          ref={fileInputRef}
          type="file"
          id="file-input"
          className="file-input"
          accept="image/jpeg,image/jpg,image/png,image/gif"
          onChange={handleFileInputChange}
          disabled={uploading}
        />
        <label htmlFor="file-input" className="file-input-label">
          {uploading ? 'Uploading...' : 'Choose Image'}
        </label>
      </div>

      <div className="upload-info">
        <p>Drag and drop an image here, or click to select a file</p>
        <p>Supported formats: JPG, PNG, GIF | Maximum size: 5MB</p>
      </div>

      {uploading && (
        <div className="upload-progress">
          Uploading your image...
        </div>
      )}

      {uploadError && (
        <div className="upload-error">
          {uploadError}
        </div>
      )}

      {uploadSuccess && (
        <div className="upload-progress">
          {uploadSuccess}
        </div>
      )}
    </div>
  )
}

export default FileUpload
