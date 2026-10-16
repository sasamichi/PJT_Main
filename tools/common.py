import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_DATA_DIR = os.path.join(BASE_DIR, "data", "master")

def apply_common_styles():
    st.markdown("""
    <style>
    div[data-testid="InputInstructions"] {
        display: none;
    }
    div.stButton > button {
        text-align: left;
        width: 100%;
        padding: 0.25rem 0.5rem;
        margin: 0;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

def read_csv_clean(filename):
    path = os.path.join(MASTER_DATA_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str).fillna("")
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def save_csv_clean(df, filename):
    path = os.path.join(MASTER_DATA_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8")

def load_all_data():
    df_countries = read_csv_clean("countries.csv")
    df_municipalities = read_csv_clean("municipalities.csv")
    df_operators = read_csv_clean("operators.csv")
    df_routes = read_csv_clean("transport_routes.csv")
    df_nodes = read_csv_clean("transport_nodes.csv")
    df_route_nodes = read_csv_clean("route_nodes.csv")
    df_logs = read_csv_clean("exploration_logs.csv")
    df_country_prog = read_csv_clean("country_progress.csv")
    return (
        df_countries,
        df_municipalities,
        df_operators,
        df_routes,
        df_nodes,
        df_route_nodes,
        df_logs,
        df_country_prog
    )
