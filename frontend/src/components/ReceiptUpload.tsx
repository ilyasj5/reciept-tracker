'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { storage } from '@/lib/firebase'
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage'
import { Upload, CheckCircle, AlertCircle } from 'lucide-react'

interface ReceiptUploadProps {
  userId: string
}

export default function ReceiptUpload({ userId }: ReceiptUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setUploading(true)
    setUploadStatus('idle')
    setMessage('')

    try {
      // Upload to Firebase Storage
      const storageRef = ref(storage, `receipts/${userId}/${Date.now()}_${file.name}`)
      await uploadBytes(storageRef, file)
      const downloadURL = await getDownloadURL(storageRef)

      // Trigger Cloud Function for processing
      const response = await fetch('/api/process-receipt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imageUrl: downloadURL,
          userId,
        }),
      })

      if (response.ok) {
        setUploadStatus('success')
        setMessage('Receipt uploaded and processing started!')
      } else {
        throw new Error('Failed to process receipt')
      }
    } catch (error: any) {
      setUploadStatus('error')
      setMessage(error.message || 'Failed to upload receipt')
    } finally {
      setUploading(false)
    }
  }, [userId])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif']
    },
    maxFiles: 1,
    disabled: uploading
  })

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload Receipt</h2>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        {isDragActive ? (
          <p className="text-lg text-gray-600">Drop the receipt here...</p>
        ) : (
          <div>
            <p className="text-lg text-gray-600 mb-2">
              Drag and drop a receipt image here, or click to select
            </p>
            <p className="text-sm text-gray-500">
              Supports PNG, JPG, JPEG, GIF
            </p>
          </div>
        )}
      </div>

      {uploading && (
        <div className="mt-4 flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Processing receipt...</span>
        </div>
      )}

      {uploadStatus === 'success' && (
        <div className="mt-4 flex items-center space-x-2 text-green-600 bg-green-50 p-4 rounded-lg">
          <CheckCircle size={20} />
          <span>{message}</span>
        </div>
      )}

      {uploadStatus === 'error' && (
        <div className="mt-4 flex items-center space-x-2 text-red-600 bg-red-50 p-4 rounded-lg">
          <AlertCircle size={20} />
          <span>{message}</span>
        </div>
      )}

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">How it works:</h3>
        <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
          <li>Upload a receipt image</li>
          <li>AI extracts merchant, date, amount, and items</li>
          <li>Receipt is automatically categorized</li>
          <li>Data appears in your dashboard</li>
        </ol>
      </div>
    </div>
  )
}
