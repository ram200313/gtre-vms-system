// 👇 These are TypeScript "types" - they define what shape our data should have
// Think of them like a blueprint/template

export type DocumentType = 'aadhaar' | 'pan' | 'driving_license' | 'passport' | 'unknown';

export interface DetectionResult {
  documentType: DocumentType;
  confidence: number;        // 0 to 100 - how sure we are about the doc type
  extractedNumber: string;   // the document number we found
  isNumberValid: boolean;    // does the number match the expected format?
  rawText: string;           // full text from OCR
  extractedName: string;     // name found on document
  extractedDOB: string;      // date of birth found
  timestamp: Date;           // when was this scanned
}

export interface VerificationInput {
  expectedDocNumber: string; // the number we want to verify against
  expectedName?: string;     // optional: name to verify
}

export type AppScreen = 'home' | 'capture' | 'processing' | 'result';
