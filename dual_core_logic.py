#!/usr/bin/env python3
"""
DualCoreCommander - ET 時區與邏輯
負責市場階段切換與嚴格評級
"""

import pandas as pd
import numpy as np
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)

class DualCoreCommander:
    def __init__(self):
        self.et_tz = ZoneInfo("US/Eastern")
        self.thresholds = {
            "PRE_MARKET": {"stock_move": 0.005, "spread_limit": 0.05, "strict": True},
            "OPENING_DRIVE": {"stock_move": 0.003, "spread_limit": 0.08, "strict": True},
            "MID_DAY": {"stock_move": 0.002, "spread_limit": 0.10, "strict": False},
            "CLOSED": {"stock_move": 9.999, "spread_limit": 0.00, "strict": True}
        }
    
    def get_market_status(self):
        """取得當前市場階段與對應閾值"""
        now_et = datetime.now(self.et_tz)
        current_time = now_et.strftime("%H:%M")
        
        phase = "CLOSED"
        if "04:00" <= current_time < "09:30":
            phase = "PRE_MARKET"
        elif "09:30" <= current_time < "10:00":
            phase = "OPENING_DRIVE"
        elif "10:00" <= current_time < "15:30":
            phase = "MID_DAY"
        elif "15:30" <= current_time < "20:00":
            phase = "POST_MARKET"
        
        return phase, self.thresholds.get(phase, self.thresholds["CLOSED"])
    
    def check_stock_sop(self, df, ai_decision: str) -> tuple:
        """母股 SOP 判斷"""
        if df is None or len(df) < 5:
            return False, "數據不足"
        
        close = df["Close"].values
        high = df["High"].values
        low = df["Low"].values
        last_close = close[-1]
        
        # ATR
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        atr = np.mean(np.maximum(tr1, np.maximum(tr2, tr3)))
        atr_pct = atr / last_close
        
        # EMA
        ema20 = pd.Series(close).ewm(span=20).mean().values[-1]
        ema50 = pd.Series(close).ewm(span=50).mean().values[-1]
        
        # 位置
        day_high, day_low = high.max(), low.min()
        position = (last_close - day_low) / (day_high - day_low)
        
        # 趨勢
        trend = "多頭" if last_close > ema20 else "空頭"
        trend_strong = (last_close > ema20 > ema50) or (last_close < ema20 < ema50)
        
        # Barb Wire
        cv = np.std(close[-12:]) / np.mean(close[-12:])
        if cv < 0.02:
            return False, "Barb Wire", "F"
        
        # Middle (含趨勢例外)
        if 0.35 <= position <= 0.65:
            if trend_strong and abs(last_close - ema20) / last_close < 0.02:
                pass
            else:
                return False, f"Middle ({position:.0f}%)", "F"
        
        # AI 裁決
        if "✅" not in ai_decision:
            return False, "AI 否決", "F"
        
        # Low Vol
        if atr_pct < 0.0015:
            return False, f"LowVol (ATR%={atr_pct:.3f})", "F"
        
        return True, f"結構成立 ({trend})", "B"
    
    def rate_signal(self, stock_result, option_result) -> tuple:
        """嚴格評級輸出"""
        stock_pass, stock_msg = stock_result
        option_pass, option_msg = option_result
        
        # 🛑 BLOCK
        if not stock_pass:
            return "🛑 BLOCK", stock_msg
        
        # ⭐ A 級
        if stock_pass and option_pass:
            return "⭐ A 級", f"具備交易資格 (母股✅ + 期權✅ {option_msg})"
        
        # ⚠️ C 級
        return "⚠️ C 級", f"期權觀望 (母股✅ 但 {option_msg})"


if __name__ == "__main__":
    commander = DualCoreCommander()
    phase, thresholds = commander.get_market_status()
    print(f"市場階段: {phase}")
    print(f"閾值: {thresholds}")
