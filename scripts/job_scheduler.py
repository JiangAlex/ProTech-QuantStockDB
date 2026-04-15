#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
股票數據抓取工作分配表
期間: 2023-04-14 ~ 2026-04-14 (三年歷史資料)

週期分類:
- 日線 (Daily): 每交易日
- 月線 (Monthly): 每月
- 季線 (Quarterly): 每季
'''

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

START_DATE = date(2023, 4, 14)
END_DATE = date(2026, 4, 14)

# ==============================================================================
# 工作分配: 日線抓取 (每日)
# ==============================================================================
DAILY_JOBS = []

current = START_DATE
while current <= END_DATE:
    # 排除週末
    if current.weekday() < 5:
        DAILY_JOBS.append({
            'date': current,
            'type': 'daily_kline',
            'tables': ['daily_kline', 'institutional_investors']
        })
    current += timedelta(days=1)

# ==============================================================================
# 工作分配: 月營收 (每月)
# ==============================================================================
MONTHLY_JOBS = []

current = START_DATE
while current <= END_DATE:
    # 每月15日執行 (月營收通常在15日前公布)
    if current.day == 15 and current.weekday() < 5:
        MONTHLY_JOBS.append({
            'date': current,
            'type': 'monthly_revenue',
            'tables': ['monthly_revenue', 'monthly_revenue_tpex']
        })
    current += timedelta(days=1)

# ==============================================================================
# 工作分配: 季獲利 (每季)
# ==============================================================================
QUARTERLY_JOBS = []

# 季度: Q1=3月, Q2=6月, Q3=9月, Q4=12月
quarters = [
    ('2023-Q2', date(2023, 6, 30)),
    ('2023-Q3', date(2023, 9, 30)),
    ('2023-Q4', date(2023, 12, 31)),
    ('2024-Q1', date(2024, 3, 31)),
    ('2024-Q2', date(2024, 6, 30)),
    ('2024-Q3', date(2024, 9, 30)),
    ('2024-Q4', date(2024, 12, 31)),
    ('2025-Q1', date(2025, 3, 31)),
    ('2025-Q2', date(2025, 6, 30)),
    ('2025-Q3', date(2025, 9, 30)),
    ('2025-Q4', date(2025, 12, 31)),
    ('2026-Q1', date(2026, 3, 31)),
]

for q, d in quarters:
    QUARTERLY_JOBS.append({
        'date': d,
        'quarter': q,
        'type': 'quarterly_profit',
        'tables': ['quarterly_profit']
    })

# ==============================================================================
# 一次性工作 (初始執行)
# ==============================================================================
ONE_TIME_JOBS = [
    {'type': 'sectors', 'tables': ['sectors'], 'description': '產業分類'},
    {'type': 'stock_basic', 'tables': ['stock_basic'], 'description': '股票基本資料'},
]

# ==============================================================================
# 排程摘要
# ==============================================================================
def print_schedule():
    print('=' * 80)
    print('股票數據抓取工作分配表')
    print('=' * 80)
    print(f'資料期間: {START_DATE} ~ {END_DATE}')
    print()
    
    print('┌─────────────────────────────────────────────────────────────────────────┐')
    print('│ [1] 日線抓取 (Daily)                                                   │')
    print('├─────────────────────────────────────────────────────────────────────────┤')
    print(f'│ 頻率: 每交易日                                                          │')
    print(f'│ 資料表: daily_kline, institutional_investors                            │')
    print(f'│ 總次數: {len(DAILY_JOBS)} 次                                                 │')
    first_date = DAILY_JOBS[0].get('date', 'N/A')
    last_date = DAILY_JOBS[-1].get('date', 'N/A')
    print(f'│ 首日: {first_date}                                            │')
    print(f'│ 末日: {last_date}                                            │')
    print('└─────────────────────────────────────────────────────────────────────────┘')
    print()
    
    print('┌─────────────────────────────────────────────────────────────────────────┐')
    print('│ [2] 月營收 (Monthly)                                                   │')
    print('├─────────────────────────────────────────────────────────────────────────┤')
    print(f'│ 頻率: 每月15日                                                          │')
    print(f'│ 資料表: monthly_revenue, monthly_revenue_tpex                          │')
    print(f'│ 總次數: {len(MONTHLY_JOBS)} 次                                                 │')
    first_month = MONTHLY_JOBS[0].get('date', date(2023,4,15)).strftime('%Y-%m')
    last_month = MONTHLY_JOBS[-1].get('date', date(2026,4,15)).strftime('%Y-%m')
    print(f'│ 期間: {first_month} ~ {last_month}                                              │')
    print('└─────────────────────────────────────────────────────────────────────────┘')
    print()
    
    print('┌─────────────────────────────────────────────────────────────────────────┐')
    print('│ [3] 季獲利 (Quarterly)                                                │')
    print('├─────────────────────────────────────────────────────────────────────────┤')
    print(f'│ 頻率: 每季末                                                            │')
    print(f'│ 資料表: quarterly_profit                                              │')
    print(f'│ 總次數: {len(QUARTERLY_JOBS)} 次                                                  │')
    first_q = QUARTERLY_JOBS[0].get('quarter', '2023-Q2')
    last_q = QUARTERLY_JOBS[-1].get('quarter', '2026-Q1')
    print(f'│ 期間: {first_q} ~ {last_q}                                     │')
    print('└─────────────────────────────────────────────────────────────────────────┘')
    print()
    
    print('┌─────────────────────────────────────────────────────────────────────────┐')
    print('│ [4] 一次性工作 (One-time)                                             │')
    print('├─────────────────────────────────────────────────────────────────────────┤')
    for job in ONE_TIME_JOBS:
        desc = job.get('description', '')
        tbls = job.get('tables', [])
        print(f'│ - {desc:15} -> {tbls}')
    print('└─────────────────────────────────────────────────────────────────────────┘')
    print()
    
    total = len(DAILY_JOBS) + len(MONTHLY_JOBS) + len(QUARTERLY_JOBS) + len(ONE_TIME_JOBS)
    print(f'總工作次數: {total}')

if __name__ == '__main__':
    print_schedule()