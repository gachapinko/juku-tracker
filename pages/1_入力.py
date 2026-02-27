import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_utils import SUBJECTS, LESSON_TYPES, upsert_result, load_results, get_units_for_test, load_units
import datetime
import pandas as pd

st.set_page_config(page_title="テスト結果入力", page_icon="✏️", layout="wide")
st.title("✏️ テスト結果を入力する")

# 講座種別ごとの最大講義数を取得
units_df = load_units()

col1, col2 = st.columns(2)
with col1:
    lesson_type = st.selectbox("講座種別", LESSON_TYPES)
with col2:
    # 講座種別に応じた講義No.の選択肢を生成
    if not units_df.empty:
        available_numbers = sorted(
            units_df[units_df["lesson_type"] == lesson_type]["test_number"].unique().tolist()
        )

# --- 直近データ一覧 ---
st.divider()
st.subheader("📋 直近の入力データ")
df = load_results()
if not df.empty:
    show = df.sort_values(["lesson_type","test_number"], ascending=False).head(20).copy()
    show["相対スコア"] = show.apply(
        lambda r: round((r["score"]/r["max_score"] - r["average_score"]/r["max_score"])*100 + 50, 1), axis=1
    )
    show = show[["lesson_type","test_number","subject","score","average_score","max_score","相対スコア"]]
    show.columns = ["講座","講義No.","教科","得点","平均点","満点","相対スコア"]
    st.dataframe(show, use_container_width=True, hide_index=True)
