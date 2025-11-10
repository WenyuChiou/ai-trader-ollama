#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sys
# 自动检测路径
import os
if os.path.basename(os.getcwd()) == 'test':
    sys.path.insert(0, '../backend')
else:
    sys.path.insert(0, 'backend')

from src.tools.fundamental_data import get_earnings_history
import json

r = get_earnings_history('NVDA')
print('Quarterly earnings:', len(r.get('quarterly_earnings', [])))
print('Annual earnings:', len(r.get('annual_earnings', [])))
if r.get('quarterly_earnings'):
    print('Latest quarter:', r['quarterly_earnings'][0])
if r.get('annual_earnings'):
    print('Latest year:', r['annual_earnings'][0])
print('\nFull result:')
print(json.dumps(r, indent=2, ensure_ascii=False)[:500])

