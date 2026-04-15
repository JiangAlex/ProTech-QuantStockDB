#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Stock Data Fetch Job Scheduler
抓取週期: 2023-04-14 ~ 2026-04-14 (三年歷史資料)

工作分配:
- 日線抓取: 每日執行 (涵蓋所有交易日)
- 月營收: 每月執行
- 季獲利: 每季執行
'''

import psycopg2
from datetime import date, timedelta
import calendar

import os
# DB 連線 - 使用環境變數
DB_CONFIG = {
    'host': 'blog.softsnail.com',
    'port': 2432,
    'user': 'reef',
    'password': os.environ.get('POSTGRES_PASSWORD', ''),
    'dbname': 'twsestock'
}

START_DATE = date(2023, 4, 14)
END_DATE = date(2026, 4, 14)

# ==============================================================================
# 數據源配置 (台灣證券交易所 - TWSE)
# ==============================================================================
# 日線: https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d?...
# 月營收: https://www.twse.com.tw/rwd/zh/financial/MonthlyReport
# 季財報: https://www.twse.com.tw/rwd/zh/financial/CYQ

JOBS = {
    'daily_kline': {
        'description': '日K線資料',
        'frequency': '每日',
        'date_range': f'{START_DATE} ~ {END_DATE}',
        'total_days': (END_DATE - START_DATE).days,
        'estimated_records': '~720 交易日',
        'source': 'TWSE 證券櫃檯買賣中心',
        'priority': 1,
        'steps': [
            '1. 取得股票清單 (stock_basic)',
            '2. 依序抓取每檔股票日線',
            '3. 解析並寫入 daily_kline',
            '4. 記錄至 fetch_history'
        ]
    },
    'monthly_revenue': {
        'description': '月營收 (上市)',
        'frequency': '每月',
        'date_range': f'{START_DATE:%Y-%m} ~ {END_DATE:%Y-%m}',
        'total_months': (END_DATE.year - START_DATE.year) * 12 + END_DATE.month - START_DATE.month + 1,
        'estimated_records': '~36 個月',
        'source': 'TWSE 每月營收揭露',
        'priority': 2,
        'steps': [
            '1. 每月固定日期抓取',
            '2. 解析營收數據',
            '3. 寫入 monthly_revenue',
            '4. 記錄至 fetch_history'
        ]
    },
    'quarterly_profit': {
        'description': '季獲利資料',
        'frequency': '每季',
        'date_range': '2023Q2 ~ 2026Q1',
        'total_quarters': 12,
        'estimated_records': '~12 季',
        'source': 'TWSE 公開資訊觀測站',
        'priority': 3,
        'steps': [
            '1. 每季財報公布後抓取',
            '2. 解析EPS/營收/獲利',
            '3. 寫入 quarterly_profit',
            '4. 記錄至 fetch_history'
        ]
    },
    'institutional_investors': {
        'description': '法人買賣資料',
        'frequency': '每日',
        'date_range': f'{START_DATE} ~ {END_DATE}',
        'estimated_records': '~720 交易日',
        'source': 'TWSE 三大法人買賣統計',
        'priority': 2,
        'steps': [
            '1. 每日收盤後抓取',
            '2. 解析法人買賣',
            '3. 寫入 institutional_investors',
            '4. 記錄至 fetch_history'
        ]
    },
    'sectors': {
        'description': '產業分類',
        'frequency': '一次性',
        'date_range': '僅需執行一次',
        'estimated_records': '~50 產業',
        'source': 'TWSE 產業分類',
        'priority': 0,
        'steps': [
            '1. 取得產業清單',
            '2. 寫入 sectors',
            '3. 後續依賴 stock_basic 更新'
        ]
    }
}

def generate_schedule():
    '''生成完整工作排程'''
    
    print('=' * 80)
    print('股票數據抓取工作排程')
    print('=' * 80)
    print(f'資料期間: {START_DATE} ~ {END_DATE}')
    print(f'總天數: {(END_DATE - START_DATE).days} 天')
    print('=' * 80)
    
    for job_name, job_info in JOBS.items():
        print(f'\n[{job_info["priority"]}] {job_name}')
        print(f'  描述: {job_info["description"]}')
        print(f'  頻率: {job_info["frequency"]}')
        print(f'  期間: {job_info["date_range"]}')
        print(f'  來源: {job_info["source"]}')
        print(f'  預估: {job_info.get("estimated_records", "N/A")}')
        print(f'  步驟:')
        for step in job_info['steps']:
            print(f'    {step}')
    
    return JOBS

def save_to_db(job_name, start_date, end_date, record_count, status, error_message=None):
    '''記錄抓取歷史'''
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO fetch_history 
            (table_name, start_date, end_date, record_count, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (job_name, start_date, end_date, record_count, status, error_message))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f'✓ 已記錄 {job_name} 至 fetch_history')
    except Exception as e:
        print(f'⚠ 記錄失敗: {e}')

if __name__ == '__main__':
    JOBS = generate_schedule()