import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_utils import SUBJECTS, load_results, enrich_results
import plotly.graph_objects as go

st.set_page_config(page_title="成績グラフ", page_icon="📈", layout="wide")
st.title("📈 成績グラフ")

df_raw = load_results()
if df_raw.empty:
    st.info("まだデータがありません。「✏️ テスト結果を入力する」からデータを登録してください。")
    st.stop()

df = enrich_results(df_raw)

# --- サイドバー ---
with st.sidebar:
    st.header("表示設定")
    y_metric = st.radio(
        "指標",
        ["相対スコア（平均=50）", "得点率（%）", "得点（点）"],
        help="相対スコア：平均得点率を50として自分の得点率との差を加算。平均より上なら50超、下なら50未満。"
    )
    lesson_types = df["lesson_type"].unique().tolist()
    selected_types = st.multiselect("講座種別", lesson_types, default=lesson_types)
    show_avg_line = st.checkbox("平均ラインを表示", value=True)

metric_map = {
    "相対スコア（平均=50）": ("relative_score", "相対スコア"),
    "得点率（%）": ("score_rate", "得点率 (%)"),
    "得点（点）": ("score", "得点 (点)"),
}
y_col, y_label = metric_map[y_metric]

df = df[df["lesson_type"].isin(selected_types)].copy()
df["x_label"] = df.apply(lambda r: f"{r['lesson_type']} 第{int(r['test_number'])}回", axis=1)
df = df.sort_values(["test_date", "test_number"])

COLORS = {"国語": "#EF4444", "算数": "#3B82F6", "理科": "#10B981", "社会": "#F59E0B"}

# --- 全教科まとめ ---
st.subheader("全教科の推移")
fig_all = go.Figure()
for subject in SUBJECTS:
    sub = df[df["subject"] == subject]
    if sub.empty:
        continue
    fig_all.add_trace(go.Scatter(
        x=sub["x_label"], y=sub[y_col],
        mode="lines+markers", name=subject,
        line=dict(color=COLORS[subject], width=2),
        marker=dict(size=9),
        hovertemplate=f"<b>{subject}</b><br>%{{x}}<br>{y_label}: %{{y}}<extra></extra>"
    ))
if y_col == "relative_score" and show_avg_line:
    fig_all.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="平均(50)")
fig_all.update_layout(
    height=380, hovermode="x unified",
    yaxis_title=y_label, xaxis_title="",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=30, b=10),
)
st.plotly_chart(fig_all, use_container_width=True)

st.divider()

# --- 教科別タブ ---
st.subheader("教科別グラフ")
tabs = st.tabs(SUBJECTS)
for tab, subject in zip(tabs, SUBJECTS):
    with tab:
        sub = df[df["subject"] == subject].copy()
        if sub.empty:
            st.info(f"{subject}のデータがまだありません。")
            continue

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sub["x_label"], y=sub[y_col],
            mode="lines+markers", name=subject,
            line=dict(color=COLORS[subject], width=3),
            marker=dict(size=11),
            hovertemplate=f"<b>{subject}</b><br>%{{x}}<br>{y_label}: %{{y}}<br>得点: %{{customdata[0]}} / %{{customdata[1]}}<extra></extra>",
            customdata=sub[["score", "max_score"]].values,
        ))

        # 平均ラインを得点率・得点モードで追加
        if show_avg_line and y_col == "score_rate":
            fig.add_trace(go.Scatter(
                x=sub["x_label"], y=sub["avg_rate"],
                mode="lines+markers", name="平均",
                line=dict(color="#9CA3AF", width=2, dash="dash"),
                marker=dict(size=7),
            ))
        elif show_avg_line and y_col == "score":
            fig.add_trace(go.Scatter(
                x=sub["x_label"], y=sub["average_score"],
                mode="lines+markers", name="平均",
                line=dict(color="#9CA3AF", width=2, dash="dash"),
                marker=dict(size=7),
            ))
        elif y_col == "relative_score" and show_avg_line:
            fig.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="平均(50)")

        # 最新の統計
        latest = sub.iloc[-1]
        m1, m2, m3 = st.columns(3)
        m1.metric("最新得点率", f"{latest['score_rate']:.1f}%",
                  delta=f"{latest['score_rate'] - sub.iloc[-2]['score_rate']:.1f}pt" if len(sub) > 1 else None)
        m2.metric("最新相対スコア", f"{latest['relative_score']:.1f}",
                  delta=f"{latest['relative_score'] - sub.iloc[-2]['relative_score']:.1f}" if len(sub) > 1 else None)
        avg_rs = sub["relative_score"].mean()
        m3.metric("平均相対スコア（全回）", f"{avg_rs:.1f}")

        fig.update_layout(
            height=320, hovermode="x unified",
            yaxis_title=y_label, xaxis_title="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        # 全データ表示
        with st.expander("データ一覧"):
            disp = sub[["x_label","test_date","score","average_score","max_score","score_rate","relative_score"]].copy()
            disp.columns = ["回","日付","得点","平均点","満点","得点率(%)","相対スコア"]
            st.dataframe(disp, use_container_width=True, hide_index=True)
