#!/usr/bin/env python3
"""
OptionRadar - 期權反作弊雷達
負責抓取真實期權數據，過濾假死、價差過大合約
"""

import yfinance as yf
import pandas as pd
from collections import defaultdict, deque

class OptionRadar:
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.ticker = yf.Ticker(self.symbol)
        self.mid_history = defaultdict(lambda: deque(maxlen=5))
    
    def _get_current_price(self):
        """獲取母股最新價格"""
        try:
            price = self.ticker.fast_info.get('last_price')
            if price is None:
                info = self.ticker.info
                price = info.get('regularMarketPrice') or info.get('preMarketPrice')
            return price
        except:
            return None
    
    def get_atm_call(self):
        """抓取 ATM Call 合約"""
        try:
            stock_price = self._get_current_price()
            if stock_price is None:
                return None, "無母股現價"
            
            exp_dates = self.ticker.options
            if not exp_dates:
                return None, "無期權鏈"
            
            target_date = exp_dates[0]
            opts = self.ticker.option_chain(target_date)
            calls = opts.calls
            
            if len(calls) == 0:
                return None, "無 Call 合約"
            
            calls = calls.copy()
            calls['diff'] = abs(calls['strike'] - stock_price)
            atm = calls.sort_values('diff').iloc[0]
            
            # 轉成 dict
            contract = {
                'contractSymbol': str(atm['contractSymbol']),
                'strike': float(atm['strike']),
                'bid': float(atm['bid']) if pd.notna(atm['bid']) else 0,
                'ask': float(atm['ask']) if pd.notna(atm['ask']) else 0,
                'lastPrice': float(atm['lastPrice']) if pd.notna(atm['lastPrice']) else 0,
                'volume': int(atm['volume']) if pd.notna(atm['volume']) else 0
            }
            
            return contract, f"ATM Strike: {contract['strike']}"
        except Exception as e:
            return None, f"Error: {e}"
    
    def anti_cheat_check(self, contract, stock_change_pct, threshold_dict, debug=False):
        """
        反作弊檢查 (基於 Mid Price 與歷史狀態)
        
        Returns: (Passed: bool, Reason: str)
        """
        if contract is None:
            return False, "無合約數據"
        
        contract_id = contract['contractSymbol']
        bid = contract['bid']
        ask = contract['ask']
        
        # 計算 Mid Price
        if bid == 0 or ask == 0:
            return False, "Bid/Ask 異常"
        
        mid_price = (bid + ask) / 2
        spread = (ask - bid) / mid_price
        
        # 更新歷史
        self.mid_history[contract_id].append(mid_price)
        history = self.mid_history[contract_id]
        
        if debug:
            print(f" [RADAR] {contract_id[:20]}... | Mid: {mid_price:.2f} | Spread: {spread:.1%}")
        
        # ❌ 否決條款
        if len(history) >= 3:
            if history[-1] == history[-2] == history[-3]:
                return False, "Mid 連 3 次未跳動"
        
        limit = threshold_dict.get('spread_limit', 0.12)
        if spread > limit:
            return False, f"價差過大 ({spread:.1%} > {limit:.1%})"
        
        if len(history) >= 2:
            mid_change = (history[-1] - history[-2]) / history[-2]
            if stock_change_pct > 0 and mid_change < -0.01:
                return False, "動能背離"
        
        # ✅ 通過條款
        unique_prices = len(set(history))
        is_active = unique_prices >= 2 if len(history) < 3 else unique_prices >= 3
        
        if is_active and spread <= limit:
            return True, f"報價活躍 (Spread {spread:.1%})"
        
        return False, f"動能不明 (Spread {spread:.1%})"


if __name__ == "__main__":
    # 測試
    radar = OptionRadar("NVDA")
    contract, msg = radar.get_atm_call()
    print(f"合約: {contract['contractSymbol'] if contract else msg}")
    print(f"價格: {contract['lastPrice'] if contract else 'N/A'}")
