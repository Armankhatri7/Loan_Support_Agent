-- ============================================================
-- Test Seed Data — Loans with MISSING fields
-- ============================================================
-- Run this in the Supabase SQL Editor AFTER the main schema.sql.
--
-- These entries have intentionally missing data (NULL, 0, 'N/A')
-- so the agent triggers the `request_missing_loan_detail` and
-- `save_loan_detail` tool flow.
--
-- The _is_missing() function in prompts.py treats these as missing:
--   • NULL
--   • Empty string, 'N/A', 'NA', 'MISSING'
--   • Numeric 0
-- ============================================================


-- ============================================
-- TEST 1: Hindi user — Missing EMI + Bank details
-- ============================================
-- Loan amount & tranches are PRESENT → agent confirms them.
-- EMI (emi_amount, pre_emi), bank (bank_name, branch, IFSC) are MISSING → agent asks customer.
--
-- Login ID: SFC202509001
-- Expected agent behavior:
--   STEP 2 (Loan Amount): Confirms ₹7,50,000 with deductions → ₹7,22,000
--   STEP 3 (Tranches):    Confirms 2 tranches (Feb + Mar 2026)
--   STEP 4 (EMI):         Asks customer for EMI amount, pre-EMI, dates
--   STEP 5 (Bank):        Asks customer for bank name, branch, IFSC
--   STEP 6 (Health Check): Asks about loan experience issues
--   STEP 7 (Queries):     Asks for additional queries
--   STEP 8 (Closing):     Thanks and ends
-- ============================================

INSERT INTO public.loans (
    loan_id,
    borrower_name,
    preferred_language,
    loan_amount,
    insurance_premium,
    processing_fee,
    effective_loan_amount,
    tranches,
    bank_account_masked,
    bank_name,
    branch_name,
    ifsc_code,
    state,
    emi_amount,
    emi_start_date,
    pre_emi_amount,
    pre_emi_date,
    nach_registered,
    loan_date
) VALUES (
    'SFC202509001',
    'Ravi Kumar',
    'hi',
    750000.00,          -- ✅ Present
    25000.00,           -- ✅ Present
    3000.00,            -- ✅ Present
    722000.00,          -- ✅ Present (750000 - 25000 - 3000)
    '[
        {
            "tranch_number": 1,
            "gross_amount": 450000,
            "deductions": {"insurance_premium": 25000},
            "net_amount": 425000,
            "scheduled_month": "February 2026",
            "status": "pending"
        },
        {
            "tranch_number": 2,
            "gross_amount": 300000,
            "deductions": {"processing_fee": 3000},
            "net_amount": 297000,
            "scheduled_month": "March 2026",
            "status": "pending"
        }
    ]'::jsonb,          -- ✅ Present
    'xxx-333-xxx-456',  -- ✅ Present
    'N/A',              -- ❌ MISSING — agent should ask
    'N/A',              -- ❌ MISSING — agent should ask
    'N/A',              -- ❌ MISSING — agent should ask
    'Uttar Pradesh',
    0,                  -- ❌ MISSING (0 = missing) — agent should ask
    'N/A',              -- ❌ MISSING — agent should ask
    NULL,               -- ❌ MISSING — agent should ask
    NULL,               -- ❌ MISSING — agent should ask
    FALSE,
    '15 January 2026'
)
ON CONFLICT (loan_id) DO NOTHING;


-- ============================================
-- TEST 2: English user — Missing Loan Amount + Tranches
-- ============================================
-- Bank details & EMI are PRESENT → agent confirms them.
-- Loan amount and tranches are MISSING → agent asks customer.
--
-- Login ID: SFC202509002
-- Expected agent behavior:
--   STEP 2 (Loan Amount): Asks customer for total loan amount
--   STEP 3 (Tranches):    Asks customer for tranche details (JSON)
--   STEP 4 (EMI):         Confirms ₹18,500 EMI + ₹12,000 pre-EMI
--   STEP 5 (Bank):        Confirms SBI, Connaught Place, SBIN0001234
--   STEP 6 (Health Check): Asks about loan experience issues
--   STEP 7 (Queries):     Asks for additional queries
--   STEP 8 (Closing):     Thanks and ends
-- ============================================

INSERT INTO public.loans (
    loan_id,
    borrower_name,
    preferred_language,
    loan_amount,
    insurance_premium,
    processing_fee,
    effective_loan_amount,
    tranches,
    bank_account_masked,
    bank_name,
    branch_name,
    ifsc_code,
    state,
    emi_amount,
    emi_start_date,
    pre_emi_amount,
    pre_emi_date,
    nach_registered,
    loan_date
) VALUES (
    'SFC202509002',
    'Anita Desai',
    'en',
    0,                  -- ❌ MISSING (0 = missing) — agent should ask
    0,                  -- ❌ MISSING
    0,                  -- ❌ MISSING
    0,                  -- ❌ MISSING
    '[]'::jsonb,        -- ❌ MISSING (empty array) — agent should ask
    'xxx-444-xxx-789',  -- ✅ Present
    'State Bank of India',  -- ✅ Present
    'Connaught Place',      -- ✅ Present
    'SBIN0001234',          -- ✅ Present
    'Delhi',
    18500.00,           -- ✅ Present
    '5 March 2026',     -- ✅ Present
    12000.00,           -- ✅ Present
    '5 February 2026',  -- ✅ Present
    TRUE,
    '20 December 2025'
)
ON CONFLICT (loan_id) DO NOTHING;
