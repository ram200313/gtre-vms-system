-- Oracle 19c+ Database Schema for Visitor Management System (VMS)

-- Sequence for VISITOR_ID
CREATE SEQUENCE visitor_seq START WITH 1 INCREMENT BY 1;

-- Creating the Visitors table
CREATE TABLE VISITORS (
    ID NUMBER PRIMARY KEY,
    
    -- Basic Information
    FULL_NAME VARCHAR2(100) NOT NULL,
    COMPANY_NAME VARCHAR2(100) NOT NULL,
    PURPOSE_OF_VISIT VARCHAR2(100) NOT NULL,
    HOST_NAME VARCHAR2(100) NOT NULL,
    PHONE_NUMBER VARCHAR2(15) NOT NULL,
    ADDRESS VARCHAR2(255) NOT NULL,
    
    -- Nationality & Document Verification
    NATIONALITY VARCHAR2(20) NOT NULL, -- 'Indian' or 'Foreign Visitor'
    AADHAAR_NUMBER VARCHAR2(12),
    PAN_NUMBER VARCHAR2(10),
    PASSPORT_NUMBER VARCHAR2(20),
    VISA_NUMBER VARCHAR2(20),
    COUNTRY VARCHAR2(50),
    DOC_VERIFIED CHAR(1) DEFAULT 'N' CHECK (DOC_VERIFIED IN ('Y', 'N')), -- 'Y' if manually verified
    
    -- Photo Capture
    PHOTO_PATH VARCHAR2(255), -- Local path to offline storage, nullable initially
    
    -- Block Access Selection
    ALLOWED_BLOCKS VARCHAR2(500) NOT NULL, -- Comma-separated blocks or JSON
    
    -- Locker & Phone Deposit
    PHONE_DEPOSITED CHAR(1) DEFAULT 'N' CHECK (PHONE_DEPOSITED IN ('Y', 'N')),
    LOCKER_NUMBER VARCHAR2(20),
    
    -- Visit Validity
    PASS_VALID_FROM VARCHAR2(50) NOT NULL, -- e.g. '2026-03-07 10:00'
    PASS_VALID_UNTIL VARCHAR2(50) NOT NULL,
    MULTI_ENTRY_ALLOWED CHAR(1) DEFAULT 'N' CHECK (MULTI_ENTRY_ALLOWED IN ('Y', 'N')),
    
    -- Metadata
    STATUS VARCHAR2(30) DEFAULT 'WAITING_FOR_PHOTO' CHECK (STATUS IN ('WAITING_FOR_PHOTO', 'PASS_READY', 'VISITOR_INSIDE', 'VISITOR_EXITED')),
    CREATED_BY_OFFICER VARCHAR2(100),
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Index to optimize querying today's visitors for duplicates
CREATE INDEX idx_visitors_valid_from ON VISITORS (PASS_VALID_FROM);
CREATE INDEX idx_visitors_phone ON VISITORS (PHONE_NUMBER);

-- Commit
COMMIT;
