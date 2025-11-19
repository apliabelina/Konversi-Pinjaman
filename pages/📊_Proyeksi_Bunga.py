import streamlit as st
import openpyxl
from openpyxl import Workbook
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image
import altair as alt
import ast
import plotly.graph_objects as go
import datetime
import plotly.express as px
import plotly.io as pio
from datetime import date
from plotly.subplots import make_subplots
import plotly.subplots as sp
import matplotlib.pyplot as plt


st.set_page_config(layout="wide", page_title="Konversi Pinjaman")
st.markdown("""
    <style>
    /* Warna latar sidebar */
    section[data-testid="stSidebar"] {
        background-color: #100E34;
    }

    /* Menu aktif */
    [data-testid="stSidebar"] a[aria-current="page"] {
        background-color: #FFBF18;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        display: block;
        text-decoration: none;
    }

    /* Teks menu aktif */
    [data-testid="stSidebar"] a[aria-current="page"] span {
        color: #262730 !important;
        font-weight: bold !important;
    }

    /* Menu tidak aktif (link) */
    [data-testid="stSidebar"] a:not([aria-current="page"]) {
        color: #ffffff !important;
        text-decoration: none;
    }

    /* Teks menu tidak aktif */
    [data-testid="stSidebar"] a:not([aria-current="page"]) span {
        color: #ffffff !important;
        font-weight: bold !important;
    }

    /* Hover efek */
    [data-testid="stSidebar"] a:hover span {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Silakan login terlebih dahulu di halaman Home.")
    st.stop()

color_type1 = {
    'USDIDR': 'Red',  # Purple-like color
    'DXY': 'Blue',   # Orange-like color
    'USDJPY': 'Black',
    'USDEUR': '#ED8827',
    'JPYIDR': 'Green'
}

color_type2 = {
    'GTIDR10Y': '#7D297E',  # Purple-like color
    'USGG10YR': '#FAC92B',   # Orange-like color
    'GTJPY10Y': 'Black',
    'GTEUR10Y': '#ED8827'
}

color_type3 = {
    'IDBIRRPO Index': '#7D297E',  # Purple-like color
    'FDTR Index': '#FAC92B',   # Orange-like color
    'BOJDTR Index': 'Black',
    'EURR002W Index': '#ED8827'
}

@st.cache_data 

def baca_data(x,y):
    data     = pd.read_excel(x,  sheet_name=y,engine="openpyxl")
    return data

# **SESSION STATE HANDLING**
if "data_file2" not in st.session_state:
    st.session_state.data_file2 = None
if "data_file3" not in st.session_state:
    st.session_state.data_file3 = None
if "data_outstanding" not in st.session_state:
    st.session_state.data_outstanding = None
if "data_proyeksi" not in st.session_state:
    st.session_state.data_proyeksi = None
if "creditor_name" not in st.session_state:
    st.session_state.creditor_name = []
if "currency_name" not in st.session_state:
    st.session_state.currency_name = []

col21, col22= st.columns(2)
with col21:
    data_file2 = st.file_uploader("Upload File Data Proyeksi ",type=['xlsx'])
    if data_file2:
        st.session_state.data_file2 = data_file2
with col22:
    data_file3 = st.file_uploader("Upload File Data Outstanding ",type=['xlsx'])
    if data_file3:
        st.session_state.data_file3 = data_file3
# **BACA FILE DATA OUTSTANDING**
if st.session_state.data_file3:
    if st.session_state.data_outstanding is None:
        st.session_state.data_outstanding = baca_data(st.session_state.data_file3, "Data")
    
    data_outstanding = st.session_state.data_outstanding
    data_outstanding['LOAN_ID'] = data_outstanding['LOAN_ID'].astype(str)
    data_outstanding['MATURITY_DATE'] = pd.to_datetime(data_outstanding['MATURITY_DATE'])
    data_outstanding['BACKUPASOFDATEID'] = pd.to_datetime(data_outstanding['BACKUPASOFDATEID']).dt.strftime('%d-%b-%Y')
    asofdate = data_outstanding.loc[0, 'BACKUPASOFDATEID']

    # **EXPANDER UNTUK FILTER DATA**
    with st.expander(f"Outstanding (as of {asofdate})"):
        creditor_name = st.multiselect('Select CREDITOR NAME', data_outstanding['CREDITOR_NAME'].unique(), default=st.session_state.creditor_name)
        st.session_state.creditor_name = creditor_name

        data_outstanding1 = data_outstanding[data_outstanding.CREDITOR_NAME.isin(creditor_name)]

        currency_name = st.multiselect('Select CURR', data_outstanding1['CURR'].unique(), default=st.session_state.currency_name)
        st.session_state.currency_name = currency_name

        data_outstanding1 = data_outstanding1[data_outstanding1.CURR.isin(currency_name)]
        data_outstanding1 = data_outstanding1[["LOAN_ID", "CURR", "AMT_OUTSTANDING_ORI", "MATURITY_DATE", "INTEREST_RATE", "INTEREST_SPREAD", "LOAN_AMOUNT_STATUS", "NAME", "INTEREST_RATE_TYPE"]]
        data_outstanding1 = data_outstanding1.sort_values(by=["CURR", "MATURITY_DATE"], ascending=[True, True])
        data_outstanding1 = data_outstanding1.reset_index(drop=True)
        data_outstanding1['MATURITY_DATE'] = data_outstanding1['MATURITY_DATE'].dt.strftime('%d-%b-%Y')

        # **PIVOT DATA OUTSTANDING**
        pivot_data = data_outstanding1.groupby("LOAN_ID").agg({
            "AMT_OUTSTANDING_ORI": "sum",  # SUM untuk total outstanding
            "INTEREST_RATE": "mean",  # AVG untuk interest rate
            "INTEREST_SPREAD": "mean"  # AVG untuk spread
        }).reset_index()

        # Tambahkan kembali kolom kategorikal
        categorical_cols = ["CURR", "MATURITY_DATE", "LOAN_AMOUNT_STATUS", "NAME", "INTEREST_RATE_TYPE"]
        pivot_data = pivot_data.merge(data_outstanding1.groupby("LOAN_ID")[categorical_cols].first(), on="LOAN_ID")

        # **BACA FILE DATA PROYEKSI**
        if st.session_state.data_file2:
            if st.session_state.data_proyeksi is None:
                st.session_state.data_proyeksi = baca_data(st.session_state.data_file2, "Data")

            data_proyeksi = st.session_state.data_proyeksi
            data_proyeksi['LO_NO'] = data_proyeksi['LO_NO'].astype(str)

            # Salin data untuk diproses
            data_proyeksi1 = data_proyeksi.copy()
            data_proyeksi1 = data_proyeksi1[["LO_NO", "CREDITOR_NAME", "AMT_ORI", "AMT_IDR"]]

            # **HANYA AMBIL DATA PROYEKSI BUNGA**
            data_proyeksi_bunga = data_proyeksi1[
                (data_proyeksi1.CREDITOR_NAME.isin(creditor_name)) & 
                ((data_proyeksi.PROJ_TYPE == 'INTEREST') | (data_proyeksi.PROJ_TYPE == 'FEE'))
            ]
            data_proyeksi_bunga_sum = data_proyeksi_bunga.groupby('LO_NO')[["AMT_ORI", "AMT_IDR"]].sum().reset_index()
            data_proyeksi_bunga_sum.rename(columns={"LO_NO": "LOAN_ID"}, inplace=True)

            # **MERGE DATA OUTSTANDING DAN PROYEKSI**
            data_final = pivot_data.merge(data_proyeksi_bunga_sum, on="LOAN_ID", how="left")
            data_final.rename(columns={"AMT_ORI": "PROJ_AMT_ORI", "AMT_IDR": "PROJ_AMT_IDR"}, inplace=True)

            st.write(data_final)
