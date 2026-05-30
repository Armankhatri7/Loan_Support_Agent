# 🏦 लोन सहायक — Loan Support Agent

A **multilingual conversational AI agent** (Hindi & English) that guides loan customers through a structured verification flow — confirming disbursement amounts, tranch schedules, EMI details, and bank information. The agent also collects missing loan details, performs a post-verification health check, and handles customer queries — all within a single guided conversation.

**Stack:** Streamlit · LangGraph · GPT-4o · Supabase (PostgreSQL)

---

## ✨ What the Agent Does

| Capability | Description |
|---|---|
| **Loan Detail Confirmation** | Presents loan amount, tranch breakdown, EMI schedule, and bank details one step at a time, asking the customer to confirm each. |
| **Missing Data Collection** | Detects fields missing from the database (e.g., EMI amount, IFSC code) and politely asks the customer to provide them. Saves the values back to the database. |
| **Dispute Escalation** | If the customer disputes any presented information, the agent escalates the issue to the support team with full context and ends the conversation. |
| **Health Check** | After all loan details are confirmed, asks the customer if they faced any issues during their loan experience. Logs any reported issues for the support team. |
| **Additional Queries** | Asks if the customer has any remaining questions. Logs queries for support team follow-up. |
| **Language Awareness** | Responds in Hindi (Devanagari) or English based on the customer's `preferred_language` setting. Understands Hindi, Hinglish (Romanized Hindi), and English input regardless of output language. |
| **Conversation Resume** | If the customer closes the browser mid-conversation, they can log in again and resume from the exact step where they left off. |

---

## 🔄 Conversation Flow (8 Steps)

The agent follows a strict sequential flow. It does **not** skip steps and does **not** move forward until the current step is explicitly confirmed or resolved.

```
STEP 1: GREET
  │  Greet customer by name, mention Loan ID & date
  │  (Proceeds to Step 2 immediately — no user reply needed)
  ▼
STEP 2: CONFIRM LOAN AMOUNT
  │  Present total loan amount, deductions, effective amount
  │  If data is MISSING → ask customer, save via tool, then confirm
  │  ✅ Confirmed → Step 3  |  ❌ Disputed → Escalate & end
  ▼
STEP 3: CONFIRM TRANCHES
  │  Present 2-tranche breakdown (gross, deductions, net, month)
  │  If data is MISSING → ask customer for tranche details
  │  ✅ Confirmed → Step 4  |  ❌ Disputed → Escalate & end
  ▼
STEP 4: CONFIRM EMI
  │  Present pre-EMI and regular EMI amounts with dates
  │  If data is MISSING → ask customer for EMI details
  │  ✅ Confirmed → Step 5  |  ❌ Disputed → Escalate & end
  ▼
STEP 5: CONFIRM BANK DETAILS
  │  Remind to maintain balance, present IFSC / bank / branch
  │  If data is MISSING → ask customer for bank details
  │  ✅ Confirmed → Step 6  |  ❌ Disputed → Escalate & end
  ▼
STEP 6: HEALTH CHECK                              ← NEW
  │  "Did you face any issues during your loan experience?"
  │  If YES → apologize, log feedback for support team
  │  If NO  → thank for positive feedback
  │  → Step 7
  ▼
STEP 7: ADDITIONAL QUERIES                        ← NEW
  │  "Do you have any other queries about your loan?"
  │  If YES → log query for support team follow-up
  │  If NO  → acknowledge
  │  → Step 8
  ▼
STEP 8: CLOSING
     Thank customer, give brief summary, say goodbye
```

---

## 🛠️ Agent Tools (5 Tools)

The LangGraph ReAct agent has access to these tools. Each tool is bound to the current `loan_id` and `conversation_id` via closures — the LLM never needs to guess these values.

| Tool | Purpose | Terminates Flow? |
|---|---|---|
| `request_missing_loan_detail` | Logs that a field is missing and returns a language-appropriate message asking the customer to provide the value | No |
| `save_loan_detail` | Saves a customer-provided value to the `loans` table. Handles numeric, boolean, and JSON (tranches) normalization | No |
| `confirm_step` | Marks a conversation step as confirmed in the database and advances to the next step | No |
| `escalate_to_support` | Creates an escalation record for disputes. Marks the conversation as escalated | **Yes** |
| `log_customer_feedback` | Logs health check issues or additional queries to the escalations table **without** ending the conversation | No |

---

## 🚀 Setup Guide

### Prerequisites

- **Python 3.11+** installed
- **OpenAI API key** with GPT-4o access
- **Supabase credentials** (Project URL and `anon` public key)

### Step 1: Configure Environment Variables

Create a `.env` file in the project root (or copy from `.env.example`):

```
OPENAI_API_KEY=sk-your-actual-key-here
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...your-anon-key
```

> **Where to find Supabase credentials:** In your Supabase dashboard → **Settings → API**. Copy the **Project URL** and the **`anon` public key**.

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🎮 How to Use

1. **Login:** Enter a Loan ID (e.g., `SFC202508986`) and click **"🔑 लॉग इन करें"**.
2. **Chat:** The agent will greet you and walk through the 8-step verification flow.
3. **Respond naturally** — the agent understands Hindi, Hinglish, and English input.
4. **If you disagree** with any information, the agent will escalate to the support team.
5. **If you close the browser** mid-conversation, you can return and resume from where you left off.
6. **Progress bar** at the top shows your current step (💰 → 📊 → 📅 → 🏦 → 🩺 → ❓ → ✅).

---

## 📁 Project Structure

```
Loan_Support_Agent/
├── app.py                      # Streamlit entry point (login + chat UI + progress bar)
├── agent/
│   ├── graph.py                # LangGraph ReAct agent setup (GPT-4o + tools)
│   ├── prompts.py              # Dynamic system prompt builder (bilingual, data-aware)
│   └── tools.py                # 5 agent tools (confirm, escalate, save, request, feedback)
├── db/
│   └── supabase_client.py      # Supabase client singleton + all DB operations
├── supabase/
│   ├── schema.sql              # Database schema + seed data (Pranshu Sharma)
│   └── test_seed.sql           # Test entries with missing data (Ravi Kumar, Anita Desai)
├── .env                        # Environment variables (not committed)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────┐
│  Streamlit UI                                             │
│  • Login page (Loan ID lookup)                            │
│  • Chat interface with bilingual support                  │
│  • Step progress bar (💰 📊 📅 🏦 🩺 ❓ ✅)               │
│  • Session state management + conversation resume         │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────────────┐
│  LangGraph ReAct Agent                                    │
│  • GPT-4o (temperature 0.3) with dynamic system prompt    │
│  • 8-step structured conversation flow                    │
│  • 5 tools: confirm_step, escalate_to_support,            │
│    request_missing_loan_detail, save_loan_detail,         │
│    log_customer_feedback                                  │
│  • Language-aware prompt (Hindi / English)                 │
│  • Missing-field-aware step instructions                  │
└──────────────────────┬────────────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────────────┐
│  Supabase (PostgreSQL)                                    │
│  • loans        — loan records + customer data            │
│  • conversations — step-level progress (not raw messages) │
│  • escalations  — dispute tickets + customer feedback     │
└───────────────────────────────────────────────────────────┘
```

### Key Technical Decisions

- **No raw messages stored** — the database stores only step-level progress (`current_step`, `confirmed_steps`, `conversation_summary`) and status. Full message history lives in Streamlit `session_state` during the active session.
- **Closure-bound tools** — `loan_id` and `conversation_id` are captured in tool closures at agent build time. The LLM never needs to guess or hallucinate these values.
- **Dynamic system prompt** — the prompt is rebuilt per session with actual loan data injected. Each step's instructions change based on whether data is present (→ confirm) or missing (→ request from customer).
- **Non-terminal feedback logging** — `log_customer_feedback` inserts into the `escalations` table with `issue_type='other'` but does **not** change conversation status, allowing the flow to continue. This is distinct from `escalate_to_support` which marks the conversation as escalated and terminates the flow.

---

## 📊 Test Records

### Record 1 — Pranshu Sharma (Complete Data, Hindi)

| Field | Value |
|---|---|
| **Loan ID** | `SFC202508986` |
| **Language** | Hindi (`hi`) |
| Borrower | Pranshu Sharma |
| Total Loan | ₹10,25,000 |
| Insurance Premium | ₹38,342 |
| Processing Fee | ₹4,000 |
| **Effective Amount** | **₹9,82,658** |
| Tranch 1 | ₹7,00,000 → net ₹6,61,658 (Nov 2025) |
| Tranch 2 | ₹3,25,000 → net ₹3,21,000 (Dec 2025) |
| Pre-EMI | ₹15,999 on 4 Dec 2025 |
| Regular EMI | ₹23,456 from 3 Jan 2026 |
| Bank | ICICI Bank, Neem-ka-thana (ICIC0006720) |

**All fields present** — agent confirms each step without requesting any missing data.

---

### Record 2 — Ravi Kumar (Missing EMI + Bank, Hindi)

| Field | Value | Status |
|---|---|---|
| **Loan ID** | `SFC202509001` | |
| **Language** | Hindi (`hi`) | |
| Borrower | Ravi Kumar | |
| Total Loan | ₹7,50,000 | ✅ Present |
| Insurance Premium | ₹25,000 | ✅ Present |
| Processing Fee | ₹3,000 | ✅ Present |
| Effective Amount | ₹7,22,000 | ✅ Present |
| Tranch 1 | ₹4,50,000 → net ₹4,25,000 (Feb 2026) | ✅ Present |
| Tranch 2 | ₹3,00,000 → net ₹2,97,000 (Mar 2026) | ✅ Present |
| EMI Amount | `0` | ❌ Missing |
| EMI Start Date | `N/A` | ❌ Missing |
| Pre-EMI Amount | `NULL` | ❌ Missing |
| Pre-EMI Date | `NULL` | ❌ Missing |
| Bank Name | `N/A` | ❌ Missing |
| Branch Name | `N/A` | ❌ Missing |
| IFSC Code | `N/A` | ❌ Missing |

**Missing fields:** EMI details + Bank details. Agent will request these from the customer.

---

### Record 3 — Anita Desai (Missing Loan Amount + Tranches, English)

| Field | Value | Status |
|---|---|---|
| **Loan ID** | `SFC202509002` | |
| **Language** | English (`en`) | |
| Borrower | Anita Desai | |
| Total Loan | `0` | ❌ Missing |
| Insurance Premium | `0` | ❌ Missing |
| Processing Fee | `0` | ❌ Missing |
| Effective Amount | `0` | ❌ Missing |
| Tranches | `[]` (empty) | ❌ Missing |
| EMI Amount | ₹18,500 | ✅ Present |
| EMI Start Date | 5 March 2026 | ✅ Present |
| Pre-EMI Amount | ₹12,000 | ✅ Present |
| Pre-EMI Date | 5 February 2026 | ✅ Present |
| Bank Name | State Bank of India | ✅ Present |
| Branch | Connaught Place | ✅ Present |
| IFSC Code | SBIN0001234 | ✅ Present |

**Missing fields:** Loan amount + Tranch breakdown. Agent will request these from the customer in English.

---

## 🧪 Testing Guidelines

### How to Add Test Data

Run `supabase/test_seed.sql` in the Supabase SQL Editor to insert the two test records (Ravi Kumar and Anita Desai). Pranshu Sharma is already inserted by `supabase/schema.sql`.

Verify all three records exist:

```sql
SELECT loan_id, borrower_name, preferred_language, loan_amount, emi_amount, bank_name
FROM public.loans
ORDER BY loan_id;
```

Expected output:

| loan_id | borrower_name | preferred_language | loan_amount | emi_amount | bank_name |
|---|---|---|---|---|---|
| SFC202508986 | Pranshu Sharma | hi | 1025000.00 | 23456.00 | ICICI Bank |
| SFC202509001 | Ravi Kumar | hi | 750000.00 | 0.00 | N/A |
| SFC202509002 | Anita Desai | en | 0.00 | 18500.00 | State Bank of India |

---

### Test Case 1: Pranshu Sharma — Full Confirmation Flow (Hindi)

**Login ID:** `SFC202508986`

**Purpose:** Verify the happy path — all data is present, the agent confirms each step sequentially in Hindi.

**Expected agent behavior:**

| Step | Agent Action | You Should Reply |
|---|---|---|
| 1. Greet | Greets "Pranshu Sharma जी", mentions Loan ID and date, immediately presents loan amount | — |
| 2. Loan Amount | States ₹10,25,000 with deductions → ₹9,82,658. Asks "क्या यह राशि सही है?" | `हाँ` or `हां, सही है` |
| 3. Tranches | States 2 tranches (Nov + Dec 2025). Asks "क्या यह सही है?" | `हां` or `जी हां` |
| 4. EMI | States pre-EMI ₹15,999 (4 Dec) + EMI ₹23,456 (3 Jan). Asks confirmation | `हां, सही है` |
| 5. Bank | Reminds to maintain balance. States ICICI, ICIC0006720. Asks IFSC confirmation | `हां` or `जी, सही है` |
| 6. Health Check | Asks "क्या आपको लोन अनुभव के दौरान कोई समस्या हुई?" | `नहीं` (no issues) or `हां, मुझे देरी हुई` (report an issue) |
| 7. Additional Queries | Asks "क्या कोई और प्रश्न है?" | `नहीं` (no queries) or `हां, मुझे EMI बदलनी है` (raise a query) |
| 8. Closing | Thanks, gives summary, says goodbye | — |

**Test for dispute escalation:** At any confirmation step, reply with something like `नहीं, यह गलत है, मेरा लोन 12 लाख है` — the agent should escalate and end.

---

### Test Case 2: Ravi Kumar — Missing EMI + Bank Details (Hindi)

**Login ID:** `SFC202509001`

**Purpose:** Verify the agent correctly detects missing EMI and bank fields, requests them from the customer in Hindi, saves the values to the database, and then confirms.

**Expected agent behavior:**

| Step | Agent Action | You Should Reply |
|---|---|---|
| 1. Greet | Greets "Ravi Kumar जी", mentions Loan ID | — |
| 2. Loan Amount | Confirms ₹7,50,000 → ₹7,22,000 (data is present). Asks confirmation | `हां, सही है` |
| 3. Tranches | Confirms 2 tranches — Feb + Mar 2026 (data is present). Asks confirmation | `हां` |
| 4. EMI | **Detects EMI is missing.** Calls `request_missing_loan_detail`. Asks you for EMI amount and dates | Provide: `मेरी EMI 15000 रुपये है, 10 अप्रैल 2026 से शुरू` |
| | Agent calls `save_loan_detail` to save the values. Asks for pre-EMI details | Provide: `Pre-EMI 8000 रुपये, 10 मार्च 2026 को` |
| | Agent saves and confirms. Asks final EMI confirmation | `हां, सही है` |
| 5. Bank | **Detects bank details are missing.** Asks for bank name, branch, and IFSC | Provide: `Punjab National Bank, Lucknow branch, IFSC PUNB0123400` |
| | Agent saves and confirms. Asks IFSC confirmation | `हां, सही है` |
| 6. Health Check | Asks about any issues | `नहीं, कोई समस्या नहीं` |
| 7. Additional Queries | Asks for more queries | `नहीं, धन्यवाद` |
| 8. Closing | Thanks and goodbye | — |

**Verify data was saved:** After the conversation, run in SQL Editor:

```sql
SELECT emi_amount, emi_start_date, pre_emi_amount, bank_name, branch_name, ifsc_code
FROM public.loans
WHERE loan_id = 'SFC202509001';
```

The previously missing fields should now contain the values you provided during the chat.

---

### Test Case 3: Anita Desai — Missing Loan Amount + Tranches (English)

**Login ID:** `SFC202509002`

**Purpose:** Verify the agent detects missing loan amount and tranch data, requests them in English, handles JSON tranch input, and confirms the rest of the present data.

**Expected agent behavior:**

| Step | Agent Action | You Should Reply |
|---|---|---|
| 1. Greet | Greets "Anita Desai", mentions Loan ID (in English) | — |
| 2. Loan Amount | **Detects loan amount is missing.** Calls `request_missing_loan_detail`. Asks you for the total loan amount | Provide: `My total loan amount is 500000 rupees` |
| | Agent saves. May also ask for insurance premium and processing fee | Provide: `Insurance is 15000, processing fee is 2000` |
| | Agent saves and calculates effective amount. Asks confirmation | `Yes, that's correct` |
| 3. Tranches | **Detects tranches are missing.** Asks for tranche details | Provide: `Tranche 1: gross 300000, net 285000 in April 2026. Tranche 2: gross 200000, net 198000 in May 2026` |
| | Agent saves as JSON. Asks confirmation | `Yes` |
| 4. EMI | Confirms ₹18,500 EMI + ₹12,000 pre-EMI (data is present). Asks confirmation | `Yes, correct` |
| 5. Bank | Confirms SBI, Connaught Place, SBIN0001234 (data is present). Asks confirmation | `Yes` |
| 6. Health Check | Asks about any issues (in English) | `No, everything was fine` or `Yes, there was a delay in processing` |
| 7. Additional Queries | Asks for more queries (in English) | `No, I'm good` or `Yes, when will my first tranche be disbursed?` |
| 8. Closing | Thanks and goodbye (in English) | — |

**Verify data was saved:** After the conversation, run in SQL Editor:

```sql
SELECT loan_amount, insurance_premium, processing_fee, effective_loan_amount, tranches
FROM public.loans
WHERE loan_id = 'SFC202509002';
```

The previously zero/empty fields should now contain the values you provided.

---

### What to Verify Across All Tests

| Check | How to Verify |
|---|---|
| **Language compliance** | Ravi Kumar's session must be entirely in Hindi (Devanagari). Anita Desai's must be entirely in English. |
| **Missing data detection** | Agent should NOT present "₹0" or "N/A" as real values. It should call `request_missing_loan_detail` and ask the customer. |
| **Data persistence** | After the agent calls `save_loan_detail`, query the `loans` table to confirm the values were saved correctly. |
| **Step progression** | The progress bar chips (💰 📊 📅 🏦 🩺 ❓ ✅) should light up as each step is confirmed. |
| **Health check logging** | If you report an issue at Step 6, check the `escalations` table for a record with `issue_type = 'other'` and description starting with `[customer_feedback]`. |
| **Additional query logging** | If you raise a query at Step 7, check the `escalations` table for a record with description starting with `[additional_query]`. |
| **Escalation (dispute)** | If you dispute a confirmed field (e.g., "No, my loan amount is different"), the agent should call `escalate_to_support`, the conversation should end, and the progress bar should show the escalated (red) state. |
| **Conversation resume** | Close the browser mid-conversation, then log in again with the same Loan ID. The agent should resume from the last confirmed step, not restart from the beginning. |

**SQL to check escalations and feedback:**

```sql
SELECT id, loan_id, issue_type, description, status, created_at
FROM public.escalations
ORDER BY created_at DESC;
```

**SQL to check conversation progress:**

```sql
SELECT id, loan_id, current_step, confirmed_steps, status
FROM public.conversations
ORDER BY created_at DESC;
```