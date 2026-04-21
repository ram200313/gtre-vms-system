/**
 * 📷 CAMERA CAPTURE COMPONENT
 * 
 * WHAT THIS DOES:
 * - Opens your device camera (webcam or phone camera)
 * - Shows a live video feed with a guide overlay
 * - Lets you take a photo (snapshot)
 * - Converts the video frame to an image for OCR
 * 
 * KEY CONCEPTS:
 * - navigator.mediaDevices.getUserMedia() = asks browser for camera access
 * - <video> element = shows live camera feed
 * - <canvas> element = used to capture a still frame from video
 * - canvas.toDataURL() = converts canvas image to base64 string
 */

import { useRef, useState, useCallback, useEffect } from 'react';
import { FiCamera, FiRotateCw, FiUpload, FiX, FiZap } from 'react-icons/fi';

interface CameraCaptureProps {
  onCapture: (imageData: string) => void;  // callback when photo is taken
  onCancel: () => void;                     // callback to go back
}

export default function CameraCapture({ onCapture, onCancel }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [facingMode, setFacingMode] = useState<'environment' | 'user'>('environment');
  const [error, setError] = useState<string>('');
  const [cameraReady, setCameraReady] = useState(false);

  // Start camera when component mounts
  const startCamera = useCallback(async () => {
    try {
      // Stop any existing stream first
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }

      setError('');
      setCameraReady(false);

      // Request camera access
      // 'environment' = back camera (for phones), 'user' = front camera
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },   // request HD resolution for better OCR
          height: { ideal: 1080 },
        },
      });

      setStream(mediaStream);

      // Connect the stream to the video element
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.onloadedmetadata = () => {
          setCameraReady(true);
        };
      }
    } catch (err) {
      console.error('Camera error:', err);
      setError(
        'Camera access denied or not available. Please allow camera access or upload an image instead.'
      );
    }
  }, [facingMode]);

  // Start camera on mount
  useEffect(() => {
    startCamera();
    // Cleanup: stop camera when component unmounts
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [facingMode]);

  // Take a photo from the video feed
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw the current video frame onto the canvas
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Apply image enhancement for better OCR
    // Increase contrast and sharpen
    ctx.filter = 'contrast(1.3) brightness(1.1)';
    ctx.drawImage(canvas, 0, 0);
    ctx.filter = 'none';

    // Convert canvas to image data URL (base64 encoded PNG)
    const imageData = canvas.toDataURL('image/png', 1.0);

    // Stop the camera
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }

    // Send the image data to parent component
    onCapture(imageData);
  }, [stream, onCapture]);

  // Switch between front and back camera
  const switchCamera = () => {
    setFacingMode(prev => prev === 'environment' ? 'user' : 'environment');
  };

  // Handle file upload as alternative to camera
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      if (result) {
        // Stop camera
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }
        onCapture(result);
      }
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="flex flex-col items-center w-full max-w-2xl mx-auto">
      {/* Header */}
      <div className="w-full flex items-center justify-between mb-4 px-2">
        <button
          onClick={onCancel}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <FiX size={20} />
          <span>Cancel</span>
        </button>
        <h2 className="text-lg font-semibold text-white">📷 Scan Document</h2>
        <div className="w-20" /> {/* Spacer for centering */}
      </div>

      {/* Camera View */}
      <div className="relative w-full aspect-[4/3] bg-gray-900 rounded-2xl overflow-hidden shadow-2xl border border-gray-700">
        {error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
            <div className="text-5xl mb-4">📷</div>
            <p className="text-red-400 mb-4">{error}</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl flex items-center gap-2 transition-colors"
            >
              <FiUpload size={18} />
              Upload Image Instead
            </button>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            
            {/* Document Guide Overlay */}
            {cameraReady && (
              <div className="absolute inset-0 pointer-events-none">
                {/* Semi-transparent overlay with cutout */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative w-[85%] h-[60%]">
                    {/* Corner markers */}
                    <div className="absolute top-0 left-0 w-8 h-8 border-t-3 border-l-3 border-green-400 rounded-tl-lg" />
                    <div className="absolute top-0 right-0 w-8 h-8 border-t-3 border-r-3 border-green-400 rounded-tr-lg" />
                    <div className="absolute bottom-0 left-0 w-8 h-8 border-b-3 border-l-3 border-green-400 rounded-bl-lg" />
                    <div className="absolute bottom-0 right-0 w-8 h-8 border-b-3 border-r-3 border-green-400 rounded-br-lg" />
                    
                    {/* Scanning line animation */}
                    <div className="absolute left-2 right-2 h-0.5 bg-gradient-to-r from-transparent via-green-400 to-transparent animate-pulse" 
                         style={{ top: '50%' }} />
                  </div>
                </div>
                
                {/* Guide text */}
                <div className="absolute bottom-4 left-0 right-0 text-center">
                  <p className="text-green-400 text-sm font-medium bg-black/50 inline-block px-4 py-1 rounded-full">
                    Position document within the frame
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Tips */}
      <div className="w-full mt-4 px-4">
        <div className="bg-gray-800/60 rounded-xl p-3 border border-gray-700/50">
          <div className="flex items-start gap-2">
            <FiZap className="text-yellow-400 mt-0.5 shrink-0" size={16} />
            <div className="text-xs text-gray-400">
              <span className="text-yellow-400 font-medium">Tips for best results: </span>
              Good lighting • Hold steady • Avoid glare • Document should fill the frame
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-center gap-6 mt-6 pb-4">
        {/* Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-4 bg-gray-700 hover:bg-gray-600 text-white rounded-full transition-all hover:scale-105 shadow-lg"
          title="Upload from gallery"
        >
          <FiUpload size={22} />
        </button>

        {/* Capture Button (the big one!) */}
        <button
          onClick={capturePhoto}
          disabled={!cameraReady}
          className="p-6 bg-white hover:bg-gray-200 disabled:bg-gray-600 disabled:cursor-not-allowed 
                     text-gray-900 rounded-full transition-all hover:scale-105 shadow-xl 
                     ring-4 ring-white/20 active:scale-95"
          title="Capture photo"
        >
          <FiCamera size={32} />
        </button>

        {/* Switch Camera Button */}
        <button
          onClick={switchCamera}
          className="p-4 bg-gray-700 hover:bg-gray-600 text-white rounded-full transition-all hover:scale-105 shadow-lg"
          title="Switch camera"
        >
          <FiRotateCw size={22} />
        </button>
      </div>

      {/* Hidden elements */}
      <canvas ref={canvasRef} className="hidden" />
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileUpload}
        className="hidden"
      />
    </div>
  );
}
