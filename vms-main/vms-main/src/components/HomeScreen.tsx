/**
 * 🏠 HOME SCREEN
 * 
 * The landing page of our VMS Document Verification System.
 * Shows supported documents and a big "Start Scanning" button.
 */

import { FiCamera, FiShield, FiWifi, FiZap } from 'react-icons/fi';

interface HomeScreenProps {
  onStartScan: () => void;
}

export default function HomeScreen({ onStartScan }: HomeScreenProps) {
  const supportedDocs = [
    { icon: '🪪', name: 'Aadhaar Card', format: 'XXXX XXXX XXXX', color: 'from-orange-500/20 to-orange-600/5 border-orange-500/20' },
    { icon: '💳', name: 'PAN Card', format: 'ABCDE1234F', color: 'from-blue-500/20 to-blue-600/5 border-blue-500/20' },
    { icon: '🚗', name: 'Driving License', format: 'XX00-XXXXXXX', color: 'from-green-500/20 to-green-600/5 border-green-500/20' },
    { icon: '✈️', name: 'Passport', format: 'A1234567', color: 'from-purple-500/20 to-purple-600/5 border-purple-500/20' },
  ];

  const features = [
    { icon: <FiZap className="text-yellow-400" size={20} />, title: 'Fast OCR', desc: 'Powered by Tesseract.js neural network' },
    { icon: <FiShield className="text-green-400" size={20} />, title: 'Secure', desc: 'All processing happens locally in browser' },
    { icon: <FiWifi className="text-blue-400" size={20} />, title: 'Intranet Ready', desc: 'Works without internet after deployment' },
    { icon: <FiCamera className="text-purple-400" size={20} />, title: 'Camera Scan', desc: 'Use camera or upload document image' },
  ];

  return (
    <div className="flex flex-col items-center w-full max-w-3xl mx-auto px-4 pb-8">
      {/* Hero Section */}
      <div className="text-center mb-10 mt-4">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs font-medium mb-6">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          System Online • Intranet Mode
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4 leading-tight">
          Document<br />
          <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
            Verification System
          </span>
        </h1>
        <p className="text-gray-400 text-lg max-w-md mx-auto">
          Scan and verify visitor documents instantly using AI-powered OCR technology
        </p>
      </div>

      {/* Start Scan Button */}
      <button
        onClick={onStartScan}
        className="group relative px-10 py-5 bg-gradient-to-r from-blue-600 to-cyan-600 
                   hover:from-blue-500 hover:to-cyan-500 text-white text-lg font-bold rounded-2xl 
                   transition-all duration-300 hover:scale-105 active:scale-95 shadow-2xl 
                   shadow-blue-500/25 hover:shadow-blue-500/40 mb-10"
      >
        <span className="flex items-center gap-3">
          <FiCamera size={24} className="group-hover:rotate-12 transition-transform" />
          Start Scanning
        </span>
        <div className="absolute inset-0 rounded-2xl bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
      </button>

      {/* Supported Documents */}
      <div className="w-full mb-10">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider text-center mb-4">
          Supported Documents
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {supportedDocs.map((doc) => (
            <div
              key={doc.name}
              className={`bg-gradient-to-br ${doc.color} border rounded-xl p-4 text-center 
                         hover:scale-105 transition-transform cursor-default`}
            >
              <div className="text-3xl mb-2">{doc.icon}</div>
              <p className="text-sm font-medium text-white mb-1">{doc.name}</p>
              <p className="text-xs font-mono text-gray-400">{doc.format}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div className="w-full">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider text-center mb-4">
          Features
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4 
                         hover:bg-gray-800/60 transition-colors"
            >
              <div className="mb-2">{feature.icon}</div>
              <p className="text-sm font-semibold text-white mb-1">{feature.title}</p>
              <p className="text-xs text-gray-500">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* How it works */}
      <div className="w-full mt-10">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider text-center mb-4">
          How It Works
        </h3>
        <div className="flex flex-col md:flex-row items-center gap-4">
          {[
            { step: '1', icon: '📷', title: 'Capture', desc: 'Take a photo or upload document image' },
            { step: '2', icon: '🔍', title: 'Scan', desc: 'AI reads all text from the document' },
            { step: '3', icon: '🧠', title: 'Detect', desc: 'System identifies document type & number' },
            { step: '4', icon: '✅', title: 'Verify', desc: 'Match against expected document number' },
          ].map((item, idx) => (
            <div key={item.step} className="flex md:flex-col items-center gap-3 md:gap-2 w-full md:text-center">
              <div className="flex items-center gap-3 md:flex-col">
                <div className="w-12 h-12 bg-gray-800 border border-gray-700 rounded-xl flex items-center justify-center text-2xl shrink-0">
                  {item.icon}
                </div>
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{item.title}</p>
                <p className="text-xs text-gray-500">{item.desc}</p>
              </div>
              {idx < 3 && <div className="hidden md:block text-gray-700 text-xl">→</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12 text-center">
        <p className="text-xs text-gray-600">
          VMS Document Verification System v1.0 • All processing done locally
        </p>
        <p className="text-xs text-gray-700 mt-1">
          Powered by Tesseract.js OCR Engine
        </p>
      </div>
    </div>
  );
}
