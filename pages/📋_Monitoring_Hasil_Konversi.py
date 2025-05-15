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

#set layout
st.set_page_config(layout="wide", page_title="Monitoring Konversi Pinjaman")
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Silakan login terlebih dahulu di halaman Home.")
    st.stop()
#im = Image.open('LOGO.png')
col11, col12 = st.columns([9,1])
with col11:
    st.header("Monitoring Konversi Pinjaman")
#with col12:
    #image = Image.open('LOGO.png')
    #st.image(image, width=100)

color_type1 = {'EUR': '#7D297E','JPY': '#FAC92B','USD': '#ED8326'}
color_type2 = {'bunga': '#F35B04','pokok': '#3D348B'}

# Fungsi untuk membaca data
@st.cache_data 
def baca_data(x, y):
    data = pd.read_excel(x, sheet_name=y)
    return data

# Mengunggah file

file_path1 = "pages/Realisasi Bunga dan Pokok.xlsx"
file_path2 = "pages/Estimasi Efisiensi Konversi Pinjaman.xlsx"
# Fungsi baca data dari sheet
def baca_data(file_path, sheet_name):
    return pd.read_excel(file_path, sheet_name=sheet_name)


st.session_state.data_pokok = baca_data(file_path1, "Pokok")
st.session_state.data_bunga = baca_data(file_path1, "Bunga")
st.session_state.data_GI = baca_data(file_path1, "GI")
st.session_state.data_GI_ = baca_data(file_path1, "GI_")
    
# Tab Navigation
tab1, tab2 = st.tabs(["Realisasi Konversi", "Estimasi Efisiensi"])
with tab1 :
    data_GI_ = st.session_state.data_GI_
    data_GI_["Tahun"] = pd.to_datetime(data_GI_['Tanggal Konversi'], dayfirst=True).dt.year.astype(str)

    # Convert to string
    data_GI_["Loan-ID"]     = data_GI_["Loan-ID"].astype(str)
    data_GI_["Mata Uang Tujuan"]   = data_GI_["Mata Uang Tujuan"].astype(str)
    data_GI_["Keterangan"] = data_GI_["Keterangan"].astype(str)

    # ----- Urutan label -----
    curr_labels  = sorted(data_GI_["Mata Uang Tujuan"].unique())
    tahun_labels = sorted(data_GI_["Tahun"].unique()) 
    loan_labels  = sorted(data_GI_["Loan-ID"].unique())
    ket_labels   = sorted(data_GI_["Keterangan"].unique())

    ordered_labels = curr_labels + tahun_labels + loan_labels + ket_labels
    node_indices = {label: i for i, label in enumerate(ordered_labels)}

    # ----- Link generator -----
    def make_links(src_col, tgt_col):
        grouped = data_GI_.groupby([src_col, tgt_col]).size().reset_index(name="Value")
        grouped["source"] = grouped[src_col].map(node_indices)
        grouped["target"] = grouped[tgt_col].map(node_indices)
        return grouped[["source", "target", "Value"]]
   
    # Buat link sesuai urutan baru
    links_curr_tahun = make_links("Mata Uang Tujuan", "Tahun")
    links_tahun_loan = make_links("Tahun", "Loan-ID")
    links_loan_ket = make_links("Loan-ID", "Keterangan")

    # Gabungkan semua link
    all_links = pd.concat([links_curr_tahun, links_tahun_loan, links_loan_ket], ignore_index=True)
    # Buat mapping warna
    import seaborn as sns
    curr_palette = sns.color_palette("Set2", len(curr_labels)).as_hex()
    tahun_palette = sns.color_palette("Set1", len(tahun_labels)).as_hex()
    ket_palette = sns.color_palette("Pastel1", len(ket_labels)).as_hex()
    color_map = {}
    for i, curr in enumerate(curr_labels):
        color_map[curr] = curr_palette[i]
    for i, tahun in enumerate(tahun_labels):
        color_map[tahun] = tahun_palette[i]
    for i, ket in enumerate(ket_labels):
        color_map[ket] = ket_palette[i]
    for loan in loan_labels:
        color_map[loan] = "#d9d9d9"  # abu-abu muda

    # Warna alur berdasarkan target
    link_colors = [color_map.get(ordered_labels[target], "lightgray") for target in all_links["source"]]

    # Plot Sankey
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=1000,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=ordered_labels,
            color=[color_map.get(label, "lightgray") for label in ordered_labels]
        ),
        link=dict(
            source=all_links["source"],
            target=all_links["target"],
            value=all_links["Value"],
            color=link_colors
        )
    )])

    fig.update_layout(title_text="Realisasi Transaksi Konversi Pinjaman", font_size=12)

    # Tampilkan di Streamlit
    st.plotly_chart(fig, use_container_width=True)

    #------bar chart-----
    # ----- Data Manual -----
    st.session_state.data_chart = {
    "Tahun": ["2019-2022", "2024", "2025"],
    "EUR": [9, 9, 9],
    "JPY": [19, 12, 4],
    "IDR (from JPY)": [0, 7, 15],
    "IDR (from USD)": [0, 1, 12]
        }
    st.session_state.df_chart = pd.DataFrame(st.session_state.data_chart)

    # Transform ke long format
    st.session_state.df_long_chart = st.session_state.df_chart.melt(
        id_vars="Tahun", var_name="Sumber Mata Uang", value_name="Jumlah"
    )
    st.session_state.df_long_chart["Tahun"] = pd.Categorical(
        st.session_state.df_long_chart["Tahun"],
        categories=["2019-2022", "2024", "2025"],
        ordered=True
    )

    # Warna custom untuk legend
    color_map = {
        "EUR": "#4e79a7",             # Biru
        "JPY": "#f28e2b",             # Oranye
        "IDR (from JPY)": "#bab0ac", # Abu
        "IDR (from USD)": "#ffbe0b"  # Kuning
    }

    # Plot Bar Chart
    fig2 = px.bar(
        st.session_state.df_long_chart,
        x="Tahun",
        y="Jumlah",
        color="Sumber Mata Uang",
        text="Jumlah",
        color_discrete_map=color_map,
        title="Jumlah Loan Berdasarkan Mata Uang Tujuan Konversi"
    )

    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        xaxis=dict(type='category'), 
        yaxis=dict(title="Jumlah", range=[0, 50]),
        barmode="stack",
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title=None,
        yaxis_title="Jumlah",
        legend_title=None,
        font=dict(size=14)
    )
    fig2.update_traces(
        textposition="inside",
        insidetextanchor="start",
        textfont_color="black"
    )

    # Tampilkan chart
    st.plotly_chart(fig2)

with tab2:
    st.session_state.data_GI_ = baca_data(file_path1, "GI_")
    
    # AS OF
    st.session_state.as_of_ = baca_data(file_path1, "as_of")
    st.session_state.as_of_['Bulan'] = pd.to_datetime(st.session_state.as_of_['Bulan'], format='%d/%m/%Y %H:%M')
    st.session_state.as_of_['Bulan_'] = st.session_state.as_of_['Bulan'].dt.strftime('%b %y')
    
    default_index = len(st.session_state.as_of_['Bulan_']) - 1
    st.session_state.as_of__ = st.selectbox('As of:', st.session_state.as_of_['Bulan_'], index=default_index)
    
    selected_index = st.session_state.as_of_['Bulan_'].tolist().index(st.session_state.as_of__)
    st.session_state.as_of = st.session_state.as_of_['As_of'].iloc[selected_index]
    
    # Filter data GI berdasarkan tanggal konversi
    st.session_state.data_GI['Execution Date'] = pd.to_datetime(st.session_state.data_GI['Execution Date'])
    st.session_state.data_GI = st.session_state.data_GI[st.session_state.data_GI['Execution Date'] <= st.session_state.as_of]
    
    st.session_state.data_GI['Year'] = st.session_state.data_GI['Execution Date'].dt.year
    #st.session_state.data_GI["Bunga Konversi"] = st.session_state.data_GI["Bunga Konversi"] * 100
    st.session_state.data_GI['Loan-ID'] = st.session_state.data_GI['Loan-ID'].astype(str)
    st.session_state.loan_id       = st.session_state.data_GI['Loan-ID'].tolist()
    
    # Tampilkan expander dengan data historis
    with st.expander("ESTIMASI EFISIENSI"):
        # Simpan data rate dalam session_state jika belum ada
        
        # Simpan subset_data_pokok dalam session_state jika belum ada
        if "subset_data_pokok" not in st.session_state:
            st.session_state.subset_data_pokok = st.session_state.data_pokok.copy()
            st.session_state.subset_data_pokok['PAYMENT_DATE'] = pd.to_datetime(st.session_state.subset_data_pokok['PAYMENT_DATE'])
            st.session_state.subset_data_pokok = st.session_state.subset_data_pokok[st.session_state.subset_data_pokok['PAYMENT_DATE'] <= st.session_state.as_of]
            st.session_state.subset_data_pokok = st.session_state.subset_data_pokok.rename(columns={'AMT_IDR': 're_pokok'})

        if "subset_data_bunga" not in st.session_state:
            st.session_state.subset_data_bunga = st.session_state.data_bunga.copy() 
            st.session_state.subset_data_bunga['DATE_PAYMENT'] = pd.to_datetime(st.session_state.subset_data_bunga['DATE_PAYMENT'])
            st.session_state.subset_data_bunga = st.session_state.subset_data_bunga[st.session_state.subset_data_bunga['DATE_PAYMENT'] <= st.session_state.as_of]
            st.session_state.subset_data_bunga = st.session_state.subset_data_bunga.rename(columns={'AMT_IDR': 're_bunga'})

        # Summary by year
        st.session_state.subset_data_pokok_ = st.session_state.subset_data_pokok.groupby(['year', 'LOAN_ID', 'Kode'])['re_pokok'].sum().reset_index()
        st.session_state.subset_data_pokok_['LOAN_ID'] = st.session_state.subset_data_pokok_['LOAN_ID'].astype(str).str[:6]
        st.session_state.subset_data_bunga_ = st.session_state.subset_data_bunga.groupby(['year', 'LOAN_ID', 'Kode'])['re_bunga'].sum().reset_index()
        st.session_state.subset_data_bunga_['LOAN_ID'] = st.session_state.subset_data_bunga_['LOAN_ID'].astype(str).str[:6]
        
        st.session_state.subset_data_bunga_['Kode'] = st.session_state.subset_data_bunga_['Kode'].astype(str)
        st.session_state.subset_data_pokok_['Kode'] = st.session_state.subset_data_pokok_['Kode'].astype(str)
        st.session_state.merge_realisasi = pd.merge(st.session_state.subset_data_pokok_, st.session_state.subset_data_bunga_, on='Kode', how='outer')

        st.session_state.merge_realisasi['year_x'] = st.session_state.merge_realisasi['year_x'].fillna(st.session_state.merge_realisasi['year_y'])
        st.session_state.merge_realisasi['year_y'] = st.session_state.merge_realisasi['year_y'].fillna(st.session_state.merge_realisasi['year_x'])

        st.session_state.merge_realisasi['LOAN_ID_x'] = st.session_state.merge_realisasi['LOAN_ID_x'].fillna(st.session_state.merge_realisasi['LOAN_ID_y'])
        st.session_state.merge_realisasi['LOAN_ID_y'] = st.session_state.merge_realisasi['LOAN_ID_y'].fillna(st.session_state.merge_realisasi['LOAN_ID_x'])

        st.session_state.merge_realisasi['re_pokok'] = st.session_state.merge_realisasi['re_pokok'].fillna(0)
        st.session_state.merge_realisasi['re_bunga'] = st.session_state.merge_realisasi['re_bunga'].fillna(0)

        st.session_state.merge_realisasi = st.session_state.merge_realisasi.drop(columns=['year_y', "LOAN_ID_y"])
        st.session_state.merge_realisasi = st.session_state.merge_realisasi.rename(columns={'year_x': 'year', "LOAN_ID_x": 'LOAN_ID'})

        st.session_state.merged_re = st.session_state.merge_realisasi.copy()

        # Data estimasi
        st.session_state.merged_es = pd.DataFrame()
        for value in st.session_state.loan_id:
            sheet_name = f"{value}"
            data = pd.read_excel(file_path2, sheet_name=sheet_name)
            data['Date Schedule'] = pd.to_datetime(data['Date Schedule'])
            data['Year'] = data['Date Schedule'].dt.year
            data = data[data['Date Schedule'] <= st.session_state.as_of]
            data['Loan-ID']      = value
            grouped_data = data.groupby(['Year', 'Loan-ID']).agg({'Principal original (in IDR)': 'sum', 'Bunga LIBOR in IDR (est)': 'sum'}).reset_index()
            
            st.session_state.merged_es = pd.concat([st.session_state.merged_es, grouped_data], ignore_index=True)

        st.session_state.merged_es['Kode'] = st.session_state.merged_es['Loan-ID'].astype(str) + st.session_state.merged_es['Year'].astype(str)
        st.session_state.merged_es = st.session_state.merged_es.rename(columns={'Bunga LIBOR in IDR (est)': 'es_bunga', "Principal original (in IDR)": 'es_pokok'})
        
        # Merge semua data
        st.session_state.merged_es['Kode'] = st.session_state.merged_es['Kode'].astype(str)
        st.session_state.merged_re['Kode'] = st.session_state.merged_re['Kode'].astype(str)
 
        st.session_state.merge_all = pd.merge(st.session_state.merged_re, st.session_state.merged_es, on='Kode', how='outer')

        st.session_state.merge_all['year'] = st.session_state.merge_all['year'].fillna(st.session_state.merge_all['Year'])
        st.session_state.merge_all['Year'] = st.session_state.merge_all['Year'].fillna(st.session_state.merge_all['year'])
        st.session_state.merge_all['LOAN_ID'] = st.session_state.merge_all['LOAN_ID'].fillna(st.session_state.merge_all['Loan-ID'])
        st.session_state.merge_all['Loan-ID'] = st.session_state.merge_all['Loan-ID'].fillna(st.session_state.merge_all['LOAN_ID'])
        st.session_state.merge_all['re_pokok'] = st.session_state.merge_all['re_pokok'].fillna(0)
        st.session_state.merge_all['re_bunga'] = st.session_state.merge_all['re_bunga'].fillna(0)
        st.session_state.merge_all['es_pokok'] = st.session_state.merge_all['es_pokok'].fillna(0)
        st.session_state.merge_all['es_bunga'] = st.session_state.merge_all['es_bunga'].fillna(0)

        st.session_state.merge_all['saving_pokok'] = st.session_state.merge_all['es_pokok'] - st.session_state.merge_all['re_pokok']
        st.session_state.merge_all['saving_bunga'] = st.session_state.merge_all['es_bunga'] - st.session_state.merge_all['re_bunga']
        st.session_state.merge_all['Total_saving'] = (st.session_state.merge_all['es_pokok'] - st.session_state.merge_all['re_pokok']) + \
                                                    (st.session_state.merge_all['es_bunga'] - st.session_state.merge_all['re_bunga'])

        cols_merge_all = st.session_state.merge_all.columns
        cols_data_GI = st.session_state.data_GI.columns

        st.session_state.merge_all_ = pd.merge(st.session_state.merge_all, st.session_state.data_GI, on='Loan-ID', how='left')
        st.session_state.Total_saving = st.session_state.merge_all_['Total_saving'].sum() / 1_000_000_000_000

        # Perhitungan Saving
        st.session_state.tanggal_terakhir = pd.Timestamp(st.session_state.as_of).strftime('%b-%y')



        if "Total_saving" not in st.session_state:
            st.session_state.Total_saving = st.session_state.merge_all_['Total_saving'].sum() / 1_000_000_000_000  # Dalam triliun

        if "tanggal_terakhir" not in st.session_state:
            st.session_state.tanggal_terakhir = pd.Timestamp(st.session_state.as_of).strftime('%b-%y')
        
        
        st.metric(
            label=f"Total Efisiensi (as of {st.session_state.tanggal_terakhir})",
            value=f"Rp {st.session_state.Total_saving:,.2f} triliun"
        )

        col41, col42 = st.columns([2, 2])

        with col41:
            # Data berdasarkan kewajiban utang
            if "grouped_df_ef" not in st.session_state:
                ef_kewajiban = st.session_state.merge_all_[['LOAN_ID', 'saving_pokok', 'saving_bunga', 'year']]
                melted_df_ef = pd.melt(
                    ef_kewajiban, id_vars=['LOAN_ID', 'year'], value_vars=['saving_pokok', 'saving_bunga'],
                    var_name='Variable', value_name='Value'
                )
                melted_df_ef['Variable'] = melted_df_ef['Variable'].str.split('_').str[1]

                st.session_state.grouped_df_ef = melted_df_ef.groupby(['year', 'Variable'], as_index=False)['Value'].sum()
                st.session_state.grouped_df_ef1 = melted_df_ef.groupby(['Variable'], as_index=False)['Value'].sum()

            fig412 = px.bar(
                st.session_state.grouped_df_ef1, x='Variable', y='Value', color='Variable',
                color_discrete_map=color_type2, barmode='group',
                labels={'Value': 'Estimasi Efisiensi', 'Variable': 'Jenis Kewajiban'},
                title='Efisiensi Berdasarkan Pembayaran Kewajiban Utang'
            )
            st.plotly_chart(fig412, theme="streamlit", use_container_width=True)

            fig411 = px.bar(
                st.session_state.grouped_df_ef, x='year', y='Value', color='Variable',
                color_discrete_map=color_type2, barmode='group',
                labels={'Value': 'Estimasi Efisiensi', 'Variable': 'Jenis Kewajiban'},
                title='Breakdown by Year'
            )
            st.plotly_chart(fig411, theme="streamlit", use_container_width=True)

        with col42:
            # Data berdasarkan mata uang
            if "grouped_df_ef_curr" not in st.session_state:
                ef_curr = st.session_state.merge_all_[['LOAN_ID', "Total_saving", "year", 'Mata Uang Tujuan']]
                st.session_state.grouped_df_ef_curr = ef_curr.groupby(['year', 'Mata Uang Tujuan'], as_index=False)['Total_saving'].sum()
                st.session_state.grouped_df_ef_curr1 = ef_curr.groupby(['Mata Uang Tujuan'], as_index=False)['Total_saving'].sum()

            fig421 = px.bar(
                st.session_state.grouped_df_ef_curr1, x='Mata Uang Tujuan', y='Total_saving', color='Mata Uang Tujuan',
                color_discrete_map=color_type1, barmode='group',
                labels={'Total_saving': 'Estimasi Efisiensi', 'Mata Uang Tujuan': 'Mata Uang Tujuan'},
                title='Efisiensi Berdasarkan Mata Uang Tujuan'
            )
            st.plotly_chart(fig421, theme="streamlit", use_container_width=True)

            fig422 = px.bar(
                st.session_state.grouped_df_ef_curr, x='year', y='Total_saving', color='Mata Uang Tujuan',
                color_discrete_map=color_type1, barmode='group',
                labels={'Total_saving': 'Estimasi Efisiensi', 'Mata Uang Tujuan': 'Mata Uang Tujuan'},
                title='Breakdown by Year'
            )
            st.plotly_chart(fig422, theme="streamlit", use_container_width=True)

        # Data berdasarkan Loan ID
        #st.write(st.session_state.merge_all_)
        ef_loanid = st.session_state.merge_all_[['Kode Pinjaman', "Total_saving", "year", 'Mata Uang Tujuan']]
        ef_loanid['Kode Pinjaman'] = ef_loanid['Kode Pinjaman'].astype(str)

        ef_loanid_ = ef_loanid.groupby(['Kode Pinjaman', 'Mata Uang Tujuan'], as_index=False)['Total_saving'].sum()
        st.session_state.ef_loanid_sorted = ef_loanid_.sort_values(by='Total_saving', ascending=False)


        fig43 = px.bar(st.session_state.ef_loanid_sorted, x='Kode Pinjaman', y='Total_saving', color='Mata Uang Tujuan',
            color_discrete_map=color_type1, title='Estimasi Efisiensi by Loan ID'
        )
        st.plotly_chart(fig43, theme="streamlit", use_container_width=True)

    if st.button('Simpan Report'):
        nama = st.session_state.tanggal_terakhir
        tipe = '.xlsx'
        namafile = nama + tipe
        
        with pd.ExcelWriter(namafile) as writer:  # Ubah nama excel
            st.session_state.merge_all_.to_excel(writer, sheet_name='Data ALL')
            st.session_state.grouped_df_ef1.to_excel(writer, sheet_name='by jenis')
            st.session_state.grouped_df_ef.to_excel(writer, sheet_name='by jenis by year')
            st.session_state.grouped_df_ef_curr1.to_excel(writer, sheet_name='by curr')
            st.session_state.grouped_df_ef_curr.to_excel(writer, sheet_name='by curr by year')
            st.session_state.ef_loanid_sorted.to_excel(writer, sheet_name='by loan')
            st.session_state.data_rekap.to_excel(writer, sheet_name='Rekap Loan Konversi')
        
        st.success(f'Report berhasil disimpan: {namafile}')

    

