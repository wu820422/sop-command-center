#!/usr/bin/env python3
"""
🛡️ SOP 防線官 - 美股戰情室 (黑暗指揮官版)
"""

import streamlit as st
import pandas as pd
import time
import random
from option_radar import OptionRadar
from dual_core_logic import DualCoreCommander

# ==========================================
# ⚙️ 系統設定開關
# ==========================================
# True = 使用模擬數據測試 UI (讓你看綠光特效)
# False = 連接真實 OptionRadar/SOP (實戰模式)
DEMO_MODE = False

# ==========================================
# 1. 頁面初始化 (必須在第一行)
# ==========================================
st.set_page_config(
    page_title="SOP 戰情室",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. CSS 黑科技 (黑暗指揮官風格 - 修正版)
# ==========================================
st.markdown("""
<style>
/* 全局背景與字體 */
.stApp {
    background-color: #0E1117;
}
/* 1. 調整頂部留白 (關鍵修正) */
.block-container {
    padding-top: 3.5rem;
    padding-bottom: 2rem;
}
/* 2. 隱藏 Streamlit 預設的漢堡選單與頂部彩條 */
header {
    visibility: hidden;
}
header:hover {
    visibility: visible;
}
/* 3. 隱藏底部的 "Made with Streamlit" */
footer {
    visibility: hidden;
}
/* 指標卡片 (Metric Cards) */
div[data-testid="stMetric"] {
    background-color: #1a1c24;
    border: 1px solid #333;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
}
div[data-testid="stMetricLabel"] {
    font-size: 14px;
    color: #aaa;
}
div[data-testid="stMetricValue"] {
    font-size: 26px;
    font-weight: bold;
    color: #fff;
}
/* 表格字體優化 */
.dataframe {
    font-family: 'Courier New', monospace;
    font-size: 14px !important;
}
/* 按鈕樣式 */
div.stButton > button {
    height: 3em;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 初始化核心組件
# ==========================================
commander = DualCoreCommander()
TICKERS = [
    "NVDA", "TSLA", "AMD", "AAPL", "MSFT", "META",
    "AMZN", "GOOGL", "NFLX", "COIN", "MARA", "PLTR",
    "QCOM", "INTC", "SMCI", "MSTR", "SPY", "QQQ", "IWM", "DIA"
]

# ==========================================
# 4. 頂部儀表板配置
# ==========================================
col_title, col_btn = st.columns([4, 1])
with col_title:
    st.markdown("## 🛡️ SOP 防線官 - 美股戰情室")
with col_btn:
    scan_clicked = st.button("🔄 立即全域掃描", use_container_width=True, type="primary")

# 自動監控開關
col_auto, col_empty = st.columns([1, 3])
with col_auto:
    auto_run = st.toggle("🚀 啟用自動監控 (每 30 秒刷新)", value=False)

# 狀態顯示列 (四欄佈局)
phase, thresholds = commander.get_market_status()
m1, m2, m3, m4 = st.columns(4)
m1.metric("市場狀態 (ET)", phase, delta="監控運作中")

# 佔位符：掃描後會更新這些數字
placeholder_a = m2.empty()
placeholder_c = m3.empty()
placeholder_b = m4.empty()

# 預設顯示
placeholder_a.metric("⭐ A 級信號", "0", delta="等待指令")
placeholder_c.metric("⚠️ C 級觀望", "0", delta=None)
placeholder_b.metric("🛡️ BLOCK", "0", delta=None)

st.markdown("---")

# ==========================================
# 5. 掃描邏輯與表格渲染 (核心戰場)
# ==========================================
# 觸發條件：按下按鈕 OR 自動開關被打開
if scan_clicked or auto_run:
    results = []
    
    # 如果是自動跑，就不顯示進度條干擾視線
    if not auto_run:
        progress_text = "🛰️ 衛星連線中... 正在掃描 20 檔標的"
        my_bar = st.progress(0, text=progress_text)

    # 模擬母股 Gate (僅用於 Demo)
    def mock_stock_gate(sym):
        if sym == "NVDA":
            return True, "H2 結構成立 (Demo)"
        return random.choice([True, False]), random.choice(["H2", "Trap", "Middle", "Barb Wire"])

    # --- 掃描迴圈 ---
    for i, symbol in enumerate(TICKERS):
        if not auto_run:
            my_bar.progress((i + 1) / len(TICKERS), text=f"正在分析: {symbol}...")
        else:
            # 自動模式下在右上角顯示進度
            st.caption(f"🔄 正在分析: {symbol}...")

        # 初始化變數
        stock_pass = False
        stock_msg = "N/A"
        option_pass = False
        option_msg = "未檢測"
        atm_info = "-"
        current_price_display = "Loading..."

        radar = OptionRadar(symbol)

        # --- A. 取得母股狀態 ---
        if DEMO_MODE:
            stock_pass, stock_msg = mock_stock_gate(symbol)
            current_price_display = f"${random.uniform(100, 300):.2f}"
            stock_pct = 0.005
        else:
            stock_pass = True
            stock_msg = "SOP 檢查中"
            real_price = radar._get_current_price()
            if real_price:
                current_price_display = f"${real_price:.2f}"
            else:
                current_price_display = "N/A"
            stock_pct = 0.002

        # --- B. 取得期權狀態 (Gate 2) ---
        if stock_pass:
            if DEMO_MODE:
                if symbol == "NVDA":
                    option_pass = True
                    option_msg = "🚀 強力跟隨 (+5.2%)"
                    atm_info = "Call 195"
                else:
                    option_pass = random.choice([True, False])
                    option_msg = "🚀 跟隨" if option_pass else "⚠️ 價差過大"
                    atm_info = "Call ATM"
            else:
                contract, msg = radar.get_atm_call()
                if contract is not None:
                    atm_info = f"{contract['contractSymbol']} (${contract['lastPrice']})"
                    option_pass, option_msg = radar.anti_cheat_check(
                        contract, stock_pct, thresholds, debug=False
                    )
                else:
                    option_msg = msg
        else:
            if not DEMO_MODE:
                stock_msg = "BLOCK (Middle/LowVol)"

        # --- C. 最終評級 ---
        grade, reason = commander.rate_signal(
            (stock_pass, stock_msg),
            (option_pass, option_msg)
        )

        # --- D. 整理數據 ---
        score = 0
        if "A 級" in grade:
            score = 3
        elif "C 級" in grade:
            score = 2
        elif "BLOCK" in grade:
            score = 1

        results.append({
            "代號": symbol,
            "現價": current_price_display,
            "評級": grade,
            "母股狀態": stock_msg,
            "期權狀態": option_msg,
            "ATM合約": atm_info,
            "理由": reason,
            "_Score": score
        })

        # 小延遲避免被封
        time.sleep(0.05)

    if not auto_run:
        my_bar.empty()

    # 轉 DataFrame 並排序
    df = pd.DataFrame(results)
    df = df.sort_values(by="_Score", ascending=False).drop(columns=["_Score"])

    # 更新頂部數字指標
    count_a = len(df[df["評級"].str.contains("A")])
    count_c = len(df[df["評級"].str.contains("C")])
    count_b = len(df[df["評級"].str.contains("BLOCK")])

    placeholder_a.metric("⭐ A 級信號", f"{count_a}", delta="具備資格", delta_color="normal")
    placeholder_c.metric("⚠️ C 級觀望", f"{count_c}", delta="風險注意", delta_color="off")
    placeholder_b.metric("🛡️ BLOCK", f"{count_b}", delta="已過濾", delta_color="off")

    # ==========================================
    # 6. 表格樣式美化 (Pandas Styler)
    # ==========================================
    def highlight_rows(row):
        grade = row["評級"]
        styles = [''] * len(row)
        if "A 級" in grade:
            return ['background-color: #0c3818; color: #a3ffac; font-weight: bold; border-bottom: 1px solid #1e5c2b'] * len(row)
        elif "C 級" in grade:
            return ['background-color: #38300c; color: #ffdf75; border-bottom: 1px solid #5c4f14'] * len(row)
        elif "BLOCK" in grade:
            return ['background-color: #2d1b1e; color: #8a5a5f; opacity: 0.7'] * len(row)
        return styles

    # 顯示戰術表格
    st.dataframe(
        df.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        height=800,
        column_config={
            "代號": st.column_config.TextColumn("代號", help="股票代碼", width="small"),
            "現價": st.column_config.TextColumn("現價", width="small"),
            "評級": st.column_config.TextColumn("戰鬥評級", width="medium"),
            "ATM合約": st.column_config.TextColumn("ATM 期權", width="medium"),
            "理由": st.column_config.TextColumn("詳細理由", width="large"),
        },
        hide_index=True
    )

    # === ✨ 自動刷新邏輯 ===
    if auto_run:
        st.caption(f"🔄 系統將在 30 秒後自動刷新... (最後更新: {time.strftime('%H:%M:%S')})")
        time.sleep(30)
        st.rerun()

else:
    # 待機畫面
    st.info("👋 指揮官，系統就緒。請點擊「立即全域掃描」或開啟「自動監控」。")

# 底部版權/狀態
st.markdown("---")
st.caption(f"🛡️ SOP 防線官 V4.0 UI | 資料來源: Yahoo Finance | Mode: {'DEMO' if DEMO_MODE else 'LIVE'}")
