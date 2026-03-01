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
    PHOTO_PATH VARCHAR2(255) NOT NULL, -- Local path to offline storage
    
    -- Block Access Selection
    ALLOWED_BLOCKS VARCHAR2(500) NOT NULL, -- Comma-separated blocks or JSON
    
    -- Locker & Phone Deposit
    PHONE_DEPOSITED CHAR(1) DEFAULT 'N' CHECK (PHONE_DEPOSITED IN ('Y', 'N')),
    LOCKER_NUMBER VARCHAR2(20),
    
    -- Visit Validity
    VISIT_DATE DATE DEFAULT SYSDATE NOT NULL,
    EXPECTED_EXIT_TIME VARCHAR2(10) NOT NULL, -- e.g., '18:00'
    MULTI_ENTRY_ALLOWED CHAR(1) DEFAULT 'N' CHECK (MULTI_ENTRY_ALLOWED IN ('Y', 'N')),
    
    -- Metadata
    STATUS VARCHAR2(20) DEFAULT 'PENDING' CHECK (STATUS IN ('PENDING', 'APPROVED', 'REJECTED', 'DRAFT')),
    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Index to optimize querying today's visitors for duplicates
CREATE INDEX idx_visitors_date ON VISITORS (TRUNC(VISIT_DATE));
CREATE INDEX idx_visitors_phone ON VISITORS (PHONE_NUMBER);

-- Commit
COMMIT;
