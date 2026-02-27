import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_utils import SUBJECTS, LESSON_TYPES, upsert_result, load_results, get_units_for_test, load_units
import datetime
import pandas as pd

st.set_page_config(page_title="テスト結果入力", page_icon="✏️", layout="wide")
st.title("✏️ テスト結果を入力する")

# 講座種別ごとの講義No.を取得
units_df = load_units()

col1, col2 = st.columns(2)
with col1:
    lesson_type = st.selectbox("講座種別", LESSON_TYPES)
with col2:
    if not units_df.empty:
        available_numbers = sorted(
            units_df[units_df["lesson_type"] == lesson_type]["test_number"].unique().tolist()
        )
    else:
        available_numbers = list(range(1, 45))
    test_number = st.selectbox("講義No.", available_numbers)

st.divider()

def save_subject(subject, score, avg, max_s, std_dev):
    return upsert_result(
        test_date=datetime.date.today(),
        lesson_type=lesson_type,
        test_number=int(test_number),
        subject=subject,
        score=score,
        average_score=avg,
        max_score=max_s,
        std_dev=std_dev,
        memo="",
    )

for subject in SUBJECTS:
    units_df_sub = get_units_for_test(subject, lesson_type, test_number)

    with st.expander(f"**{subject}**", expanded=True):
        if not units_df_sub.empty:
            for _, row in units_df_sub.iterrows():
                unit_str = f"📌 **単元:** {row['unit_name']}"
                if pd.notna(row.get('content')) and str(row.get('content')).strip():
                    unit_str += f"　／　{row['content']}"
                st.markdown(unit_str)
        else:
            st.caption("📌 単元データなし")

        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
        with c1:
            score = st.number_input("得点", min_value=0.0, max_value=500.0, step=1.0,
                                    key=f"score_{subject}", format="%.0f")
        with c2:
            avg = st.number_input("平均点", min_value=0.0, max_value=500.0, step=0.5,
                                  key=f"avg_{subject}", format="%.1f")
        with c3:
            max_s = st.number_input("満点", min_value=1.0, max_value=500.0, step=1.0,
                                    value=100.0, key=f"max_{subject}", format="%.0f")
        with c4:
            std = st.number_input("標準偏差（任意）", min_value=0.0, max_value=200.0, step=0.1,
                                  value=0.0, key=f"std_{subject}", format="%.1f",
                                  help="塾から入手できた場合のみ。")
        with c5:
            st.write("")
            st.write("")
            if st.button("💾 保存", key=f"save_{subject}"):
                result = save_subject(subject, score, avg, max_s, std if std > 0 else None)
                if result == "saved":
                    st.success("✅ 保存！")
                elif result == "updated":
                    st.success("✅ 上書き保存！")

# --- 直近データ一覧 ---
st.divider()
st.subheader("📋 直近の入力データ")
df = load_results()
if not df.empty:
    show = df.sort_values(["lesson_type", "test_number"], ascending=False).head(20).copy()
    show["相対スコア"] = show.apply(
        lambda r: round((r["score"]/r["max_score"] - r["average_score"]/r["max_score"])*100 + 50, 1), axis=1
    )
    show = show[["lesson_type","test_number","subject","score","average_score","max_score","相対スコア"]]
    show.columns = ["講座","講義No.","教科","得点","平均点","満点","相対スコア"]
    st.dataframe(show, use_container_width=True, hide_index=True)
else:
    st.info("まだデータがありません。")
