-- ============================================
-- Donor Deduplication Tables for Supabase
-- ============================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. PERSON_MASTER: Central identity table
-- ============================================
CREATE TABLE IF NOT EXISTS person_master (
    master_person_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_first_name VARCHAR(100),
    canonical_middle_name VARCHAR(100),
    canonical_last_name VARCHAR(100),
    canonical_suffix VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    merge_confidence DECIMAL(5,4),
    is_verified BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- ============================================
-- 2. PERSON_ALIASES: Name variants mapping
-- ============================================
CREATE TABLE IF NOT EXISTS person_aliases (
    alias_id SERIAL PRIMARY KEY,
    master_person_id UUID REFERENCES person_master(master_person_id),
    alias_name VARCHAR(255) NOT NULL,
    alias_first_name VARCHAR(100),
    alias_middle_name VARCHAR(100),
    alias_last_name VARCHAR(100),
    alias_suffix VARCHAR(20),
    source_table VARCHAR(100),
    source_id BIGINT,
    match_type VARCHAR(50), -- 'exact', 'fuzzy', 'manual'
    confidence_score DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(alias_name, source_table, source_id)
);

-- ============================================
-- 3. PERSON_ADDRESSES: Normalized addresses
-- ============================================
CREATE TABLE IF NOT EXISTS person_addresses (
    address_id SERIAL PRIMARY KEY,
    master_person_id UUID REFERENCES person_master(master_person_id),
    house_number VARCHAR(20),
    street_name VARCHAR(255),
    unit VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    full_address TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    source_table VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 4. PERSON_CLUSTER_MEMBERS: Grouping duplicates
-- ============================================
CREATE TABLE IF NOT EXISTS person_cluster_members (
    cluster_id SERIAL PRIMARY KEY,
    master_person_id UUID REFERENCES person_master(master_person_id),
    member_name VARCHAR(255),
    member_address TEXT,
    source_table VARCHAR(100),
    source_id BIGINT,
    similarity_score DECIMAL(5,4),
    cluster_method VARCHAR(50), -- 'name_fuzzy', 'address_match', 'manual'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 5. DONATIONS_NORMALIZED: Cleaned donations
-- ============================================
CREATE TABLE IF NOT EXISTS donations_normalized (
    donation_id SERIAL PRIMARY KEY,
    raw_id BIGINT, -- FK to nc_boe_donations_raw.id
    master_person_id UUID REFERENCES person_master(master_person_id),
    
    -- Parsed donor info
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    last_name VARCHAR(100),
    suffix VARCHAR(20),
    
    -- Normalized address
    house_number VARCHAR(20),
    street_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    
    -- Donation details (from raw)
    amount DECIMAL(12,2),
    donation_date DATE,
    transaction_type VARCHAR(100),
    employer_name VARCHAR(255),
    profession VARCHAR(255),
    
    -- Committee info
    committee_name VARCHAR(255),
    committee_sboe_id VARCHAR(50),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_person_aliases_master ON person_aliases(master_person_id);
CREATE INDEX IF NOT EXISTS idx_person_aliases_name ON person_aliases(alias_name);
CREATE INDEX IF NOT EXISTS idx_person_addresses_master ON person_addresses(master_person_id);
CREATE INDEX IF NOT EXISTS idx_donations_master ON donations_normalized(master_person_id);
CREATE INDEX IF NOT EXISTS idx_donations_raw ON donations_normalized(raw_id);
CREATE INDEX IF NOT EXISTS idx_person_master_name ON person_master(canonical_last_name, canonical_first_name);
