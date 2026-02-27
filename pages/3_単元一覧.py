import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_utils import SUBJECTS, LESSON_TYPES, load_units

st.set_page_config(page_title="単元一覧", page_icon="📋", layout="wide")
st.title("📋 単元一覧")
st.caption("画像から取り込んだ単元データです。テスト結果入力時にも参照されます。")

units_df = load_units()
if units_df.empty:
    st.error("単元データが見つかりません。")
    st.stop()

# フィルタ
col1, col2 = st.columns(2)
with col1:
    selected_subject = st.selectbox("教科", ["すべて"] + SUBJECTS)
with col2:
    selected_type = st.selectbox("講座種別", ["すべて"] + LESSON_TYPES)

filtered = units_df.copy()
if selected_subject != "すべて":
    filtered = filtered[filtered["subject"] == selected_subject]
if selected_type != "すべて":
    filtered = filtered[filtered["lesson_type"] == selected_type]

filtered = filtered.sort_values(["subject", "lesson_type", "test_number"])

# 教科ごとにタブ表示
subjects_to_show = SUBJECTS if selected_subject == "すべて" else [selected_subject]
tabs = st.tabs(subjects_to_show)

for tab, subject in zip(tabs, subjects_to_show):
    with tab:
        sub_df = filtered[filtered["subject"] == subject]
        if sub_df.empty:
            st.info("該当データなし")
            continue

        types_in_sub = sub_df["lesson_type"].unique().tolist()
        # 通常 → 春期 → 夏期 → 冬期 の順
        ordered_types = [t for t in LESSON_TYPES if t in types_in_sub]

        for lt in ordered_types:
            lt_df = sub_df[sub_df["lesson_type"] == lt].sort_values("test_number")
            st.markdown(f"#### {'📅' if lt != '通常' else '📖'} {lt}講座")
            display = lt_df[["test_number", "unit_name", "content"]].copy()
            display.columns = ["回", "単元名", "学習内容"]
            st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()
st.caption(f"総単元数: {len(units_df)} 件（社会44＋国語44＋算数44＋理科44＋各講習）")
