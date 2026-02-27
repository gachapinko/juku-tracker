import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_utils import SUBJECTS, LESSON_TYPES, add_result, load_results, get_units_for_test
import datetime
import pandas as pd

st.set_page_config(page_title="テスト結果入力", page_icon="✏️", layout="wide")
st.title("✏️ テスト結果を入力する")

# --- テスト選択 ---
col1, col2, col3 = st.columns(3)
with col1:
    test_date = st.date_input("📅 テスト日", value=datetime.date.today())
with col2:
    lesson_type = st.selectbox("📂 講座種別", LESSON_TYPES)
with col3:
    test_number = st.number_input("🔢 第○回", min_value=1, max_value=50, step=1, value=1)

st.divider()

# --- 各教科の単元プレビュー＋入力フォーム ---
st.subheader("4教科の得点・平均点を入力")

subject_data = {}
for subject in SUBJECTS:
    units_df = get_units_for_test(subject, lesson_type, test_number)

    with st.expander(f"**{subject}**", expanded=True):
        # 単元表示
        if not units_df.empty:
            for _, row in units_df.iterrows():
                unit_str = f"📌 **単元:** {row['unit_name']}"
                if pd.notna(row.get('content')) and str(row.get('content')).strip():
                    unit_str += f"　／　{row['content']}"
                st.markdown(unit_str)
        else:
            st.caption("📌 単元データなし")

        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
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
                                  help="塾から入手できた場合のみ。空欄でもOK。")
        subject_data[subject] = {
            "score": score, "avg": avg, "max_s": max_s,
            "std_dev": std if std > 0 else None,
        }

memo = st.text_area("📝 メモ（任意）", placeholder="例：算数は計算ミスが多かった。国語の時間が足りなかった。")

st.divider()
if st.button("💾 保存する", type="primary", use_container_width=True):
    existing = load_results()
    saved, skipped = [], []

    for subject in SUBJECTS:
        d = subject_data[subject]
        dup = existing[
            (existing["test_date"].astype(str) == str(test_date)) &
            (existing["lesson_type"] == lesson_type) &
            (existing["test_number"] == test_number) &
            (existing["subject"] == subject)
        ] if not existing.empty else pd.DataFrame()

        if not dup.empty:
            skipped.append(subject)
            continue

        add_result(
            test_date=test_date,
            lesson_type=lesson_type,
            test_number=test_number,
            subject=subject,
            score=d["score"],
            average_score=d["avg"],
            max_score=d["max_s"],
            std_dev=d["std_dev"],
            memo=memo,
        )
        saved.append(subject)

    if saved:
        st.success(f"✅ 保存しました：{' / '.join(saved)}")
    if skipped:
        st.warning(f"⚠️ 既存データあり（スキップ）：{' / '.join(skipped)}")

# --- 直近データ一覧 ---
st.divider()
st.subheader("📋 直近の入力データ")
df = load_results()
if not df.empty:
    show = df.sort_values("test_date", ascending=False).head(20).copy()
    show["相対スコア"] = show.apply(
        lambda r: round((r["score"]/r["max_score"] - r["average_score"]/r["max_score"])*100 + 50, 1), axis=1
    )
    show = show[["test_date","lesson_type","test_number","subject","score","average_score","max_score","相対スコア"]]
    show.columns = ["日付","講座","回","教科","得点","平均点","満点","相対スコア"]
    st.dataframe(show, use_container_width=True, hide_index=True)
else:
    st.info("まだデータがありません。")
