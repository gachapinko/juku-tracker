import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_utils import SUBJECTS, load_results, load_units, enrich_results
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="苦手分析", page_icon="🔍", layout="wide")
st.title("🔍 苦手単元を分析する")

df_raw = load_results()
units_df = load_units()

if df_raw.empty:
    st.info("まだデータがありません。テスト結果を入力すると分析できるようになります。")
    st.stop()

df = enrich_results(df_raw)

# 単元と結果をマージ
merged = pd.merge(
    df,
    units_df,
    on=["subject", "lesson_type", "test_number"],
    how="left"
)

# --- 教科別の相対スコア平均 ---
st.subheader("📊 教科別 平均相対スコア")
subj_stats = df.groupby("subject").agg(
    avg_relative=("relative_score", "mean"),
    avg_score_rate=("score_rate", "mean"),
    count=("score", "count")
).reset_index()
subj_stats = subj_stats.sort_values("avg_relative")

COLORS = {"国語": "#3B82F6", "算数": "#EF4444", "理科": "#10B981", "社会": "#F59E0B"}
fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=subj_stats["subject"],
    y=subj_stats["avg_relative"],
    marker_color=[COLORS[s] for s in subj_stats["subject"]],
    text=subj_stats["avg_relative"].round(1),
    textposition="outside",
))
fig_bar.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="平均(50)")
fig_bar.update_layout(
    height=300, yaxis_title="平均相対スコア", xaxis_title="",
    margin=dict(t=20, b=10), yaxis_range=[30, 70],
)
st.plotly_chart(fig_bar, use_container_width=True)

# --- 苦手回次ランキング ---
st.divider()
st.subheader("⚠️ 相対スコアが低かった回（苦手候補）")

threshold = st.slider("この相対スコア未満を苦手とみなす", min_value=30, max_value=55, value=48, step=1)

weak = merged[merged["relative_score"] < threshold].copy()
if weak.empty:
    st.success(f"相対スコア{threshold}未満の回はありません！好調です 🎉")
else:
    weak_display = weak[[
        "subject", "lesson_type", "test_number", "unit_name", "content",
        "score", "average_score", "max_score", "relative_score", "test_date"
    ]].copy()
    weak_display = weak_display.sort_values("relative_score")
    weak_display.columns = ["教科","講座","回","単元名","学習内容","得点","平均点","満点","相対スコア","日付"]

    # 教科ごとにタブ表示
    tab_subjects = weak_display["教科"].unique().tolist()
    tabs = st.tabs(tab_subjects)
    for tab, subject in zip(tabs, tab_subjects):
        with tab:
            sub_weak = weak_display[weak_display["教科"] == subject].drop(columns=["教科"])
            st.dataframe(sub_weak, use_container_width=True, hide_index=True)

# --- 単元別ヒートマップ（データが多い場合） ---
st.divider()
st.subheader("📈 教科別 回次スコア推移マップ")
selected_subject = st.selectbox("教科を選択", SUBJECTS)

sub_df = merged[merged["subject"] == selected_subject].sort_values(["lesson_type","test_number"])
if sub_df.empty:
    st.info("データなし")
else:
    sub_df["label"] = sub_df.apply(
        lambda r: f"{r['lesson_type']} 第{int(r['test_number'])}回\n{r['unit_name'] if pd.notna(r['unit_name']) else ''}",
        axis=1
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=sub_df["label"],
        y=sub_df["relative_score"],
        marker_color=[
            "#EF4444" if v < threshold else "#10B981"
            for v in sub_df["relative_score"]
        ],
        text=sub_df["relative_score"],
        textposition="outside",
        hovertemplate="%{x}<br>相対スコア: %{y}<br>得点: %{customdata[0]} / %{customdata[1]}<extra></extra>",
        customdata=sub_df[["score","max_score"]].values,
    ))
    fig2.add_hline(y=threshold, line_dash="dash", line_color="#F59E0B",
                   annotation_text=f"苦手ライン({threshold})")
    fig2.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="平均(50)")
    fig2.update_layout(
        height=400, yaxis_title="相対スコア", xaxis_title="",
        margin=dict(t=20, b=10),
        xaxis_tickangle=-45,
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("🔴 赤 = 苦手ライン未満　🟢 緑 = 平均以上")
