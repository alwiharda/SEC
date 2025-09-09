import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# CONFIGURASI HALAMAN
# ==============================
st.set_page_config(page_title="Dashboard Prediksi Komoditas", layout="wide")

# ==============================
# CSS AGAR TAMPILAN MENARIK
# ==============================
st.markdown("""
    <style>
    body {
        background-color: #f9fafc;
    }
    .main {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stSelectbox, .stMultiSelect {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# LOAD DATA
# ==============================
df_aktual = pd.read_excel("prediksi permintaan (3).xlsx")
df_forecast = pd.read_excel("Forecast_2024_2028_Detail_PerKomoditas.xlsx")

# Ambil kolom penting saja agar konsisten
df_aktual = df_aktual[["Provinsi", "Tahun", "Komoditas", "produksi", "konsumsi (ton)"]]
df_forecast = df_forecast[["Provinsi", "Tahun", "Komoditas", "produksi", "konsumsi (ton)"]]

# Gabungkan
df_all = pd.concat([df_aktual, df_forecast], ignore_index=True)

# Hitung surplus
df_all["surplus"] = df_all["produksi"] - df_all["konsumsi (ton)"]

# ==============================
# SIDEBAR FILTER
# ==============================
st.sidebar.header("Filter Data")

provinsi_list = df_all["Provinsi"].unique().tolist()
komoditas_list = df_all["Komoditas"].unique().tolist()
tahun_list = sorted(df_all["Tahun"].unique().tolist())

provinsi = st.sidebar.selectbox("Pilih Provinsi", provinsi_list)
komoditas = st.sidebar.selectbox("Pilih Komoditas", komoditas_list)
tahun = st.sidebar.multiselect("Pilih Tahun", tahun_list, default=tahun_list)

# ==============================
# FILTER DATA SESUAI INPUT
# ==============================
df_filtered = df_all[
    (df_all["Provinsi"] == provinsi) &
    (df_all["Komoditas"] == komoditas) &
    (df_all["Tahun"].isin(tahun))
]

# ==============================
# TAMPILKAN DATA
# ==============================
st.title("📊 Dashboard Prediksi Komoditas")
st.subheader(f"Provinsi: {provinsi} | Komoditas: {komoditas}")

st.dataframe(df_filtered, use_container_width=True)

# ==============================
# VISUALISASI 1: Per Provinsi
# ==============================
st.markdown("### Tren Produksi, Konsumsi, dan Surplus (2018–2028)")

fig, ax = plt.subplots(figsize=(10,5))
ax.plot(df_filtered["Tahun"], df_filtered["produksi"], marker="o", label="Produksi")
ax.plot(df_filtered["Tahun"], df_filtered["konsumsi (ton)"], marker="o", label="Konsumsi")
ax.plot(df_filtered["Tahun"], df_filtered["surplus"], marker="o", label="Surplus")

ax.set_title(f"Tren {komoditas} di {provinsi}", fontsize=14)
ax.set_ylabel("Jumlah (ton)")
ax.legend()
st.pyplot(fig)

# ==============================
# VISUALISASI 2: Gabungan Semua Provinsi
# ==============================
st.markdown("### Perbandingan Antar Provinsi (2018–2028)")

df_compare = df_all[
    (df_all["Komoditas"] == komoditas) &
    (df_all["Tahun"].isin(tahun))
]

fig2, ax2 = plt.subplots(figsize=(12,6))
for prov in df_compare["Provinsi"].unique():
    df_temp = df_compare[df_compare["Provinsi"] == prov]
    ax2.plot(df_temp["Tahun"], df_temp["produksi"], marker="o", label=prov)

ax2.set_title(f"Perbandingan Produksi {komoditas} Antar Provinsi", fontsize=14)
ax2.set_ylabel("Jumlah (ton)")
ax2.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
st.pyplot(fig2)
