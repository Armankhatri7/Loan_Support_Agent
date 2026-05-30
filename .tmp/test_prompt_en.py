import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.prompts import build_system_prompt
loan_data = {'loan_id':'SFC202600904','borrower_name':'Maya Patel','preferred_language':'en','loan_amount':750000,'insurance_premium':0,'processing_fee':0,'effective_loan_amount':750000,'tranches':[],'bank_account_masked':'','bank_name':'','branch_name':'','ifsc_code':'','state':'Maharashtra','emi_amount':0,'emi_start_date':'','pre_emi_amount':0,'pre_emi_date':'','nach_registered':False,'loan_date':'22 May 2026'}
prompt = build_system_prompt(loan_data,None,loan_data['preferred_language'])
print('\n'.join(prompt.splitlines()[:30]))
