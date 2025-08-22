/**
 * Enhanced File Upload Component with drag-and-drop, file validation, and progress tracking
 */
import React, { useState, useRef, useCallback } from 'react';
import { useAppStore } from '../appStore';
import { uploadFile } from '../services/fileApi';
import { generateId } from '../utils/id';
import { 
  Upload, 
  FileText, 
  Image, 
  X, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  File,
  Paperclip
} from 'lucide-react';

interface EnhancedFileUploadProps {
  acceptedTypes?: string[];
  maxFileSize?: number; // in MB
  multiple?: boolean;
  onUploadComplete?: (files: any[]) => void;
  className?: string;
  variant?: 'full' | 'compact' | 'button';
}

export const EnhancedFileUpload: React.FC<EnhancedFileUploadProps> = ({
  acceptedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.txt', '.csv'],
  maxFileSize = 50,
  multiple = false,
  onUploadComplete,
  className = '',
  variant = 'full'
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const { addUpload, updateUpload, addMessage, addStatusMessage, uploads } = useAppStore();
  
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // File validation
  const validateFile = (file: File): string[] => {
    const errors: string[] = [];
    
    // Check file size
    if (file.size > maxFileSize * 1024 * 1024) {
      errors.push(`File size must be less than ${maxFileSize}MB`);
    }
    
    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedTypes.includes(fileExtension)) {
      errors.push(`File type ${fileExtension} is not supported. Accepted types: ${acceptedTypes.join(', ')}`);
    }
    
    return errors;
  };

  // Handle file selection
  const handleFiles = useCallback(async (files: FileList) => {
    const fileArray = Array.from(files);
    const allErrors: string[] = [];
    const validFiles: File[] = [];

    // Validate all files first
    fileArray.forEach(file => {
      const errors = validateFile(file);
      if (errors.length > 0) {
        allErrors.push(`${file.name}: ${errors.join(', ')}`);
      } else {
        validFiles.push(file);
      }
    });

    setValidationErrors(allErrors);

    // Process valid files
    const uploadedFiles: any[] = [];
    for (const file of validFiles) {
      const tempId = generateId('upload');

      // Add to upload tracking
      addUpload({
        id: tempId,
        name: file.name,
        size: file.size,
        mime: file.type,
        progress: 0,
        assetType: 'component',
        parsed_at: null,
        parsing_status: null,
        parsing_error: null,
        is_human_verified: false,
      });

      addStatusMessage(`Uploading ${file.name}…`, 'info');

      try {
        const asset = await uploadFile(file, (progress) => 
          updateUpload(tempId, { progress })
        );

        // Update with completed upload
        updateUpload(tempId, {
          ...asset,
          id: asset.id,
          progress: 100,
          parsing_status: 'pending',
        });

        uploadedFiles.push(asset);
        addMessage({ id: crypto.randomUUID(), author: 'User', text: `✅ Uploaded ${file.name}` });
        addStatusMessage(`Upload complete: ${file.name}`, 'success');

      } catch (error: any) {
        console.error('Upload failed', error);
        updateUpload(tempId, { progress: -1 });
        addMessage({ id: crypto.randomUUID(), author: 'User', text: `❌ Upload failed for ${file.name}` });
        if (error?.status === 401) {
          addStatusMessage('Unauthorized. Please log in to upload files.', 'error');
        } else {
          addStatusMessage(`Upload failed: ${file.name}`, 'error');
        }
      }
    }

    // Clear input
    if (inputRef.current) {
      inputRef.current.value = '';
    }

    // Callback with successful uploads
    if (onUploadComplete && uploadedFiles.length > 0) {
      onUploadComplete(uploadedFiles);
    }
  }, [acceptedTypes, maxFileSize, addUpload, updateUpload, addMessage, addStatusMessage, onUploadComplete]);

  // File input change handler
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      handleFiles(files);
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files) {
      handleFiles(files);
    }
  };

  // Click handler
  const handleClick = () => {
    inputRef.current?.click();
  };

  // Get file type icon
  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return <FileText className="w-6 h-6 text-red-500" />;
      case 'png':
      case 'jpg':
      case 'jpeg':
        return <Image className="w-6 h-6 text-blue-500" />;
      default:
        return <File className="w-6 h-6 text-gray-500" />;
    }
  };

  // Active uploads for this component
  const activeUploads = uploads.filter(u => u.progress >= 0 && u.progress < 100);

  // Render compact button variant
  if (variant === 'button') {
    return (
      <div className={className}>
        <input
          ref={inputRef}
          type="file"
          onChange={handleInputChange}
          accept={acceptedTypes.join(',')}
          multiple={multiple}
          className="hidden"
        />
        <button
          onClick={handleClick}
          className="relative p-2 text-gray-500 hover:text-blue-600 transition-colors"
          aria-label="Upload file"
        >
          <Paperclip size={20} />
          {activeUploads.length > 0 && (
            <>
              <Loader2 size={14} className="absolute top-0 right-0 text-blue-600 animate-spin" />
              <span className="absolute -top-1 -right-1 bg-red-600 text-white rounded-full text-xs w-4 h-4 flex items-center justify-center">
                {activeUploads.length}
              </span>
            </>
          )}
        </button>
      </div>
    );
  }

  // Render compact variant
  if (variant === 'compact') {
    return (
      <div className={`space-y-2 ${className}`}>
        <input
          ref={inputRef}
          type="file"
          onChange={handleInputChange}
          accept={acceptedTypes.join(',')}
          multiple={multiple}
          className="hidden"
        />
        
        <button
          onClick={handleClick}
          className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          <Upload className="w-4 h-4" />
          <span className="text-sm">Upload Files</span>
        </button>

        {/* Active uploads */}
        {activeUploads.map(upload => (
          <div key={upload.id} className="flex items-center space-x-2 text-sm">
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
            <span className="flex-1 truncate">{upload.name}</span>
            <span className="text-gray-500">{upload.progress}%</span>
          </div>
        ))}

        {/* Validation errors */}
        {validationErrors.map((error, index) => (
          <div key={index} className="flex items-center space-x-2 text-sm text-red-600">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        ))}
      </div>
    );
  }

  // Render full variant
  return (
    <div className={`space-y-4 ${className}`}>
      <input
        ref={inputRef}
        type="file"
        onChange={handleInputChange}
        accept={acceptedTypes.join(',')}
        multiple={multiple}
        className="hidden"
      />

      {/* Drop zone */}
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-6 cursor-pointer transition-all duration-200
          ${isDragOver 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
        `}
      >
        <div className="text-center">
          <Upload className={`mx-auto h-12 w-12 ${isDragOver ? 'text-blue-500' : 'text-gray-400'}`} />
          <div className="mt-4">
            <p className="text-sm font-medium text-gray-900">
              {isDragOver ? 'Drop files here' : 'Upload datasheets and documents'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Drag and drop files or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Supported: {acceptedTypes.join(', ')} • Max {maxFileSize}MB
            </p>
          </div>
        </div>
      </div>

      {/* Active uploads */}
      {activeUploads.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-900">Uploading...</h4>
          {activeUploads.map(upload => (
            <div key={upload.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-md">
              {getFileIcon(upload.name)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{upload.name}</p>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500">{upload.progress}%</span>
                </div>
              </div>
              <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
            </div>
          ))}
        </div>
      )}

      {/* Validation errors */}
      {validationErrors.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-red-900">Upload Errors</h4>
          {validationErrors.map((error, index) => (
            <div key={index} className="flex items-start space-x-2 p-3 bg-red-50 rounded-md">
              <AlertCircle className="w-4 h-4 text-red-500 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={() => setValidationErrors(errors => errors.filter((_, i) => i !== index))}
                className="ml-auto p-1 text-red-500 hover:text-red-700"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Recent successful uploads */}
      {uploads.filter(u => u.progress === 100).slice(-3).length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-900">Recently Uploaded</h4>
          {uploads.filter(u => u.progress === 100).slice(-3).map(upload => (
            <div key={upload.id} className="flex items-center space-x-3 p-3 bg-green-50 rounded-md">
              {getFileIcon(upload.name)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{upload.name}</p>
                <p className="text-xs text-gray-500">
                  {upload.parsing_status === 'success' ? 'Parsed successfully' : 
                   upload.parsing_status === 'failed' ? 'Parsing failed' : 
                   upload.parsing_status === 'processing' ? 'Processing...' : 'Ready for parsing'}
                </p>
              </div>
              <CheckCircle className="w-4 h-4 text-green-500" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EnhancedFileUpload;
