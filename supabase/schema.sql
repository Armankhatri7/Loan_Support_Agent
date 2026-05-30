-- ============================================================
-- Loan Support Agent — Supabase Schema (POC)
-- ============================================================
-- Run this ENTIRE script in the Supabase SQL Editor.
-- It creates the tables and inserts the sample loan record.
-- ============================================================


-- ============================================
-- 1. LOANS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.loans (
    loan_id TEXT PRIMARY KEY,
    borrower_name TEXT NOT NULL,
    preferred_language TEXT DEFAULT 'hi',

    -- Amounts
    loan_amount NUMERIC(12,2) NOT NULL,
    insurance_premium NUMERIC(12,2) DEFAULT 0,
    processing_fee NUMERIC(12,2) DEFAULT 0,
    effective_loan_amount NUMERIC(12,2) NOT NULL,

    -- Tranch breakdown (JSONB array)
    tranches JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Bank details
    bank_account_masked TEXT NOT NULL,
    bank_name TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    ifsc_code TEXT NOT NULL,
    state TEXT,

    -- EMI
    emi_amount NUMERIC(12,2) NOT NULL,
    emi_start_date TEXT NOT NULL,
    pre_emi_amount NUMERIC(12,2),
    pre_emi_date TEXT,

    -- NACH
    nach_registered BOOLEAN DEFAULT FALSE,

    -- Meta
    loan_date TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================
-- 2. CONVERSATIONS TABLE
-- Smart storage: only key details, not raw messages
-- ============================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    loan_id TEXT REFERENCES public.loans(loan_id) ON DELETE CASCADE NOT NULL,
    current_step TEXT DEFAULT 'greet',
    confirmed_steps JSONB DEFAULT '[]'::jsonb,
    conversation_summary TEXT DEFAULT '',
    status TEXT DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'escalated', 'abandoned')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_loan_id
    ON public.conversations(loan_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status
    ON public.conversations(status);


-- ============================================
-- 3. ESCALATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.escalations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    loan_id TEXT REFERENCES public.loans(loan_id) ON DELETE CASCADE NOT NULL,
    conversation_id BIGINT REFERENCES public.conversations(id) ON DELETE SET NULL,
    issue_type TEXT NOT NULL
        CHECK (issue_type IN (
            'amount_mismatch',
            'bank_mismatch',
            'emi_dispute',
            'tranch_dispute',
            'other'
        )),
    description TEXT NOT NULL,
    user_claim TEXT,
    system_value TEXT,
    status TEXT DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================
-- 4. AUTO-UPDATE updated_at ON conversations
-- ============================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_conversations_updated_at
    BEFORE UPDATE ON public.conversations
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();


-- ============================================
-- 5. SEED DATA — Pranshu Sharma (SFC202508986)
-- ============================================
-- Correct math:
--   Total loan:       10,25,000
--   Insurance:           38,342  (deducted from tranch 1)
--   Processing fee:       4,000  (deducted from tranch 2)
--   Effective amount:  9,82,658
--
--   Tranch 1 gross:   7,00,000 → net: 6,61,658
--   Tranch 2 gross:   3,25,000 → net: 3,21,000
--   Total net:        9,82,658  ✓
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
    'SFC202508986',
    'Pranshu Sharma',
    'hi',
    1025000.00,
    38342.00,
    4000.00,
    982658.00,
    '[
        {
            "tranch_number": 1,
            "gross_amount": 700000,
            "deductions": {"insurance_premium": 38342},
            "net_amount": 661658,
            "scheduled_month": "November 2025",
            "status": "pending"
        },
        {
            "tranch_number": 2,
            "gross_amount": 325000,
            "deductions": {"processing_fee": 4000},
            "net_amount": 321000,
            "scheduled_month": "December 2025",
            "status": "pending"
        }
    ]'::jsonb,
    'xxx-222-xxx-244',
    'ICICI Bank',
    'Neem-ka-thana',
    'ICIC0006720',
    'Rajasthan',
    23456.00,
    '3 January 2026',
    15999.00,
    '4 December 2025',
    TRUE,
    '10 November 2025'
)
ON CONFLICT (loan_id) DO NOTHING;
