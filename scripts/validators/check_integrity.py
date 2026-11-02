# -*- coding: utf-8 -*-
"""
マスタデータ整合性・精度自動検証スクリプト (check_integrity.py)
---------------------------------------------------------------
`audit_integrity.py`（確定スキーマv3の全14テーブル監査＋回帰防止ゲート）への統合ラッパー。
"""

import sys
from audit_integrity import run_comprehensive_audit

if __name__ == '__main__':
    update = '--update-baseline' in sys.argv
    ok = run_comprehensive_audit(update_baseline=update)
    sys.exit(0 if ok else 1)
