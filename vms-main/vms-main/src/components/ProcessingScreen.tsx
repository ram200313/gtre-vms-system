/**
 * ⏳ PROCESSING SCREEN
 * 
 * Shows the captured image and OCR progress.
 * Tesseract.js gives us progress updates (0% to 100%)
 * which we display as a progress bar.
 */

interface ProcessingScreenProps {
  imageData: string;
  progress: number;       // 0 to 100
  statusText: string;     // "Recognizing text..." etc.
}

export default function ProcessingScreen({ imageData, progress, statusText }: ProcessingScreenProps) {
  return (
    <div className="flex flex-col items-center w-full max-w-2xl mx-auto px-4">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">🔍 Scanning Document</h2>
        <p className="text-gray-400 text-sm">Please wait while we analyze your document...</p>
      </div>

      {/* Captured Image Preview */}
      <div className="relative w-full max-w-md aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl border border-gray-700 mb-8">
        <img
          src={imageData}
          alt="Captured document"
          className="w-full h-full object-cover"
        />
        {/* Scanning overlay effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/10 to-transparent">
          <div
            className="absolute left-0 right-0 h-1 bg-blue-400 shadow-lg shadow-blue-400/50"
            style={{
              top: `${progress}%`,
              transition: 'top 0.3s ease-out',
              boxShadow: '0 0 20px rgba(96, 165, 250, 0.5)',
            }}
          />
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full max-w-md">
        <div className="flex justify-between mb-2">
          <span className="text-sm text-gray-400">{statusText}</span>
          <span className="text-sm font-mono text-blue-400">{Math.round(progress)}%</span>
        </div>
        <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden border border-gray-700">
          <div
            className="h-full bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-400 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Fun facts while waiting */}
      <div className="mt-8 text-center max-w-md">
        <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50">
          <p className="text-xs text-gray-500 mb-1">💡 Did you know?</p>
          <p className="text-sm text-gray-400">
            {progress < 30
              ? 'OCR (Optical Character Recognition) converts images of text into machine-readable text.'
              : progress < 60
              ? 'Tesseract.js can recognize over 100 languages including Hindi, English, and more!'
              : progress < 90
              ? 'The OCR engine uses neural networks trained on millions of text samples.'
              : 'Almost done! Matching patterns against known Indian document formats...'}
          </p>
        </div>
      </div>
    </div>
  );
}
