import streamlit as st
import openpyxl
from openpyxl import Workbook
import pandas as pd
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
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from arch import arch_model
from sklearn.preprocessing import MinMaxScaler
from pmdarima import auto_arima
from streamlit_echarts import st_echarts
import datetime as dt

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

# Warna untuk plot
color_curr = {'USDIDR': 'Red', 'DXY': 'Blue', 'USDJPY': 'Black', 'JPYIDR': 'Purple'}
color_yield = {'GTIDR10Y': '#7D297E', 'USGG10YR': '#FAC92B', 'GTJPY10Y': 'Black', 'GTEUR10Y': '#ED8827'}
color_type3 = {'IDBIRRPO Index': '#7D297E','FDTR Index': '#FAC92B','BOJDTR Index': 'Black','EURR002W Index': '#ED8827'
}

# Fungsi baca data
@st.cache_data
def baca_data(file, sheet_name):
    return pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl")

# Inisialisasi session state
if "data_file1" not in st.session_state:
    st.session_state["data_file1"] = None
if "as_of" not in st.session_state:
    st.session_state["as_of"] = None

if "start_date" not in st.session_state:
    st.session_state.start_date = None
if "end_date" not in st.session_state:
    st.session_state.end_date = None
if "periods" not in st.session_state:
    st.session_state.periods = 10
if "columns" not in st.session_state:
    st.session_state.columns = []
if "tanggal_referensi" not in st.session_state:
    st.session_state.tanggal_referensi = "2024-10-04"

# Path ke file Excel di folder pages
file_path = "pages/Data Historis - Monitoring Timing Konversi Pinjaman.xlsx"

# Fungsi baca data dari sheet
def baca_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)


data_kurs        = baca_data(file_path, "Kurs JPY")
data_yield       = baca_data(file_path, "Yield")
data_policyrate  = baca_data(file_path,"Rate Bank Central")
data_GI = baca_data(file_path, "Rekap JPY")

data_kurs = data_kurs.fillna(value=0)  # atau None → tergantung kebutuhan grafik


data_kurs['Dates']       = pd.to_datetime(data_kurs['Dates'])
data_yield['Dates']      = pd.to_datetime(data_yield['Dates'])
data_policyrate['Dates'] = pd.to_datetime(data_policyrate['Dates'])

st.session_state["data_kurs"] = data_kurs
st.session_state["data_yield"] = data_yield
st.session_state["data_policyrate"] = data_policyrate
st.session_state["data_GI"] = data_GI
st.session_state["as_of"] = data_kurs['Dates'].max()


# Tampilkan info data terakhir
as_of_str = data_kurs['Dates'].iloc[-1].strftime("%d %B %Y")
st.markdown(f"""
    <div style="background-color:#f7f5f0; padding:5px; border-radius:5px; display:flex; justify-content:space-between; align-items:center;">
        <h4 style="margin:0.5;">   Data Market </b></h4>
        <p> 📅 Last Update : {as_of_str}</p>
    </div>
    """, unsafe_allow_html=True)



# Tab Navigation
tab1, tab2, tab3 = st.tabs(["Nilai Tukar JPY", "Yield", "Suku Bunga Bank Sentral"])

# Tab 1: Nilai Tukar
if "data_kurs" in st.session_state:
    with tab1:
        data_kurs = st.session_state["data_kurs"].copy()
        data_kurs["Dates"] = pd.to_datetime(data_kurs["Dates"])
        min_date = data_kurs["Dates"].min().date()
        max_date = data_kurs["Dates"].max().date()

        data_GI   = st.session_state["data_GI"].copy()

        # --- Init state ---
        if "range_start" not in st.session_state: st.session_state["range_start"] = min_date
        if "range_end"   not in st.session_state: st.session_state["range_end"]   = max_date
        if "rp_key"      not in st.session_state: st.session_state["rp_key"]      = 0  # versi key date picker
        if "chart_key"   not in st.session_state: st.session_state["chart_key"]   = 0  # versi key chart  ← NEW


        def _sync_range_from_picker():
            sel = st.session_state.get(f"range_picker_{st.session_state['rp_key']}")
            if sel and isinstance(sel, tuple) and len(sel) == 2:
                s, e = sel
                st.session_state["range_start"] = s or min_date
                st.session_state["range_end"]   = e or max_date

        with st.container(border=True):
            st.markdown(
                """
                <h6 style="background-color:#100E34; color: white; padding: 7px; border-radius: 5px;">
                    Historis Nilai Tukar
                </h6>
                """, unsafe_allow_html=True
            )

            # 1) Filter sesuai state (default: semua data)
            start_date = st.session_state["range_start"]
            end_date = st.session_state["range_end"]
            mask = (data_kurs["Dates"].dt.date >= start_date) & (data_kurs["Dates"].dt.date <= end_date)
            df_plot = data_kurs.loc[mask].copy()
            if df_plot.empty:
                st.info("Tidak ada data pada rentang tanggal yang dipilih.")
            else:
                # 2) Siapkan X & series
                x_vals = df_plot["Dates"].dt.strftime("%Y-%m-%d").tolist()

                default_colors = {"DXY": "#5470C6","USDJPY": "#91CC75","JPYIDR": "#FAC858","USDIDR": "#EE6666"}
                def get_color(k):
                    if "color_curr" in globals() and k in color_curr:
                        return color_curr[k]
                    return default_colors[k]

                series_list = [
                    {"name":"DXY","type":"line","yAxisIndex":0,"showSymbol":False,"data":df_plot["DXY"].round(4).tolist(),"lineStyle":{"width":2}},
                    {"name":"USDJPY","type":"line","yAxisIndex":0,"showSymbol":False,"data":df_plot["USDJPY"].round(4).tolist(),"lineStyle":{"width":2}},
                    {"name":"JPYIDR","type":"line","yAxisIndex":0,"showSymbol":False,"data":df_plot["JPYIDR"].round(2).tolist(),"lineStyle":{"width":2}},
                    {"name":"USDIDR","type":"line","yAxisIndex":1,"showSymbol":False,"data":df_plot["USDIDR"].round(0).tolist(),"lineStyle":{"width":2}},
                ]

                # Garis vertikal tanggal konversi
                gi_dates = pd.to_datetime(data_GI["Tanggal Konversi Awal"], errors="coerce").dropna().dt.strftime("%Y-%m-%d").tolist()
                mark_lines = [{"xAxis": d} for d in gi_dates]
                for s in series_list:
                    if s["name"] == "USDIDR":
                        s["markLine"] = {
                            "symbol":"none","silent":True,
                            "lineStyle":{"type":"dotted","width":1,"color":"#999"},
                            "label":{"show":True,"formatter":""},
                            "data":mark_lines
                        }
                min_left = round(df_plot[["DXY","USDJPY","JPYIDR"]].min().min() * 0.9)
                max_left = round(df_plot[["DXY","USDJPY","JPYIDR"]].max().max() * 1.05)

                min_right = round(df_plot["USDIDR"].min() * 0.95)
                max_right = round(df_plot["USDIDR"].max() * 1.05)

                # Sinkronkan posisi slider ke range terpilih (opsional, biar handle pas)
                full_x = data_kurs["Dates"].dt.strftime("%Y-%m-%d").tolist()
                try:
                    start_idx = full_x.index(pd.to_datetime(start_date).strftime("%Y-%m-%d"))
                except ValueError:
                    start_idx = 0
                try:
                    end_idx = full_x.index(pd.to_datetime(end_date).strftime("%Y-%m-%d"))
                except ValueError:
                    end_idx = len(full_x) - 1
                options = {
                    "backgroundColor":"transparent",
                    "color":[get_color("DXY"), get_color("USDJPY"), get_color("JPYIDR"), get_color("USDIDR")],
                    "tooltip":{"trigger":"axis","axisPointer":{"type":"cross"}},
                    "legend":{"data":["DXY","USDJPY","JPYIDR","USDIDR"],"top":10,"type":"scroll","left":"center"},
                    "grid":{"left":40,"right":50,"top":70,"bottom":80,"containLabel":True},
                    "xAxis":{"type":"category","data":x_vals,"axisLabel":{"formatter":"{value}"}},
                    "yAxis":[
                        {"type":"value","name":"DXY, USDJPY, JPYIDR","position":"left","min":min_left,"max":max_left},
                        {"type":"value","name":"USDIDR","position":"right","min":min_right,"max":max_right},
                    ],
                    # Slider di bawah grafik: paksa selalu full range saat render
                    "dataZoom":[
                        {"type":"inside"},
                        {"type":"slider","height":18,"bottom":20, "start": 0, "end": 100}  # ← NEW
                    ],
                    "series": series_list,
                }

                st_echarts(options=options, height="440px", key="echarts_fig1")

        

            c_left, c_right = st.columns([4,1])

            with c_left:
                st.date_input(
                    "Pilih rentang tanggal yang ditampilkan",
                    value=(st.session_state["range_start"], st.session_state["range_end"]),
                    min_value=min_date, max_value=max_date,
                    key=f"range_picker_{st.session_state['rp_key']}",   # ← key versi
                    on_change=_sync_range_from_picker
                )   
            
            with c_right:
                # --- Samakan tinggi date input & tombol Reset ---
                st.markdown("""
                <style>
                :root { --ctrl-h: 40px; }            /* target tinggi, sesuaikan 40–46px */

                div[data-testid="stDateInput"] div[role="button"]{
                    height: var(--ctrl-h) !important;
                    padding: 0 0px !important;      /* biar teks centering vertikal */
                    border-radius: 0px !important;
                    display: flex; align-items: center;
                }

                /* Scope khusus untuk tombol Reset agar tidak ganggu tombol lain */
                .reset-wrap div[data-testid="stButton"] > button {
                    height: var(--ctrl-h) !important;
                    padding: 0 0px !important;      /* tinggi fix -> pakai padding horizontal saja */
                    border-radius: 0px !important;
                }
                </style>
                """, unsafe_allow_html=True)

                st.markdown('<div class="reset-wrap">', unsafe_allow_html=True)
                if st.button("Reset", type="primary", use_container_width=True, key="btn_reset",
                 help="Kembalikan ke seluruh data"):
                    st.session_state["range_start"] = min_date
                    st.session_state["range_end"]   = max_date
                    st.session_state["rp_key"]     += 1   # ← ganti key agar widget remount
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


        with st.container(border=True):
            file_path2 = "pages/Loan yang sudah di konversi.xlsx"
            data_konversi_jpy    = baca_data(file_path2, "JPY")

            for c in ["Tanggal Konversi", "Tanggal Konversi Awal", "Re-konversi Date"]:
                if c in data_konversi_jpy.columns:
                    data_konversi_jpy[c] = pd.to_datetime(data_konversi_jpy[c], errors="coerce")

            st.markdown(
                    """
                    <h6 style="background-color:#100E34; color: white; padding: 7px; border-radius: 5px;">
                        Loan yang Sudah di Konversi Ke JPY
                    </h6>
                    """, unsafe_allow_html=True
                )   
            #tanggal amatan jpy
            df_hist = st.session_state["data_kurs"].copy()
            df_hist["Dates"] = pd.to_datetime(df_hist["Dates"])
            df_hist = df_hist.sort_values("Dates").reset_index(drop=True)

            if "USDJPY" not in df_hist.columns:
                st.error("Kolom 'USDJPY' tidak ada di data historis (st.session_state['data_kurs']).")
                st.stop()

            min_hist = df_hist["Dates"].min().date()
            max_hist = df_hist["Dates"].max().date()
                
            tgl_amatan = st.date_input(
                "Tanggal amatan",
                value=max_hist, min_value=min_hist, max_value=max_hist,
                key="tgl_amatan_konversi"
                )
            
            # 1) Tentukan kolom label loan
            loan_label_col = (
                "Loan-ID" if "Loan-ID" in data_konversi_jpy.columns else
                ("Loan_ID" if "Loan_ID" in data_konversi_jpy.columns else
                ("Kode Pinjaman" if "Kode Pinjaman" in data_konversi_jpy.columns else None))
            )
            if loan_label_col is None:
                st.error("Tidak ditemukan kolom Loan-ID / Loan_ID / Kode Pinjaman pada sheet JPY.")
                st.stop()

            # 2) Satukan tanggal konversi (prioritas: Tanggal Konversi -> Tanggal Konversi Awal -> Re-konversi Date)
            cols_tgl = [c for c in ["Tanggal Konversi", "Tanggal Konversi Awal", "Re-konversi Date"] if c in data_konversi_jpy.columns]
            if not cols_tgl:
                st.error("Tidak ada kolom tanggal konversi di sheet JPY.")
                st.stop()

            data_konversi_jpy["tgl_konv"] = data_konversi_jpy[cols_tgl].bfill(axis=1).iloc[:, 0]

            # 3) Helper VLOOKUP: USDJPY pada/≤ tanggal (trading day terakhir yang tersedia)
            def lookup_usdjpy_on_or_before(date_like):
                if pd.isna(date_like):
                    return None
                d = pd.Timestamp(date_like)
                pos = df_hist["Dates"].searchsorted(d, side="right") - 1
                if pos < 0:
                    return None
                return float(df_hist.iloc[pos]["USDJPY"])

            # 4) Hitung kurs hasil VLOOKUP
            #    - Kurs Awal: dari Excel
            #    - Kurs @ Konversi: USDJPY pada/≤ tgl_konv (dari historis)
            #    - Threshold: USDJPY pada/≤ tgl_amatan (garis horizontal)
            if "Kurs Awal" not in data_konversi_jpy.columns:
                st.error("Kolom 'Kurs Awal' tidak ditemukan pada sheet JPY.")
                st.stop()

            data_konversi_jpy["Kurs Awal"] = pd.to_numeric(data_konversi_jpy["Kurs Awal"], errors="coerce")
            data_konversi_jpy["Kurs @ Konversi"] = data_konversi_jpy["tgl_konv"].apply(lookup_usdjpy_on_or_before)
            kurs_obs = lookup_usdjpy_on_or_before(pd.to_datetime(tgl_amatan))

            # 5) Siapkan data ke chart
            x_labels = data_konversi_jpy[loan_label_col].astype(str).tolist()
            series_awal = data_konversi_jpy["Kurs Awal"].tolist()
            series_konv = data_konversi_jpy["Kurs @ Konversi"].tolist()

            vals = [v for v in series_awal + series_konv + ([kurs_obs] if kurs_obs is not None else []) if v is not None]
            if not vals:
                st.info("Tidak ada nilai kurs valid untuk digambarkan.")
                st.stop()

            ymin = min(vals) * 0.97
            ymax = max(vals) * 1.03

            # 6) Render ECharts (2 line series + 1 threshold/markLine)
            from streamlit_echarts import st_echarts

            def col(name, default):
                # kalau punya color_curr: gunakan; jika tidak, pakai default
                return (color_curr[name] if "color_curr" in globals() and name in color_curr else default)

            series = [
                {
                    "name": "Kurs Awal",
                    "type": "line",
                    "showSymbol": True, "symbolSize": 6, "connectNulls": True,
                    "data": series_awal,
                    "lineStyle": {"width": 2},
                },
                {
                    "name": "Kurs @ Konversi",
                    "type": "line",
                    "showSymbol": True, "symbolSize": 6, "connectNulls": True,
                    "data": series_konv,
                    "lineStyle": {"width": 2},
                    # Garis threshold ditempel di sini
                    "markLine": {
                            "symbol": "none",
                            "silent": True,
                            "lineStyle": {"type": "dashed", "width": 2, "color": col("Threshold", "#EE6666")},
                            "label": {
                                "show": True,
                                # tampilkan di TENGAH, di atas garis, dengan background supaya terbaca
                                "position": "middle",
                                "align": "center",
                                "verticalAlign": "bottom",
                                "formatter": f"USDJPY @ {pd.to_datetime(tgl_amatan).strftime('%Y-%m-%d')} = {kurs_obs:.2f}" if kurs_obs is not None else "No Data",
                                "backgroundColor": "rgba(255,255,255,0.85)",
                                "padding": [2, 6],
                                "borderRadius": 4
                            },
                            "data": [] if kurs_obs is None else [{"yAxis": kurs_obs}],
                        },

                },
            ]

            options = {
                "backgroundColor": "transparent",
                "color": [col("Kurs Awal", "#5470C6"), col("Kurs @ Konversi", "#91CC75")],
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {"type": "line"},
                    "valueFormatter": "function (val) { if(val==null){return '-';} return Number(val).toFixed(2); }"
                },
                "legend": {"data": ["Kurs Awal", "Kurs @ Konversi"], "top": 10, "left": "center", "type": "scroll"},
                "grid": {"left": 40, "right": 40, "top": 60, "bottom": 40, "containLabel": True},
                "xAxis": {
                    "type": "category",
                    "data": x_labels,
                    "axisLabel": {"rotate": 0},          # kalau label panjang, ubah ke 30/45
                    "name": "Loan ID",                   # judul sumbu-X
                    "nameLocation": "middle",            # posisikan di tengah bawah
                    "nameGap": 30,                       # jarak dari sumbu
                    "nameTextStyle": {"fontSize": 12, "fontWeight": "bold"}
                },
                "yAxis": {"type": "value", "name": "USDJPY", "min": round(ymin), "max": round(ymax)},
                "series": series,
            }

        
            st_echarts(options=options, height="420px", key="echarts_kurs_per_loan")

            
            if kurs_obs is not None:
                # 1) Kolom alert per-loan
                data_konversi_jpy["Alert"] = np.where(
                    (data_konversi_jpy["Kurs @ Konversi"].notna()) & (kurs_obs > data_konversi_jpy["Kurs @ Konversi"]),
                    "potensi untuk re-konversi",
                    ""
                )

                # 2) Ringkasan & banner
                flagged = data_konversi_jpy["Alert"].eq("potensi untuk re-konversi")
                n_flag  = int(flagged.sum())
                n_total = int(len(data_konversi_jpy))

                if n_flag == n_total and n_total > 0:
                    # Banner berkedip kalau SEMUA loan berpotensi
                    st.markdown(f"""
                    <style>
                    .flash-alert {{
                        font-size: 18px;
                        font-weight: 700;
                        color: #166534;
                        animation: flash 1s infinite;
                        text-align: center;
                        padding: 12px 16px;
                        border: 2px solid #16a34a;
                        border-radius: 10px;
                        background-color: #e6ffe6;
                        margin-top: 6px; margin-bottom: 6px;
                    }}
                    @keyframes flash {{ 0% {{opacity: 1;}} 50% {{opacity: 0;}} 100% {{opacity: 1;}} }}
                    </style>
                    <div class="flash-alert">
                        🚨 RE-KONVERSI POTENSI UNTUK DILAKUKAN </div>
                    """, unsafe_allow_html=True)
                elif n_flag > 0:
                    st.success(f"✅ {n_flag}/{n_total} loan berstatus **potensi untuk re-konversi** "
                            f"(USDJPY amatan {kurs_obs:.2f} lebih tinggi dari kurs konversi).")
                else:
                    st.info(f"ℹ️ Tidak ada loan berpotensi re-konversi (USDJPY amatan {kurs_obs:.2f} tidak lebih tinggi).")

                # 3) (Opsional) tampilkan tabel loan yang kena alert
                df_alert = data_konversi_jpy.loc[flagged, [loan_label_col, "tgl_konv", "Kurs @ Konversi", "Kurs Awal", "Alert"]]
                
            else:
                st.warning("Tanggal amatan tidak menghasilkan kurs USDJPY (threshold) yang valid.")


        with st.container(border=True):
         
            st.markdown(
                    """
                    <h6 style="background-color:#100E34; color: white; padding: 7px; border-radius: 5px;">
                        Analisis Timing Konversi Pinjaman
                    </h6>
                    """, unsafe_allow_html=True
                )   


            # ------ siapkan data sekali ------
            df_kurs_cross = data_kurs.copy()
            df_kurs_cross["Dates"] = pd.to_datetime(df_kurs_cross["Dates"])
            df_kurs_cross = df_kurs_cross.sort_values("Dates").reset_index(drop=True)
            df_kurs_cross["JPYIDR_Cross"] = df_kurs_cross["USDIDR"] / df_kurs_cross["USDJPY"]
            has_aktual = "JPYIDR" in df_kurs_cross.columns

            # buka expander supaya tidak “menghilang” saat rerun
            st.write("")
            with st.expander("Cross Rate Analysis", expanded=True):
                colcross1, colcross2, colcross3 = st.columns(3,gap="small")



                with colcross1:
                    st.write('Pergerakan JPY/IDR - Cross Rate vs Aktual')

                    # 1) Siapkan data dengan aman
                    df_kurs_cross = data_kurs.copy()
                    df_kurs_cross["Dates"] = pd.to_datetime(df_kurs_cross["Dates"], errors="coerce")
                    # Wajib ada USDIDR & USDJPY untuk cross
                    needed = ["USDIDR", "USDJPY"]
                    missing = [c for c in needed if c not in df_kurs_cross.columns]
                    if missing:
                        st.warning(f"Kolom wajib hilang: {', '.join(missing)}")
                    # drop baris yang tidak bisa dihitung cross
                    df_kurs_cross = df_kurs_cross.dropna(subset=["Dates"] + [c for c in needed if c in df_kurs_cross.columns])
                    df_kurs_cross = df_kurs_cross.sort_values("Dates").reset_index(drop=True)

                    if df_kurs_cross.empty or not set(needed).issubset(df_kurs_cross.columns):
                        st.info("Tidak ada data yang cukup untuk dihitung.")
                    else:
                        # 2) Hitung cross & siapkan seri
                        df_kurs_cross["JPYIDR_Cross"] = df_kurs_cross["USDIDR"] / df_kurs_cross["USDJPY"]
                        has_aktual = ("JPYIDR" in df_kurs_cross.columns) and df_kurs_cross["JPYIDR"].notna().any()

                        x_vals = df_kurs_cross["Dates"].dt.strftime("%Y-%m-%d").tolist()
                        y_cross = [None if pd.isna(v) else float(v) for v in df_kurs_cross["JPYIDR_Cross"].round(2).tolist()]
                        y_aktual = (
                            [None if pd.isna(v) else float(v) for v in df_kurs_cross["JPYIDR"].round(2).tolist()]
                            if has_aktual else []
                        )

                        # 3) Range Y dari nilai valid
                        vals = [v for v in (y_cross + (y_aktual if has_aktual else [])) if v is not None]
                        if not vals:
                            st.info("Tidak ada nilai valid untuk digambar.")
                        else:
                            y_min = min(vals) * 0.97
                            y_max = max(vals) * 1.03

                            series_list = [
                                {
                                    "name": "JPYIDR (Cross)",
                                    "type": "line",
                                    "showSymbol": False,
                                    "data": y_cross,
                                    "lineStyle": {"width": 2, "type": "dashed"},
                                    "sampling": "lttb"
                                }
                            ]
                            if has_aktual:
                                series_list.insert(0, {
                                    "name": "JPYIDR (Aktual)",
                                    "type": "line",
                                    "showSymbol": False,
                                    "data": y_aktual,
                                    "lineStyle": {"width": 2},
                                    "sampling": "lttb"
                                })

                            options_cross = {
                                "backgroundColor": "transparent",
                                "color": ["#3B82F6", "#EF4444"] if has_aktual else ["#EF4444"],
                                "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
                                "legend": {
                                    "data": ["JPYIDR (Aktual)", "JPYIDR (Cross)"] if has_aktual else ["JPYIDR (Cross)"],
                                    "top": 10, "left": "center", "type": "scroll"
                                },
                                "grid": {"left": 48, "right": 40, "top": 60, "bottom": 70, "containLabel": True},
                                "xAxis": {
                                    "type": "category",
                                    "data": x_vals,
                                    "axisLabel": {"formatter": "{value}"},
                                    "name": "Tanggal", "nameLocation": "middle", "nameGap": 40,
                                    "nameTextStyle": {"fontSize": 12, "fontWeight": "bold"},
                                },
                                "yAxis": {"type": "value", "name": "JPY/IDR", "min": y_min, "max": y_max},
                                "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18, "bottom": 20}],
                                "series": series_list
                            }

                            # 4) Render — pastikan key unik (hindari bentrok dengan chart lain)
                            st_echarts(options=options_cross, height="420px", width="100%",
                                    key=f"echarts_cross_vs_aktual_{len(x_vals)}_{int(y_max)}")

                # ================= col 2: Deviasi =================
                with colcross2:
                    st.write('Deviasi JPY/IDR: Cross vs Aktual')

                    if has_aktual:
                        df_kurs_cross["Deviation (%)"] = 100.0 * (
                            (df_kurs_cross["JPYIDR_Cross"] - df_kurs_cross["JPYIDR"]) / df_kurs_cross["JPYIDR"]
                        )

                        x_vals = df_kurs_cross["Dates"].dt.strftime("%Y-%m-%d").tolist()
                        y_dev  = df_kurs_cross["Deviation (%)"].astype(float).round(2).tolist()

                        thr = 1.5
                        vals = [v for v in y_dev if v is not None]
                        if not vals:
                            st.info("Tidak ada data deviasi untuk digambar.")
                        else:
                            ymin = min(vals + [-thr]) - 0.2
                            ymax = max(vals + [ thr]) + 0.2

                            options_dev = {
                                "backgroundColor": "transparent",
                                "color": ["#3B82F6"],
                                "tooltip": {
                                    "trigger": "axis", "axisPointer": {"type": "cross"},
                                    "valueFormatter": "function (val) { if(val==null){return '-';} return Number(val).toFixed(2) + '%'; }"
                                },
                                "legend": {"data": ["Deviation (%)"], "top": 10, "left": "center"},
                                "grid": {"left": 48, "right": 40, "top": 60, "bottom": 70, "containLabel": True},
                                "xAxis": {
                                    "type": "category", "data": x_vals,
                                    "axisLabel": {"formatter": "{value}"},
                                    "name": "Tanggal", "nameLocation": "middle", "nameGap": 40,
                                    "nameTextStyle": {"fontSize": 12, "fontWeight": "bold"},
                                },
                                "yAxis": {
                                    "type": "value", "name": "Deviasi (%)", "min": round(ymin), "max": ymax,
                                    "axisLabel": {"formatter": "{value}%"}
                                },
                                "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18, "bottom": 20}],
                                "series": [{
                                    "name": "Deviation (%)", "type": "line", "showSymbol": False,
                                    "data": y_dev, "lineStyle": {"width": 2},
                                    "markLine": {
                                        "symbol": "none", "silent": True,
                                        "lineStyle": {"type": "dashed", "width": 2, "color": "#ef4444"},
                                        "data": [
                                            {"yAxis":  thr, "label": {"show": True, "position": "middle",
                                                                    "formatter": "+1.5%",
                                                                    "backgroundColor": "rgba(255,255,255,0.85)",
                                                                    "padding": [2,6], "borderRadius": 4}},
                                            {"yAxis": -thr, "label": {"show": True, "position": "middle",
                                                                    "formatter": "-1.5%",
                                                                    "backgroundColor": "rgba(255,255,255,0.85)",
                                                                    "padding": [2,6], "borderRadius": 4}},
                                        ],
                                    },
                                }],
                            }
                            
                            st_echarts(options=options_dev, height="420px", width="100%", key="echarts_deviasi_cross")
                    else:
                        st.info("Kolom **JPYIDR** (aktual) tidak tersedia, deviasi tidak dapat dihitung.")

                # ================= col 3: Rekomendasi =================
                with colcross3:
                    if has_aktual:
                        min_date = df_kurs_cross['Dates'].min().date()
                        max_date = df_kurs_cross['Dates'].max().date()

                        st.write("📅Pilih Periode Pengamatan Deviasi")
                        colstart, colend = st.columns(2)
                        with colstart:
                            default_start = max_date - dt.timedelta(days=10)
                            start_date = st.date_input("Tanggal Awal", value=default_start,
                                                    min_value=min_date, max_value=max_date, key="dev_start")
                        with colend:
                            end_date = st.date_input("Tanggal Akhir", value=max_date,
                                                    min_value=min_date, max_value=max_date, key="dev_end")

                        mask_ = (df_kurs_cross['Dates'].dt.date >= start_date) & (df_kurs_cross['Dates'].dt.date <= end_date)
                        df_filtered_kurs = df_kurs_cross.loc[mask_]

                        if df_filtered_kurs.empty:
                            st.warning("⚠️ Tidak ada data pada rentang tanggal tersebut.")
                        else:
                            last_dev = float(df_filtered_kurs['Deviation (%)'].mean())
                            threshold = 1.5

                            #colm1, colm2 = st.columns([4, 2])
                            #with colm1:
                            st.info(f"📊 Rata-rata Deviasi JPY/IDR: Cross vs Aktual, "
                                        f"dari **{start_date.strftime('%d %b %Y')}** s.d **{end_date.strftime('%d %b %Y')}**")
                            #with colm2:
                            st.metric(label="", value=f"{last_dev:.2f}%")

                            st.markdown(f"**Threshold Praktis (Deviasi):** ±{threshold}%")

                            if abs(last_dev) > threshold:
                                if last_dev > 0:
                                    st.warning("💡 JPY/IDR **aktual lebih tinggi** dari nilai wajarnya (cross). Potensi **JPY overvalued**.")
                                    st.markdown("🕒 **Rekomendasi:** **TUNDA** konversi pinjaman JPY ke IDR.")
                                else:
                                    st.success("✅ JPY/IDR **aktual lebih rendah** dari nilai wajarnya (cross). Potensi **JPY undervalued**.")
                                    st.markdown("💰 **Rekomendasi:** **LAKUKAN** konversi pinjaman JPY ke IDR **sekarang**.")
                            else:
                                st.info("📊 Deviasi dalam batas normal. Tidak ada sinyal kuat.")
                                st.markdown("🤔 **Rekomendasi:** Tunggu sinyal lebih kuat, atau pertimbangkan faktor lain.")
                    else:
                        st.info("Panel rekomendasi membutuhkan kolom **JPYIDR** (aktual).")

            with st.expander("📈Analisis Moving Average (MA & EMA) - JPY/IDR", expanded=True):
                df_kurs_ma = data_kurs.copy()
                df_kurs_ma["Dates"] = pd.to_datetime(df_kurs_ma["Dates"], errors="coerce")
                df_kurs_ma = df_kurs_ma.dropna(subset=["Dates"]).sort_values("Dates").reset_index(drop=True)

                min_date = df_kurs_ma['Dates'].min().date()
                max_date = df_kurs_ma['Dates'].max().date()

                # ---- Header + picker rentang ----
                st.markdown(
                                """
                                <div style="background-color:#d4edda; padding:5px; border-radius:5px; margin-bottom:10px">
                                <p style="color:#155724; font-size:16px; font-weight:bold; margin:0">Pilih Periode Pengamatan dan Periode MA & EMA</p>
                                """,
                                unsafe_allow_html=True,
                            )
                #st.markdown("### 📅 Pilih Periode Pengamatan")
                colma1, colma2, colma3 = st.columns([5,5,3])
                with colma1:
                    start_date_ma = st.date_input(
                        "Tanggal Awal", value=max_date - dt.timedelta(days=30),
                        min_value=min_date, max_value=max_date, key="ma_start"
                    )
                with colma2:
                    end_date_ma = st.date_input(
                        "Tanggal Akhir", value=max_date,
                        min_value=min_date, max_value=max_date, key="ma_end"
                    )

                # ---- Filter data sesuai periode ----
                mask_ma = (df_kurs_ma['Dates'].dt.date >= start_date_ma) & (df_kurs_ma['Dates'].dt.date <= end_date_ma)
                df_filtered_ma = df_kurs_ma.loc[mask_ma].copy()

                if df_filtered_ma.empty:
                    st.warning("⚠️ Tidak ada data untuk rentang tanggal yang dipilih.")
                else:
                    with colma3:
                        ma_period = st.selectbox(
                                "📊 Pilih Periode MA & EMA",
                                [5, 10, 20, 50],
                                index=1,
                                key="ma_period",
                            )

                    # ========== Chart USDJPY ==========
                    colusdjpy, colusdidr, colrek = st.columns([5,5,3])

                    with colusdjpy:
                        st.write(f"💹 USDJPY — MA & EMA ({ma_period} hari)")

                        if "USDJPY" in df_filtered_ma.columns:
                            # hitung MA/EMA
                            df_filtered_ma['USDJPY_MA']  = df_filtered_ma['USDJPY'].rolling(window=ma_period).mean()
                            df_filtered_ma['USDJPY_EMA'] = df_filtered_ma['USDJPY'].ewm(span=ma_period, adjust=False).mean()

                            x_usdjpy = df_filtered_ma["Dates"].dt.strftime("%Y-%m-%d").tolist()
                            y_usdjpy      = [None if pd.isna(v) else float(v) for v in df_filtered_ma["USDJPY"].tolist()]
                            y_usdjpy_ma   = [None if pd.isna(v) else float(v) for v in df_filtered_ma["USDJPY_MA"].tolist()]
                            y_usdjpy_ema  = [None if pd.isna(v) else float(v) for v in df_filtered_ma["USDJPY_EMA"].tolist()]

                            vals = [v for v in (y_usdjpy + y_usdjpy_ma + y_usdjpy_ema) if v is not None]
                            ymin = min(vals) * 0.97 if vals else 0
                            ymax = max(vals) * 1.03 if vals else 1

                            options_usdjpy = {
                                "backgroundColor": "transparent",
                                "color": ["#3B82F6", "#F59E0B", "#10B981"],  # biru, oranye, hijau
                                "tooltip": {
                                    "trigger": "axis",
                                    "axisPointer": {"type": "cross"},
                                    "valueFormatter": "function (val) { return (val==null) ? '-' : Number(val).toFixed(2); }"
                                },
                                "legend": {"data": ["USDJPY", "USDJPY_MA", "USDJPY_EMA"], "top": 1, "left": "center", "type": "scroll"},
                                "grid": {"left": 20, "right": 16, "top": 70, "bottom": 70, "containLabel": True},
                                "xAxis": {
                                    "type": "category", "data": x_usdjpy,
                                    "name": "Tanggal", "nameLocation": "middle", "nameGap": 36,
                                    "nameTextStyle": {"fontSize": 12, "fontWeight": "bold"},
                                },
                                "yAxis": {"type": "value", "name": "USDJPY", "min": round(ymin), "max": round(ymax)},
                                "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18, "bottom": 20}],
                                "series": [
                                    {"name": "USDJPY",     "type": "line", "showSymbol": False, "data": y_usdjpy,     "lineStyle": {"width": 2}},
                                    {"name": "USDJPY_MA",  "type": "line", "showSymbol": False, "data": y_usdjpy_ma,  "lineStyle": {"width": 2}},
                                    {"name": "USDJPY_EMA", "type": "line", "showSymbol": False, "data": y_usdjpy_ema, "lineStyle": {"width": 2}},
                                ],
                            }
                            st_echarts(options=options_usdjpy, height="360px", width="100%", key=f"ech_ma_usdjpy_{ma_period}")
                        else:
                            st.info("Kolom **USDJPY** tidak tersedia.")

                    # ========== Chart USDIDR ==========
                    with colusdidr:
                        st.write(f"💹 USDIDR — MA & EMA ({ma_period} hari)")

                        if "USDIDR" in df_filtered_ma.columns:
                            df_filtered_ma['USDIDR_MA']  = df_filtered_ma['USDIDR'].rolling(window=ma_period).mean()
                            df_filtered_ma['USDIDR_EMA'] = df_filtered_ma['USDIDR'].ewm(span=ma_period, adjust=False).mean()

                            x_usdidr = df_filtered_ma["Dates"].dt.strftime("%Y-%m-%d").tolist()
                            y_usdidr      = [None if pd.isna(v) else float(v) for v in df_filtered_ma["USDIDR"].tolist()]
                            y_usdidr_ma   = [None if pd.isna(v) else float(v) for v in df_filtered_ma["USDIDR_MA"].tolist()]
                            y_usdidr_ema  = [None if pd.isna(v) else float(v) for v in df_filtered_ma["USDIDR_EMA"].tolist()]

                            vals = [v for v in (y_usdidr + y_usdidr_ma + y_usdidr_ema) if v is not None]
                            ymin = min(vals) * 0.97 if vals else 0
                            ymax = max(vals) * 1.03 if vals else 1

                            options_usdidr = {
                                "backgroundColor": "transparent",
                                "color": ["#3B82F6", "#F59E0B", "#10B981"],
                                "tooltip": {
                                    "trigger": "axis",
                                    "axisPointer": {"type": "cross"},
                                    "valueFormatter": "function (val) { return (val==null) ? '-' : Number(val).toFixed(2); }"
                                },
                                
                                "legend": {"data": ["USDIDR", "USDIDR_MA", "USDIDR_EMA"], "top": 1, "left": "center", "type": "scroll"},
                                "grid": {"left": 20, "right": 16, "top": 70, "bottom": 70, "containLabel": True},
                                "xAxis": {
                                    "type": "category", "data": x_usdidr,
                                    "name": "Tanggal", "nameLocation": "middle", "nameGap": 36,
                                    "nameTextStyle": {"fontSize": 12, "fontWeight": "bold"},
                                },
                                "yAxis": {"type": "value", "name": "USDIDR", "min": round(ymin), "max": round(ymax)},
                                "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18, "bottom": 20}],
                                "series": [
                                    {"name": "USDIDR",     "type": "line", "showSymbol": False, "data": y_usdidr,     "lineStyle": {"width": 2}},
                                    {"name": "USDIDR_MA",  "type": "line", "showSymbol": False, "data": y_usdidr_ma,  "lineStyle": {"width": 2}},
                                    {"name": "USDIDR_EMA", "type": "line", "showSymbol": False, "data": y_usdidr_ema, "lineStyle": {"width": 2}},
                                ],
                            }
                            st_echarts(options=options_usdidr, height="360px", width="100%", key=f"ech_ma_usdidr_{ma_period}")
                        else:
                            st.info("Kolom **USDIDR** tidak tersedia.")

                    # ========== Sinyal & Rekomendasi ==========
                    # ambil baris terakhir yang lengkap
                    latest = df_filtered_ma.dropna(subset=["USDJPY","USDJPY_MA","USDJPY_EMA","USDIDR","USDIDR_MA","USDIDR_EMA"])
                    if not latest.empty:
                        latest = latest.iloc[-1]

                        def check_trend(val, ma, ema):
                            # mengikuti logika yang kamu pakai sebelumnya
                            return val > ma and val > ema

                        usdjpy_signal = check_trend(latest['USDJPY'], latest['USDJPY_MA'], latest['USDJPY_EMA'])
                        usdidr_signal = (latest['USDIDR'] < latest['USDIDR_MA']) and (latest['USDIDR'] < latest['USDIDR_EMA'])

                        with colrek:
                            st.subheader("Rekomendasi Strategis")
                            if usdjpy_signal and usdidr_signal:
                                st.success("✅ **Kondisi Ideal!**\n- USDJPY tren naik (JPY melemah terhadap USD)\n- USDIDR tren turun (IDR menguat terhadap USD)\n\n💰 **Rekomendasi:** Lakukan konversi pinjaman JPY ke IDR sekarang.")
                            elif usdjpy_signal and not usdidr_signal:
                                st.warning("⚠️ USDJPY tren naik (bagus), tetapi USDIDR masih tinggi.\n💡 **Saran:** Tunggu IDR menguat lebih lanjut sebelum konversi.")
                            elif not usdjpy_signal and usdidr_signal:
                                st.warning("⚠️ USDIDR tren turun (bagus), tetapi USDJPY masih rendah.\n💡 **Saran:** Tunggu JPY melemah terhadap USD.")
                            else:
                                st.info("🤔 Belum ada sinyal ideal.\n💡 **Saran:** Tunggu hingga kondisi lebih menguntungkan.")
                    else:
                        with colrek:
                            st.subheader("Rekomendasi Strategis")
                            st.info("Data belum cukup (MA/EMA) untuk menghasilkan sinyal.")

        with st.container(border=True):
         
            st.markdown(
                    """
                    <h6 style="background-color:#100E34; color: white; padding: 7px; border-radius: 5px;">
                        Proyeksi Nilai Tukar
                    </h6>
                    """, unsafe_allow_html=True
                )   
            
            st.write("")

            

            with st.expander("Proyeksi Kurs", expanded=True):
                col1, col2 = st.columns([4,4])
                df = st.session_state.data_kurs.copy()
                df.set_index("Dates", inplace=True)
                
                with col1:
                    st.session_state.start_date = st.date_input("Pilih Start Date", df.index.min())
                    st.session_state.end_date = st.date_input("Pilih End Date", df.index.max())
                with col2:
                    st.session_state.periods = st.slider("Pilih jumlah hari proyeksi:", 1, 30, st.session_state.periods)
                    st.session_state.columns = st.multiselect("Pilih nilai tukar untuk diproyeksi:", df.columns, default=st.session_state.columns)
                st.subheader("Hasil Proyeksi")
                cola, colb, colc = st.columns(3)    
                df = df.loc[st.session_state.start_date:st.session_state.end_date]
                

                with cola:
                    df_arima_forecast = pd.DataFrame()
                    future_dates = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=st.session_state.periods, freq='B')
                    future_dates_formatted = future_dates.strftime('%d-%m-%Y')
                    for column in st.session_state.columns:
                        model = ARIMA(df[column], order=(1, 1, 1))
                        model_fit = model.fit()
                        df_arima_forecast[column] = model_fit.forecast(steps=st.session_state.periods)
                    
                    df_arima_forecast.index = future_dates_formatted
                    st.write("Hasil Forecast ARIMA:", round(df_arima_forecast))
                with colb:
                    df_Exponential_forecast = pd.DataFrame()
                    for column in st.session_state.columns:
                        model = ExponentialSmoothing(df[column], trend='add', seasonal='add', seasonal_periods=12)
                        model_fit = model.fit()
                        df_Exponential_forecast[column] = model_fit.forecast(steps=st.session_state.periods)
                    
                    df_Exponential_forecast.index = future_dates_formatted
                    st.write("Hasil Forecast Exponential Smoothing:", round(df_Exponential_forecast))
                with colc:
                    df_prophet_forecast = pd.DataFrame()
                    for column in st.session_state.columns:
                        prophet_df = df[column].reset_index()
                        prophet_df.columns = ['ds', 'y']
                        model = Prophet()
                        model.fit(prophet_df)
                        future = pd.DataFrame({'ds': future_dates})
                        forecast = model.predict(future)
                        df_prophet_forecast[column] = forecast['yhat'].values

                    df_prophet_forecast.index = future_dates_formatted
                    st.write("Hasil Forecast Prophet:", round(df_prophet_forecast))
