# 🏦 लोन सहायक — Loan Support Agent

A **Hindi-first conversational AI agent** that guides loan customers through a structured verification flow — confirming disbursement amounts, tranch schedules, EMI details, and bank information.

**Stack:** Streamlit · LangGraph · GPT-4o · Supabase

---

## 🚀 Complete Setup Guide

### Prerequisites

- **Python 3.11+** installed
- **OpenAI API key** with GPT-4o access
- **Supabase account** (free tier works)

---

### Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in.
2. Click **"New Project"**.
3. Choose a name (e.g., `loan-support-agent`), set a database password, and pick a region.
4. Wait for the project to finish provisioning (~2 minutes).

### Step 2: Create Database Tables & Seed Data

1. In your Supabase dashboard, go to **SQL Editor** (left sidebar).
2. Click **"New query"**.
3. Open the file `supabase/schema.sql` from this project.
4. **Copy the entire contents** and paste into the SQL editor.
5. Click **"Run"** (or Ctrl+Enter).
6. You should see a success message. This creates 3 tables (`loans`, `conversations`, `escalations`) and inserts the sample loan record for **Pranshu Sharma (SFC202508986)**.

#### Verify the seed data:
In the SQL Editor, run:
```sql
SELECT loan_id, borrower_name, effective_loan_amount FROM public.loans;
```
You should see:
| loan_id | borrower_name | effective_loan_amount |
|---|---|---|
| SFC202508986 | Pranshu Sharma | 982658.00 |

### Step 3: Get Your Supabase Credentials

1. In Supabase dashboard, go to **Settings → API** (left sidebar → ⚙️ Settings → API).
2. Copy:
   - **Project URL** — looks like `https://abcdefgh.supabase.co`
   - **`anon` public key** (under "Project API keys") — a long `eyJ...` string

### Step 4: Get Your OpenAI API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys).
2. Create a new API key (or use an existing one).
3. Make sure your account has access to `gpt-4o`.

### Step 5: Configure Environment Variables

1. In the project root, copy the example file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your keys:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...your-anon-key
   ```

### Step 6: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🎮 How to Use

1. **Login:** Enter Loan ID `SFC202508986` and click "लॉग इन करें".
2. **Chat:** The agent will greet you in Hindi and walk through the verification flow:
   - ✅ Confirm loan amount (₹9,82,658)
   - ✅ Confirm tranch breakdown (2 tranches)
   - ✅ Confirm EMI details (pre-EMI + regular EMI)
   - ✅ Confirm bank & IFSC code
3. **Respond in Hindi or Hinglish** — the agent understands both.
4. **If you disagree** with any information, the agent will escalate to the support team.
5. **If you close the browser** mid-conversation, you can return and resume from where you left off.

---

## 📁 Project Structure

```
Loan_Support_Agent/
├── app.py                  # Streamlit entry point (login + chat UI)
├── agent/
│   ├── graph.py            # LangGraph ReAct agent setup
│   ├── prompts.py          # Hindi system prompt builder
│   └── tools.py            # Agent tools (confirm_step, escalate)
├── db/
│   └── supabase_client.py  # Supabase client + all DB operations
├── supabase/
│   └── schema.sql          # Database schema + seed data
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  Streamlit UI (Hindi Chat)                          │
│  • Login (Loan ID lookup)                           │
│  • Chat interface with progress tracking            │
│  • Session state management                         │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  LangGraph ReAct Agent                              │
│  • GPT-4o with Hindi system prompt                  │
│  • Structured 5-step conversation flow              │
│  • Tools: confirm_step, escalate_to_support         │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  Supabase (PostgreSQL)                              │
│  • loans — loan records                             │
│  • conversations — smart state (not raw messages)   │
│  • escalations — discrepancy tickets                │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Loan Data (Test Record)

| Field | Value |
|---|---|
| Borrower | Pranshu Sharma |
| Loan ID | SFC202508986 |
| Total Loan | ₹10,25,000 |
| Insurance Premium | ₹38,342 |
| Processing Fee | ₹4,000 |
| **Effective Amount** | **₹9,82,658** |
| Tranch 1 | ₹7,00,000 → net ₹6,61,658 (Nov 2025) |
| Tranch 2 | ₹3,25,000 → net ₹3,21,000 (Dec 2025) |
| Pre-EMI | ₹15,999 on 4 Dec 2025 |
| Regular EMI | ₹23,456 from 3 Jan 2026 |
| Bank | ICICI Bank, Neem-ka-thana (ICIC0006720) |