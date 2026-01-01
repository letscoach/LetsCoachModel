#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check actual transactions created - no JOIN duplicates
"""

import sys
sys.path.append(r'C:\Users\gideo\PycharmProjects\LetsCoachModel\Helpers')
from SQL_db import exec_select_query

print("=" * 80)
print("🔍 בדיקת Transactions אמיתיות (ללא JOIN)")
print("=" * 80)

# Get ONLY transactions without JOIN
query = """
    SELECT id, user_id, token_coin_id, amount, timestamp, description, transaction_type
    FROM transactions
    WHERE transaction_type = 'Prize' 
    AND description LIKE '%Competition%1667%'
    ORDER BY id
"""

transactions = exec_select_query(query)

print(f"\n✅ נמצאו {len(transactions)} transactions אמיתיות:\n")

for trans in transactions:
    if isinstance(trans, dict):
        t_id = trans.get('id')
        user_id = trans.get('user_id')
        amount = trans.get('amount')
        description = trans.get('description')
        timestamp = trans.get('timestamp')
    else:
        t_id, user_id, _, amount, timestamp, description, _ = trans
    
    print(f"Transaction ID: {t_id}")
    print(f"User ID: {user_id}")
    print(f"Amount: {amount} MATIC")
    print(f"Description: {description}")
    print(f"Timestamp: {timestamp}")
    print("-" * 80)

print("\n" + "=" * 80)
print("✅ בדיקה הסתיימה!")
print("=" * 80)
