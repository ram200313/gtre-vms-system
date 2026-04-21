/**
 * ✅ RESULT SCREEN
 * 
 * Displays the OCR results including:
 * - Detected document type (Aadhaar/PAN/DL/Passport)
 * - Confidence score
 * - Extracted document number
 * - Verification status (if expected number was provided)
 * - Extracted name & DOB
 */

import { useState } from 'react';
import { DetectionResult } from '../types';
import { getDocumentLabel, getDocNumberHint, verifyAgainstInput } from '../utils/documentDetector';
import { FiCheckCircle, FiXCircle, FiAlertCircle, FiRefreshCw, FiEye, FiEyeOff, FiCopy, FiCheck } from 'react-icons/fi';

interface ResultScreenProps {
  result: DetectionResult;
  imageData: string;
  onScanAgain: () => void;
  onGoHome: () => void;
}

export default function ResultScreen({ result, imageData, onScanAgain, onGoHome }: ResultScreenProps) {
  const [verifyNumber, setVerifyNumber] = useState('');
  const [verificationResult, setVerificationResult] = useState<{ match: boolean; similarity: number } | null>(null);
  const [showRawText, setShowRawText] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleVerify = () => {
    if (!verifyNumber.trim()) return;
    const vResult = verifyAgainstInput(result.extractedNumber, verifyNumber);
    setVerificationResult(vResult);
  };

  const copyNumber = () => {
    if (result.extractedNumber) {
      navigator.clipboard.writeText(result.extractedNumber);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return 'text-green-400';
    if (confidence >= 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 70) return 'bg-green-500/10 border-green-500/30';
    if (confidence >= 40) return 'bg-yellow-500/10 border-yellow-500/30';
    return 'bg-red-500/10 border-red-500/30';
  };

  return (
    <div className="flex flex-col items-center w-full max-w-2xl mx-auto px-4 pb-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">📋 Scan Results</h2>
        <p className="text-gray-400 text-sm">
          Scanned at {result.timestamp.toLocaleTimeString()}
        </p>
      </div>

      {/* Image Preview */}
      <div className="w-full max-w-sm aspect-[4/3] rounded-xl overflow-hidden shadow-xl border border-gray-700 mb-6">
        <img src={imageData} alt="Scanned document" className="w-full h-full object-cover" />
      </div>

      {/* Document Type Card */}
      <div className={`w-full rounded-xl p-5 border mb-4 ${getConfidenceBg(result.confidence)}`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Detected Document</p>
            <p className="text-xl font-bold text-white">{getDocumentLabel(result.documentType)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Confidence</p>
            <p className={`text-2xl font-bold ${getConfidenceColor(result.confidence)}`}>
              {result.confidence}%
            </p>
          </div>
        </div>
        {result.documentType !== 'unknown' && (
          <p className="text-xs text-gray-500 mt-2">{getDocNumberHint(result.documentType)}</p>
        )}
      </div>

      {/* Extracted Information */}
      <div className="w-full bg-gray-800/60 rounded-xl border border-gray-700/50 overflow-hidden mb-4">
        <div className="p-4 border-b border-gray-700/50">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            Extracted Information
          </h3>
        </div>

        {/* Document Number */}
        <div className="p-4 border-b border-gray-700/30">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 mb-1">Document Number</p>
              <p className="text-lg font-mono font-bold text-white">
                {result.extractedNumber || '—  Not detected'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {result.extractedNumber && (
                <button
                  onClick={copyNumber}
                  className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                  title="Copy number"
                >
                  {copied ? <FiCheck className="text-green-400" size={16} /> : <FiCopy className="text-gray-400" size={16} />}
                </button>
              )}
              {result.isNumberValid ? (
                <span className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded-full">
                  <FiCheckCircle size={12} /> Valid Format
                </span>
              ) : result.extractedNumber ? (
                <span className="flex items-center gap-1 text-xs text-yellow-400 bg-yellow-500/10 px-2 py-1 rounded-full">
                  <FiAlertCircle size={12} /> Check Format
                </span>
              ) : null}
            </div>
          </div>
        </div>

        {/* Name */}
        {result.extractedName && (
          <div className="p-4 border-b border-gray-700/30">
            <p className="text-xs text-gray-500 mb-1">Name</p>
            <p className="text-base font-medium text-white">{result.extractedName}</p>
          </div>
        )}

        {/* DOB */}
        {result.extractedDOB && (
          <div className="p-4 border-b border-gray-700/30">
            <p className="text-xs text-gray-500 mb-1">Date of Birth</p>
            <p className="text-base font-medium text-white">{result.extractedDOB}</p>
          </div>
        )}
      </div>

      {/* Verification Section */}
      <div className="w-full bg-gray-800/60 rounded-xl border border-gray-700/50 overflow-hidden mb-4">
        <div className="p-4 border-b border-gray-700/50">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            🔐 Verify Document Number
          </h3>
          <p className="text-xs text-gray-500 mt-1">
            Enter the expected document number to verify against the scanned result
          </p>
        </div>
        <div className="p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={verifyNumber}
              onChange={(e) => {
                setVerifyNumber(e.target.value);
                setVerificationResult(null);
              }}
              placeholder="Enter document number to verify..."
              className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl text-white 
                         placeholder-gray-600 focus:outline-none focus:border-blue-500 focus:ring-1 
                         focus:ring-blue-500 font-mono text-sm"
            />
            <button
              onClick={handleVerify}
              disabled={!verifyNumber.trim()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 
                         disabled:text-gray-500 text-white rounded-xl font-medium transition-colors
                         whitespace-nowrap"
            >
              Verify
            </button>
          </div>

          {/* Verification Result */}
          {verificationResult && (
            <div className={`mt-4 p-4 rounded-xl border ${
              verificationResult.match
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="flex items-center gap-3">
                {verificationResult.match ? (
                  <FiCheckCircle className="text-green-400 shrink-0" size={24} />
                ) : (
                  <FiXCircle className="text-red-400 shrink-0" size={24} />
                )}
                <div>
                  <p className={`font-bold ${verificationResult.match ? 'text-green-400' : 'text-red-400'}`}>
                    {verificationResult.match ? '✅ VERIFIED - Numbers Match!' : '❌ MISMATCH - Numbers Don\'t Match'}
                  </p>
                  <p className="text-sm text-gray-400 mt-1">
                    Similarity: {verificationResult.similarity}%
                    {verificationResult.similarity >= 85 && verificationResult.similarity < 100 && (
                      <span className="text-yellow-400"> (Close match - possible OCR variation)</span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Raw OCR Text (collapsible) */}
      <div className="w-full bg-gray-800/60 rounded-xl border border-gray-700/50 overflow-hidden mb-6">
        <button
          onClick={() => setShowRawText(!showRawText)}
          className="w-full p-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors"
        >
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            📝 Raw OCR Text
          </h3>
          {showRawText ? <FiEyeOff className="text-gray-400" /> : <FiEye className="text-gray-400" />}
        </button>
        {showRawText && (
          <div className="p-4 pt-0">
            <pre className="text-xs text-gray-400 bg-gray-900 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap font-mono max-h-60 overflow-y-auto">
              {result.rawText || 'No text detected'}
            </pre>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 w-full">
        <button
          onClick={() => {
            window.parent.postMessage({
              type: 'VMS_SCAN_RESULT',
              data: {
                id_type: result.documentType,
                name: result.extractedName,
                id_number: result.extractedNumber,
                dob: result.extractedDOB,
                confidence: result.confidence,
                idPhotoPath: imageData
              }
            }, '*');
          }}
          className="flex-1 px-6 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg flex items-center justify-center gap-2"
        >
          <FiCheck size={18} />
          Confirm details
        </button>
        <button
          onClick={onScanAgain}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-blue-600 
                     hover:bg-blue-700 text-white rounded-xl font-medium transition-all 
                     hover:scale-[1.02] active:scale-[0.98] shadow-lg"
        >
          <FiRefreshCw size={18} />
          Rescan
        </button>
      </div>
    </div>
  );
}
