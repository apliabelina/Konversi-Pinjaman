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

st.set_page_config(layout="wide", page_title="Konversi Pinjaman")

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Silakan login terlebih dahulu di halaman Home.")
    st.stop()
st.title("Data Market")


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

#data_file1 = st.file_uploader("Upload File Data Historis", type=['xlsx'])

# Path ke file Excel di folder pages
file_path = "pages/Data Historis - Monitoring Timing Konversi Pinjaman.xlsx"

# Fungsi baca data dari sheet
def baca_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)



data_kurs        = baca_data(file_path, "Kurs JPY")
data_yield       = baca_data(file_path, "Yield")
data_policyrate  = baca_data(file_path,"Rate Bank Central")
data_GI = baca_data(file_path, "Rekap JPY")

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
st.info(f"📅 Data terakhir yang tersedia adalah data per tanggal **{as_of_str}**")



# Tab Navigation
tab1, tab2, tab3 = st.tabs(["Nilai Tukar", "Yield", "Suku Bunga Bank Sentral"])

# Tab 1: Nilai Tukar
if "data_kurs" in st.session_state:
    with tab1:
        as_of = st.date_input("As of (Pilih Tanggal)", value=st.session_state.as_of or datetime.today().date())
        st.session_state.as_of = pd.Timestamp(as_of)
        data_kurs = st.session_state["data_kurs"]
        data_kurs = data_kurs[data_kurs['Dates'] <= st.session_state.as_of]
        data_GI = st.session_state["data_GI"]
        #st.subheader(f"Data Kurs Hingga {st.session_state.as_of.strftime('%Y-%m-%d')}")
        with st.expander("Data Historis Kurs"):
            colaa, colbb = st.columns(2)
            with colaa:
                fig1 = go.Figure()
                for currency in ['DXY', 'USDJPY', 'JPYIDR']:
                    fig1.add_trace(go.Scatter(
                        x=data_kurs['Dates'], y=data_kurs[currency], mode='lines', name=currency, line=dict(color=color_curr[currency])
                    ))
                
                for date in data_GI['Tanggal Konversi Awal']:
                    fig1.add_shape(type="line",
                            x0=pd.to_datetime(date), y0=12000,  
                            x1=pd.to_datetime(date), y1=17000,
                            xref='x',
                            yref='y2',  # Penting: arahkan ke yaxis2
                            line=dict(color='grey', width=1, dash='dot'), name=f'Tanggal Konversi :{date}')
                
                fig1.add_trace(go.Scatter(
                    x=data_kurs['Dates'], y=data_kurs['USDIDR'], mode='lines', name='USDIDR', line=dict(color=color_curr['USDIDR']), yaxis="y2"
                ))
                
                
                fig1.update_layout(
                    title='Historis Nilai Tukar JPY',
                    yaxis=dict(title="DXY, USDJPY, JPYIDR", side='left'),
                    yaxis2=dict(title="USDIDR", overlaying='y', side='right'),
                    plot_bgcolor='rgba(0,0,0,0)',  # transparan
                    paper_bgcolor='rgba(0,0,0,0)',  # transparan,
                    legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,     # lebih rendah dari area chart
                    xanchor="center",
                    x=0.5
                )
                )

                st.plotly_chart(fig1, use_container_width=True)

            #---- membandingan USDJPY ----
            with colbb:
                data_GI['Tanggal Konversi Awal'] = pd.to_datetime(data_GI['Tanggal Konversi Awal'])
                data_kurs['Dates'] = pd.to_datetime(data_kurs['Dates'])

                # Gabungkan berdasarkan tanggal yang sama persis
                
                data_GI = data_GI.merge(
                    data_kurs[['Dates', 'USDJPY']].rename(columns={'Dates': 'Tanggal Konversi Awal', 'USDJPY': 'Kurs USDJPY'}),
                    on='Tanggal Konversi Awal',
                    how='left'
                    )
                #tanggal amatan
                as_of_str_ = data_kurs['Dates'].iloc[-1].strftime("%Y-%m-%d") 
                #st.write(as_of_str_)
                tanggal_akhir = st.text_input("Input Tanggal Pengamatan (YYYY-MM-DD):", 
                                               value=(as_of_str_))
                tanggal_input = pd.to_datetime(tanggal_akhir)
                kurs_usdjpy = data_kurs.loc[data_kurs['Dates'] == tanggal_input, 'USDJPY'].values

                #----scatter plot ----
                # Buat grafik scatter dari data_GI
                fig2 = go.Figure()

                fig2.add_trace(go.Scatter(
                    x=data_GI['Tanggal Konversi Awal'],
                    y=data_GI['Kurs USDJPY'],
                    mode='markers+lines',
                    name='Kurs USDJPY',
                    marker=dict(color='blue', size=8),
                    line=dict(dash='dot', color='blue')
                ))
                # Garis horizontal pada kurs tanggal_input
                x_start = data_GI['Tanggal Konversi Awal'].min()
                x_end = data_GI['Tanggal Konversi Awal'].max()
                fig2.add_shape(
                    type='line',
                    x0=x_start, x1=x_end,  # Bentang sepanjang x
                    y0=kurs_usdjpy[0], y1=kurs_usdjpy[0],  # Tinggi tetap di nilai kurs
                    line=dict(color='red', width=2, dash='dash'),
                    xref='x', yref='y'
                )

                # Tambahkan anotasi (opsional)
                fig2.add_annotation(
                    x=x_end,
                    y=kurs_usdjpy[0],
                    text=f"{tanggal_input.date()}<br>Kurs: {kurs_usdjpy[0]:.2f}",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-40,
                    bgcolor="white"
                )

                fig2.update_layout(
                    title='Perbandingan Kurs USDJPY (Tanggal amatan vs Tanggal Konversi)',
                    xaxis_title='Tanggal Konversi Awal',
                    yaxis_title='Kurs USDJPY',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )

                # Tampilkan grafik di Streamlit
                st.plotly_chart(fig2, use_container_width=True)

            # Tambahkan kolom alert berdasarkan kondisi
            data_GI['Alert'] = data_GI['Kurs USDJPY'].apply(
                lambda x: 'potensi untuk re-konversi' if x < kurs_usdjpy[0] else ''
            )

            # Tampilkan hasilnya di Streamlit (opsional)
            #st.write("Data GI dengan status alert:")
            #st.dataframe(data_GI)
            if data_GI['Alert'].eq('potensi untuk re-konversi').all():
                st.markdown("""
                <style>
                .flash-alert {
                    font-size: 24px;
                    font-weight: bold;
                    color: green;
                    animation: flash 1s infinite;
                    text-align: center;
                    padding: 1em;
                    border: 3px solid green;
                    border-radius: 10px;
                    background-color: #e6ffe6;
                }

                @keyframes flash {
                    0% {opacity: 1;}
                    50% {opacity: 0;}
                    100% {opacity: 1;}
                }
                </style>
                <div class="flash-alert">
                    🚨 RE-KONVERSI POTENSI UNTUK DILAKUKAN 🚨
                </div>
                """, unsafe_allow_html=True)
        
        with st.expander("Proyeksi Kurs"):
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
                st.write("Hasil Forecast ARIMA:", df_arima_forecast)
            with colb:
                df_Exponential_forecast = pd.DataFrame()
                for column in st.session_state.columns:
                    model = ExponentialSmoothing(df[column], trend='add', seasonal='add', seasonal_periods=12)
                    model_fit = model.fit()
                    df_Exponential_forecast[column] = model_fit.forecast(steps=st.session_state.periods)
                
                df_Exponential_forecast.index = future_dates_formatted
                st.write("Hasil Forecast Exponential Smoothing:", df_Exponential_forecast)
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
                st.write("Hasil Forecast Prophet:", df_prophet_forecast)

        st.header("Analisis Timing Pelaksanaan Konversi Pinjaman")
        with st.expander("Cross Rate Analysis"):
            colcross1, colcross2, colcross3 = st.columns(3)
            with colcross1:
                st.write('Pergerakan JPY/IDR - Cross Rate vs Aktual')
                df_kurs          = data_kurs.copy()
                df_kurs['Dates'] = pd.to_datetime(df_kurs['Dates'])
                df_kurs          = df_kurs.sort_values('Dates')
                df_kurs['JPYIDR_Cross'] = df_kurs['USDIDR'] / df_kurs['USDJPY']

                df_long = df_kurs.melt(
                    id_vars='Dates',
                    value_vars=['JPYIDR_Cross', 'JPYIDR'] if 'JPYIDR' in df_kurs.columns else ['JPYIDR_Cross'],
                    var_name='Tipe',
                    value_name='Nilai Tukar'
                )

                fig_cross = px.line(
                    df_long,
                    x='Dates',
                    y='Nilai Tukar',
                    color='Tipe',
                    line_dash='Tipe',
                    #title='Pergerakan JPY/IDR - Cross Rate vs Aktual',
                    labels={'Dates': 'Tanggal', 'Nilai Tukar': 'JPY/IDR'},
                    color_discrete_map={
                        'JPYIDR': 'blue',
                        'JPYIDR_Cross': 'red'
                    }
                )

                fig_cross.update_layout(
                    height=400,
                    legend_title_text='Keterangan',
                    xaxis_title='Tanggal',
                    yaxis_title='Nilai Tukar',
                )

                st.plotly_chart(fig_cross, use_container_width=True)
                # Selisih antara Cross dan Aktual
            with colcross2:
                st.write('Deviasi JPY/IDR: Cross vs Aktual')
                if 'JPYIDR' in df_kurs.columns:
                    df_kurs['Deviation (%)'] = 100 * (df_kurs['JPYIDR_Cross'] - df_kurs['JPYIDR']) /df_kurs['JPYIDR']
                    figdev = px.line(df_kurs, x='Dates', y='Deviation (%)', 
                    labels={'Deviation (%)': 'Deviasi (%)', 'Dates': 'Tanggal'})

        #            Tambahkan garis threshold ±1.5%
                    figdev.add_shape(
                        type="line", line=dict(color="red", dash="dash"), x0=df_kurs['Dates'].min(),
                        x1=df_kurs['Dates'].max(), y0=1.5, y1=1.5,
                        name="+1.5% Threshold"
                    )
                    figdev.add_shape(
                        type="line", line=dict(color="red", dash="dash"), x0=df_kurs['Dates'].min(),
                        x1=df_kurs['Dates'].max(), y0=-1.5, y1=-1.5,
                        name="-1.5% Threshold"
                    )
                    # Tambahkan anotasi label threshold
                    figdev.add_annotation(x=df_kurs['Dates'].min(), y=1.5, text="+1.5%", showarrow=False, yshift=10, font=dict(color="red"))
                    figdev.add_annotation(x=df_kurs['Dates'].min(), y=-1.5, text="-1.5%", showarrow=False, yshift=-10, font=dict(color="red"))
                    figdev.update_layout(height=400)

                st.plotly_chart(figdev, use_container_width=True)
            with colcross3:    
                #st.write("📍 Rekomendasi")
                #st.subheader("📍 Rekomendasi")
                if 'JPYIDR' in df.columns:
                    # Ambil range tanggal dari data
                    min_date = df_kurs['Dates'].min().date()
                    max_date = df_kurs['Dates'].max().date()

                    st.write("📅Pilih Periode Pengamatan Deviasi")
                    colstart, colend = st.columns(2)
                    with colstart:
                        start_date = st.date_input("Tanggal Awal", value=max_date - datetime.timedelta(days=10), min_value=min_date, max_value=max_date)
                    with colend:
                        end_date = st.date_input("Tanggal Akhir", value=max_date, min_value=min_date, max_value=max_date)
                    
                    # Filter data berdasarkan tanggal yang dipilih
                    mask_ = (df_kurs['Dates'].dt.date >= start_date) & (df_kurs['Dates'].dt.date <= end_date)
                    df_filtered_kurs = df_kurs.loc[mask_]

                    
                    if df_filtered_kurs.empty:
                        st.warning("⚠️ Tidak ada data pada rentang tanggal tersebut.")
                    else:
                        # Hitung deviasi rata-rata dari periode yang dipilih
                        last_dev = df_filtered_kurs['Deviation (%)'].mean()
                        threshold = 1.5  # threshold praktis (%)

                    
                    
                        colm1, colm2 = st.columns([4, 2])  # Rasio 1:2:1 biar metric ada di tengah
                        with colm1:
                            st.info(f"📊 Rata-rata Deviasi JPY/IDR: Cross vs Aktual, dari **{start_date.strftime('%d %b %Y')}** s.d **{end_date.strftime('%d %b %Y')}**")
                        with colm2:
                            st.metric(
                                label="",
                                value=f"{last_dev:.2f}%",
                                # delta=f"{delta:+.2f}%" if delta is not None else None
                            )
                        
                        st.markdown(f"**Threshold Praktis (Deviasi):** ±{threshold}%")


                        if abs(last_dev) > threshold:
                            if last_dev > 0:
                                st.warning("💡 JPY/IDR aktual *lebih tinggi* dari nilai wajarnya. Ini bisa berarti **JPY overvalued**. \
                    Pertimbangkan untuk menunggu sebelum konversi (tunda).")
                                st.markdown("🕒 **Rekomendasi:** TUNDA konversi pinjaman JPY ke IDR.")
                            else:
                                st.success("✅ JPY/IDR aktual *lebih rendah* dari nilai wajarnya. Ini bisa berarti **JPY undervalued**. \
                    Waktu yang baik untuk konversi!")
                                st.markdown("💰 **Rekomendasi:** LAKUKAN konversi pinjaman JPY ke IDR SEKARANG.")
                        else:
                            st.info("📊 Deviasi masih dalam batas normal. Tidak ada sinyal kuat untuk arbitrage atau tekanan nilai tukar.")
                            st.markdown("🤔 **Rekomendasi:** Bisa tunggu sinyal lebih kuat, atau lanjut berdasarkan faktor eksternal lain.")

        with st.expander("📈Analisis Moving Average (MA & EMA) - JPY/IDR"):   
            # Tanggal awal & akhir dari data
            min_date = df_kurs['Dates'].min().date()
            max_date = df_kurs['Dates'].max().date()      
            # Input tanggal awal & akhir untuk filter data
            st.markdown("### 📅 Pilih Periode Pengamatan")
            colma1, colma2,colma3 = st.columns(3)
            with colma1:

                start_date_ma = st.date_input("Tanggal Awal ", value=max_date - datetime.timedelta(days=30), min_value=min_date, max_value=max_date)
            with colma2:
                end_date_ma = st.date_input("Tanggal Akhir ", value=max_date, min_value=min_date, max_value=max_date) 

            # Filter data berdasarkan periode
            mask_ma = (df_kurs['Dates'].dt.date >= start_date_ma) & (df_kurs['Dates'].dt.date <= end_date_ma)
            df_filtered_ma = df_kurs.loc[mask_ma].copy()  

            if df_filtered_ma.empty:
                st.warning("⚠️ Tidak ada data untuk rentang tanggal yang dipilih.")
            else:
            # Pilih periode MA/EMA
                with colma3:
                    with st.container():
                        st.markdown(
                            """
                            <div style="background-color:#d4edda; padding:5px; border-radius:5px; margin-bottom:10px">
                            <p style="color:#155724; font-size:16px; font-weight:bold; margin-top:0; margin-bottom:0">📊 Pilih Periode MA & EMA</p>
                            """,
                            unsafe_allow_html=True
                        )

                        ma_period = st.selectbox(" ", [5, 10, 20, 50], index=1, label_visibility="collapsed")

                        st.markdown("</div>", unsafe_allow_html=True)
    
               ### ==== USDJPY ====
                colusdjpy, colusdidr, colrek =st.columns([5,5,3])
                with colusdjpy:
                    st.subheader("💹 USDJPY")
                    df_filtered_ma['USDJPY_MA'] = df_filtered_ma['USDJPY'].rolling(window=ma_period).mean()
                    df_filtered_ma['USDJPY_EMA'] = df_filtered_ma['USDJPY'].ewm(span=ma_period, adjust=False).mean()

                    fig_usdjpy = px.line(df_filtered_ma, x='Dates', y=['USDJPY', 'USDJPY_MA', 'USDJPY_EMA'],
                            labels={'value': 'Nilai Tukar', 'variable': 'Garis'},
                            title=f"USDJPY vs MA & EMA ({ma_period} Hari)",
                            color_discrete_map={'USDJPY': 'blue', 'USDJPY_MA': 'orange', 'USDJPY_EMA': 'green'})
                    fig_usdjpy.update_layout(legend_title_text='Garis')
                    st.plotly_chart(fig_usdjpy, use_container_width=True)
                with colusdidr:
                    ### ==== USDIDR ====
                    st.subheader("💹 USDIDR")
                    df_filtered_ma['USDIDR_MA'] = df_filtered_ma['USDIDR'].rolling(window=ma_period).mean()
                    df_filtered_ma['USDIDR_EMA'] = df_filtered_ma['USDIDR'].ewm(span=ma_period, adjust=False).mean()

                    fig_usdidr = px.line(df_filtered_ma, x='Dates', y=['USDIDR', 'USDIDR_MA', 'USDIDR_EMA'],
                                        labels={'value': 'Nilai Tukar', 'variable': 'Garis'},
                                        title=f"USDIDR vs MA & EMA ({ma_period} Hari)",
                                        color_discrete_map={'USDIDR': 'blue', 'USDIDR_MA': 'orange', 'USDIDR_EMA': 'green'})
                    fig_usdidr.update_layout(legend_title_text='Garis')
                    st.plotly_chart(fig_usdidr, use_container_width=True)

                ### ==== Sinyal Tren dan Rekomendasi ====
                latest = df_filtered_ma.dropna().iloc[-1]
                def check_trend(val, ma, ema):
                    return val > ma and val > ema  # untuk USDJPY, kita ingin dia menurun (JPY menguat)
    
                # Cek sinyal tren
                usdjpy_signal = check_trend(latest['USDJPY'], latest['USDJPY_MA'], latest['USDJPY_EMA'])
                usdidr_signal = latest['USDIDR'] < latest['USDIDR_MA'] and latest['USDIDR'] < latest['USDIDR_EMA']
                with colrek:
                    # Menampilkan rekomendasi berdasarkan sinyal
                    st.subheader("Rekomendasi Strategis")
                    if usdjpy_signal and usdidr_signal:
                        st.success("✅ **Kondisi Ideal!**\n- USDJPY tren naik (JPY melemah terhadap USD)\n- USDIDR tren turun (IDR menguat terhadap USD)\n\n💰 **Rekomendasi:** Lakukan konversi pinjaman JPY ke IDR sekarang.")
                    elif usdjpy_signal and not usdidr_signal:
                        st.warning("⚠️ USDJPY tren naik (bagus), tetapi USDIDR masih tinggi.\n💡 **Saran:** Tunggu IDR menguat lebih lanjut sebelum konversi.")
                    elif not usdjpy_signal and usdidr_signal:
                        st.warning("⚠️ USDIDR tren turun (bagus), tetapi USDJPY masih rendah.\n💡 **Saran:** Tunggu JPY melemah terhadap USD.")
                    else:
                        st.info("🤔 Belum ada sinyal ideal.\n💡 **Saran:** Tunggu hingga kondisi lebih menguntungkan.")

# Tab 2: Yield
if "data_yield" in st.session_state:
    with tab2:
        data_yield = st.session_state["data_yield"]
        data_yield = data_yield[data_yield['Dates'] <= st.session_state.as_of]
        
        #st.subheader(f"Data Yield Hingga {st.session_state.as_of.strftime('%Y-%m-%d')}")
        with st.expander("Data Historis Yield"):
            fig2 = go.Figure()
            for currency in ['GTIDR10Y', 'GTJPY10Y', 'GTEUR10Y', 'USGG10YR']:
                fig2.add_trace(go.Scatter(
                    x=data_yield['Dates'], y=data_yield[currency], mode='lines', name=currency, line=dict(color=color_yield[currency])
                ))
            fig2.update_layout(
                    #title_text='Index Nilai Tukar',
                    xaxis_rangeslider_visible=True
                    
                )
            fig2.update_layout(title='Historis Yield', plot_bgcolor='rgba(0,0,0,0)',  # transparan
                    paper_bgcolor='rgba(0,0,0,0)')  # transparan)
            st.plotly_chart(fig2, use_container_width=True)

if "data_policyrate" in st.session_state:
    with tab3:
        data_policyrate = st.session_state["data_policyrate"]
        data_policyrate = data_policyrate[data_policyrate['Dates'] <= st.session_state.as_of]
        #st.subheader(f"Data Yield Hingga {st.session_state.as_of.strftime('%Y-%m-%d')}")
        with st.expander("Data Historis Policy Rate"):
            fig3 = go.Figure()
            for currency in ['IDBIRRPO Index', 'BOJDTR Index','EURR002W Index',"FDTR Index"]:
                fig3.add_trace(go.Scatter
                            (x=data_policyrate['Dates'], 
                                y=data_policyrate[currency], 
                                mode='lines', 
                                name=currency, 
                                line=dict(color=color_type3[currency])))
            
            fig3.layout.update(
                title_text='Historis Policy Rate', 
                xaxis_rangeslider_visible=True)
            fig3.update_layout(xaxis=dict(
                        showline=True,  # Show axis line
                        linecolor='black',  # Set the color of the axis line to black
                        tickfont=dict(color='black')  # Set the tick labels to black
                        )
                    ,
                    yaxis=dict(
                        showline=False,  # Show axis line
                        linecolor='black',  # Set the color of the axis line to black
                        tickfont=dict(color='black')  # Set the tick labels to black
                        )
                    ,
                    plot_bgcolor='rgba(0,0,0,0)',  # transparan
                    paper_bgcolor='rgba(0,0,0,0)'
            ) 
            st.plotly_chart(fig3, theme="streamlit", use_container_width=True)