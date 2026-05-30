import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.prompts import build_system_prompt

loan_data = {
    "loan_id": "TEST001",
    "borrower_name": "Test User",
    "loan_amount": None,
    "insurance_premium": None,
    "processing_fee": None,
    "effective_loan_amount": None,
    "tranches": [],
    "bank_account_masked": None,
    "bank_name": None,
    "branch_name": None,
    "ifsc_code": None,
    "emi_amount": None,
    "emi_start_date": None,
    "pre_emi_amount": None,
    "pre_emi_date": None,
    "loan_date": None,
    "nach_registered": False,
    "preferred_language": "hi",
}

try:
    prompt = build_system_prompt(loan_data, None, loan_data['preferred_language'])
    print('Prompt built successfully. Length:', len(prompt))
    # print(prompt)
except Exception as e:
    import traceback
    traceback.print_exc()
