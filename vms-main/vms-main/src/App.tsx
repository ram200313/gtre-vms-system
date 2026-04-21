/**
 * 🏗️ MAIN APP COMPONENT
 * 
 * This is the entry point of our application.
 * It manages which screen to show (Home → Camera → Processing → Results)
 * and handles the OCR processing using Tesseract.js
 * 
 * ARCHITECTURE (how screens flow):
 * 
 *   [Home Screen] → click "Start Scan"
 *        ↓
 *   [Camera Screen] → capture photo
 *        ↓
 *   [Processing Screen] → Tesseract.js runs OCR
 *        ↓
 *   [Result Screen] → show detected doc type, number, verify
 *        ↓
 *   [Home Screen or Camera Screen] → scan again
 * 
 * 
 * ABOUT TESSERACT.JS:
 * - It's an OCR engine that runs entirely in the browser
 * - Uses WebAssembly (WASM) for near-native performance
 * - Supports 100+ languages
 * - We use 'eng' (English) + 'hin' (Hindi) for Indian documents
 * - First load downloads ~15MB of language data (cached after)
 */

import { useState, useCallback } from 'react';
import Tesseract from 'tesseract.js';
import { AppScreen, DetectionResult } from './types';
import { detectDocument } from './utils/documentDetector';
import HomeScreen from './components/HomeScreen';
import CameraCapture from './components/CameraCapture';
import ProcessingScreen from './components/ProcessingScreen';
import ResultScreen from './components/ResultScreen';

export default function App() {
  // State management - these control what the app shows
  const [screen, setScreen] = useState<AppScreen>('home');
  const [capturedImage, setCapturedImage] = useState<string>('');
  const [ocrProgress, setOcrProgress] = useState(0);
  const [ocrStatus, setOcrStatus] = useState('Initializing...');
  const [result, setResult] = useState<DetectionResult | null>(null);

  /**
   * 🧠 THE MAIN OCR FUNCTION
   * 
   * This is where the magic happens!
   * 1. Takes the captured image
   * 2. Sends it to Tesseract.js for text recognition
   * 3. Passes the extracted text to our document detector
   * 4. Shows the results
   */
  const processImage = useCallback(async (imageData: string) => {
    setCapturedImage(imageData);
    setScreen('processing');
    setOcrProgress(0);
    setOcrStatus('Initializing OCR engine...');

    try {
      // 🔥 This is the Tesseract.js call that does OCR
      const ocrResult = await Tesseract.recognize(
        imageData,        // the image to scan
        'eng',            // language: English
        {
          // This callback fires as OCR progresses
          logger: (info: { status: string; progress: number }) => {
            if (info.status === 'recognizing text') {
              setOcrProgress(Math.round(info.progress * 100));
              setOcrStatus('Recognizing text...');
            } else if (info.status === 'loading language traineddata') {
              setOcrProgress(Math.round(info.progress * 50));
              setOcrStatus('Loading language data...');
            } else {
              setOcrStatus(info.status || 'Processing...');
            }
          },
        }
      );

      // Get the raw text from OCR
      const rawText = ocrResult.data.text;

      // Pass to our document detector for analysis
      setOcrStatus('Analyzing document...');
      setOcrProgress(95);

      // Small delay to show "analyzing" status
      await new Promise(resolve => setTimeout(resolve, 500));

      const detection = detectDocument(rawText);
      setResult(detection);
      setOcrProgress(100);

      // Show results after a brief moment
      setTimeout(() => {
        setScreen('result');
      }, 300);

    } catch (error) {
      console.error('OCR Error:', error);
      // Even if OCR partially fails, show what we got
      setResult({
        documentType: 'unknown',
        confidence: 0,
        extractedNumber: '',
        isNumberValid: false,
        rawText: `Error during OCR: ${error}`,
        extractedName: '',
        extractedDOB: '',
        timestamp: new Date(),
      });
      setScreen('result');
    }
  }, []);

  // Handle photo capture from camera
  const handleCapture = useCallback((imageData: string) => {
    processImage(imageData);
  }, [processImage]);

  // Navigation handlers
  const goHome = () => {
    setScreen('home');
    setResult(null);
    setCapturedImage('');
    setOcrProgress(0);
  };

  const startScan = () => {
    setScreen('capture');
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white">
      {/* Top Navigation Bar */}
      <nav className="sticky top-0 z-50 bg-gray-900/80 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={goHome}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <span className="text-2xl">🔐</span>
            <div>
              <h1 className="text-sm font-bold text-white leading-tight">VMS DocVerify</h1>
              <p className="text-[10px] text-gray-500 leading-tight">Visitor Document Verification</p>
            </div>
          </button>

          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 hidden sm:block">Intranet Mode</span>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
              <span className="text-xs text-green-400 font-medium">Active</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto py-6 md:py-10">
        {screen === 'home' && (
          <HomeScreen onStartScan={startScan} />
        )}

        {screen === 'capture' && (
          <CameraCapture onCapture={handleCapture} onCancel={goHome} />
        )}

        {screen === 'processing' && (
          <ProcessingScreen
            imageData={capturedImage}
            progress={ocrProgress}
            statusText={ocrStatus}
          />
        )}

        {screen === 'result' && result && (
          <ResultScreen
            result={result}
            imageData={capturedImage}
            onScanAgain={startScan}
            onGoHome={goHome}
          />
        )}
      </main>
    </div>
  );
}
