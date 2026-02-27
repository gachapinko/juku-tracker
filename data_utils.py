import pandas as pd
import streamlit as st
from supabase import create_client, Client

SUBJECTS = ["国語", "算数", "理科", "社会"]
LESSON_TYPES = ["通常", "春期", "夏期", "冬期"]


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


# ─── 単元 ──────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_units() -> pd.DataFrame:
    sb = get_supabase()
    res = sb.table("units").select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame(columns=["subject", "lesson_type", "test_number", "unit_name", "content"])


def get_units_for_test(subject: str, lesson_type: str, test_number: int) -> pd.DataFrame:
    units_df = load_units()
    if units_df.empty:
        return pd.DataFrame()
    return units_df[
        (units_df["subject"] == subject) &
        (units_df["lesson_type"] == lesson_type) &
        (units_df["test_number"] == int(test_number))
    ]


# ─── テスト結果 ────────────────────────────────────

def load_results() -> pd.DataFrame:
    sb = get_supabase()
    res = sb.table("test_results").select("*").order("test_date").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df["test_date"] = pd.to_datetime(df["test_date"])
        return df
    return pd.DataFrame(columns=[
        "id", "test_date", "lesson_type", "test_number", "subject",
        "score", "average_score", "max_score", "std_dev", "memo"
    ])


def add_result(test_date, lesson_type, test_number, subject,
               score, average_score, max_score, std_dev=None, memo=""):
    sb = get_supabase()
    sb.table("test_results").insert({
        "test_date": str(test_date),
        "lesson_type": lesson_type,
        "test_number": int(test_number),
        "subject": subject,
        "score": float(score),
        "average_score": float(average_score),
        "max_score": float(max_score),
        "std_dev": float(std_dev) if std_dev else None,
        "memo": memo,
    }).execute()


def delete_result(result_id: int):
    sb = get_supabase()
    sb.table("test_results").delete().eq("id", result_id).execute()


# ─── 計算 ──────────────────────────────────────────

def calc_relative_score(score, average_score, max_score):
    if max_score and float(max_score) > 0:
        return round((float(score) / float(max_score) - float(average_score) / float(max_score)) * 100 + 50, 1)
    return None


def calc_deviation(score, average_score, std_dev):
    if std_dev and float(std_dev) > 0:
        return round((float(score) - float(average_score)) / float(std_dev) * 10 + 50, 1)
    return None


def enrich_results(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["score_rate"] = df.apply(
        lambda r: round(float(r["score"]) / float(r["max_score"]) * 100, 1)
        if float(r["max_score"]) > 0 else None, axis=1
    )
    df["avg_rate"] = df.apply(
        lambda r: round(float(r["average_score"]) / float(r["max_score"]) * 100, 1)
        if float(r["max_score"]) > 0 else None, axis=1
    )
    df["relative_score"] = df.apply(
        lambda r: calc_relative_score(r["score"], r["average_score"], r["max_score"]), axis=1
    )
    df["deviation"] = df.apply(
        lambda r: calc_deviation(r["score"], r["average_score"], r.get("std_dev")), axis=1
    )
    return df
