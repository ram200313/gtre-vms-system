/**
 * 🧠 DOCUMENT DETECTOR - The Brain of our OCR System
 * 
 * HOW IT WORKS:
 * 1. Tesseract.js reads the image and gives us raw text
 * 2. We search that text for PATTERNS (regex) that match each document type
 * 3. We extract the document number using those patterns
 * 4. We validate the number format
 * 
 * REGEX CHEAT SHEET (you'll see these below):
 * \d    = any digit (0-9)
 * {4}   = exactly 4 times
 * [A-Z] = any uppercase letter
 * \s    = any whitespace (space, tab, etc.)
 * |     = OR
 * /i    = case insensitive
 */

import { DocumentType, DetectionResult } from '../types';

// ---------- DOCUMENT PATTERNS ----------
// Each document has unique keywords and number formats

const DOCUMENT_PATTERNS = {
  aadhaar: {
    // Aadhaar cards have these keywords on them
    keywords: [
      'aadhaar', 'aadhar', 'adhar', 'uidai', 'uid',
      'unique identification', 'government of india',
      'enrolment', 'enrollment', 'male', 'female',
      'date of birth', 'dob', 'भारत सरकार'
    ],
    // Aadhaar number format: 4 digits - 4 digits - 4 digits (like 1234 5678 9012)
    numberPattern: /\b(\d{4}\s?\d{4}\s?\d{4})\b/g,
    // VID pattern (Virtual ID)
    vidPattern: /\b(\d{4}\s?\d{4}\s?\d{4}\s?\d{4})\b/g,
  },
  pan: {
    keywords: [
      'income tax', 'permanent account number', 'pan',
      'govt. of india', 'govt of india', 'it department',
      'income tax department', 'father', 'name'
    ],
    // PAN format: 5 letters + 4 digits + 1 letter (like ABCDE1234F)
    numberPattern: /\b([A-Z]{5}\d{4}[A-Z])\b/gi,
  },
  driving_license: {
    keywords: [
      'driving licence', 'driving license', 'licence',
      'transport', 'motor vehicle', 'dl no',
      'non-transport', 'valid', 'issue date',
      'rto', 'regional transport', 'mcwg', 'lmv'
    ],
    // DL format: State code (2 letters) + numbers (varies by state)
    // Examples: KA01-20120012345, DL-0420110012345
    numberPattern: /\b([A-Z]{2}[\s-]?\d{2}[\s-]?\d{4,11}\d*)\b/gi,
    altPattern: /\b([A-Z]{2}\d{2}\s?\d{4}\s?\d{7})\b/gi,
  },
  passport: {
    keywords: [
      'passport', 'republic of india', 'nationality',
      'date of issue', 'date of expiry', 'place of birth',
      'place of issue', 'type', 'country code', 'ind',
      'surname', 'given name', 'paspor'
    ],
    // Passport format: 1 letter + 7 digits (like A1234567)
    numberPattern: /\b([A-Z]\d{7})\b/gi,
  },
};

// ---------- DETECTION FUNCTION ----------

export function detectDocument(rawText: string): DetectionResult {
  const text = rawText.toLowerCase();
  const upperText = rawText.toUpperCase();
  
  // Score each document type based on how many keywords we find
  const scores: Record<DocumentType, number> = {
    aadhaar: 0,
    pan: 0,
    driving_license: 0,
    passport: 0,
    unknown: 0,
  };

  // Count keyword matches for each document type
  for (const [docType, patterns] of Object.entries(DOCUMENT_PATTERNS)) {
    for (const keyword of patterns.keywords) {
      if (text.includes(keyword.toLowerCase())) {
        scores[docType as DocumentType] += 10; // each keyword match = 10 points
      }
    }
  }

  // Try to extract numbers for each type and boost score if found
  let extractedNumber = '';
  let detectedType: DocumentType = 'unknown';
  let maxScore = 0;

  // Check Aadhaar
  const aadhaarMatch = upperText.match(DOCUMENT_PATTERNS.aadhaar.numberPattern);
  if (aadhaarMatch) {
    scores.aadhaar += 25;
    // Validate: Aadhaar shouldn't start with 0 or 1
    const cleanNum = aadhaarMatch[0].replace(/\s/g, '');
    if (cleanNum.length === 12 && !cleanNum.startsWith('0') && !cleanNum.startsWith('1')) {
      scores.aadhaar += 15;
    }
  }

  // Check PAN
  const panMatch = upperText.match(DOCUMENT_PATTERNS.pan.numberPattern);
  if (panMatch) {
    scores.pan += 30;
    // PAN 4th character tells entity type (P=Person, C=Company, etc.)
    const fourthChar = panMatch[0][3];
    if ('PCHATBLJFG'.includes(fourthChar)) {
      scores.pan += 10;
    }
  }

  // Check DL
  const dlMatch = upperText.match(DOCUMENT_PATTERNS.driving_license.numberPattern);
  if (dlMatch) {
    scores.driving_license += 25;
  }

  // Check Passport
  const passportMatch = upperText.match(DOCUMENT_PATTERNS.passport.numberPattern);
  if (passportMatch) {
    scores.passport += 25;
  }

  // Find highest scoring document type
  for (const [docType, score] of Object.entries(scores)) {
    if (score > maxScore && docType !== 'unknown') {
      maxScore = score;
      detectedType = docType as DocumentType;
    }
  }

  // If no type scored above threshold, mark as unknown
  if (maxScore < 15) {
    detectedType = 'unknown';
  }

  // Extract the document number based on detected type
  switch (detectedType) {
    case 'aadhaar':
      extractedNumber = aadhaarMatch?.[0]?.replace(/\s+/g, ' ') || '';
      break;
    case 'pan':
      extractedNumber = panMatch?.[0] || '';
      break;
    case 'driving_license':
      extractedNumber = dlMatch?.[0] || '';
      break;
    case 'passport':
      extractedNumber = passportMatch?.[0] || '';
      break;
  }

  // Calculate confidence (0-100)
  const confidence = Math.min(Math.round((maxScore / 65) * 100), 99);

  return {
    documentType: detectedType,
    confidence,
    extractedNumber: extractedNumber.trim(),
    isNumberValid: validateDocNumber(detectedType, extractedNumber),
    rawText,
    extractedName: extractName(rawText, detectedType),
    extractedDOB: extractDOB(rawText),
    timestamp: new Date(),
  };
}

// ---------- VALIDATION FUNCTIONS ----------

export function validateDocNumber(docType: DocumentType, number: string): boolean {
  const clean = number.replace(/[\s-]/g, '');
  
  switch (docType) {
    case 'aadhaar':
      // 12 digits, doesn't start with 0 or 1
      return /^\d{12}$/.test(clean) && !clean.startsWith('0') && !clean.startsWith('1');
    
    case 'pan':
      // 5 letters + 4 digits + 1 letter
      return /^[A-Z]{5}\d{4}[A-Z]$/i.test(clean);
    
    case 'driving_license':
      // State code + digits (minimum 10 chars)
      return /^[A-Z]{2}\d{8,15}$/i.test(clean) || /^[A-Z]{2}\d{2}\d{4,11}$/i.test(clean);
    
    case 'passport':
      // 1 letter + 7 digits
      return /^[A-Z]\d{7}$/i.test(clean);
    
    default:
      return false;
  }
}

export function verifyAgainstInput(extracted: string, expected: string): {
  match: boolean;
  similarity: number;
} {
  const cleanExtracted = extracted.replace(/[\s-]/g, '').toUpperCase();
  const cleanExpected = expected.replace(/[\s-]/g, '').toUpperCase();
  
  if (cleanExtracted === cleanExpected) {
    return { match: true, similarity: 100 };
  }
  
  // Calculate similarity percentage (Levenshtein-like)
  let matches = 0;
  const maxLen = Math.max(cleanExtracted.length, cleanExpected.length);
  const minLen = Math.min(cleanExtracted.length, cleanExpected.length);
  
  for (let i = 0; i < minLen; i++) {
    if (cleanExtracted[i] === cleanExpected[i]) {
      matches++;
    }
  }
  
  const similarity = maxLen > 0 ? Math.round((matches / maxLen) * 100) : 0;
  return { match: similarity >= 85, similarity };
}

// ---------- HELPER FUNCTIONS ----------

function extractName(text: string, docType: DocumentType): string {
  const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 2);
  
  // Look for name patterns
  for (const line of lines) {
    // "Name: John Doe" or "Name John Doe"
    const nameMatch = line.match(/(?:name|naam)\s*[:\-]?\s*([A-Za-z\s]{3,40})/i);
    if (nameMatch) {
      return nameMatch[1].trim();
    }
  }
  
  // For PAN cards, name is usually after "Name" line
  if (docType === 'pan') {
    for (let i = 0; i < lines.length; i++) {
      if (/name/i.test(lines[i]) && lines[i + 1]) {
        const possibleName = lines[i + 1].trim();
        if (/^[A-Za-z\s]{3,40}$/.test(possibleName)) {
          return possibleName;
        }
      }
    }
  }
  
  return '';
}

function extractDOB(text: string): string {
  // Common date formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
  const dobMatch = text.match(
    /(?:d\.?o\.?b\.?|date\s*of\s*birth|birth|जन्म)\s*[:\-]?\s*(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4})/i
  );
  if (dobMatch) return dobMatch[1];
  
  // Try to find any date pattern
  const dateMatch = text.match(/\b(\d{2}[/\-.]\d{2}[/\-.]\d{4})\b/);
  if (dateMatch) return dateMatch[1];
  
  return '';
}

// Get friendly document name
export function getDocumentLabel(type: DocumentType): string {
  const labels: Record<DocumentType, string> = {
    aadhaar: '🪪 Aadhaar Card',
    pan: '💳 PAN Card',
    driving_license: '🚗 Driving License',
    passport: '✈️ Passport',
    unknown: '❓ Unknown Document',
  };
  return labels[type];
}

// Get document number format hint
export function getDocNumberHint(type: DocumentType): string {
  const hints: Record<DocumentType, string> = {
    aadhaar: 'Format: XXXX XXXX XXXX (12 digits)',
    pan: 'Format: ABCDE1234F (5 letters + 4 digits + 1 letter)',
    driving_license: 'Format: KA01-XXXXXXXXX (State code + numbers)',
    passport: 'Format: A1234567 (1 letter + 7 digits)',
    unknown: 'Please scan a valid document',
  };
  return hints[type];
}
