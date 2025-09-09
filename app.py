import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =========================================================
# 1. Konfigurasi Awal
# =========================================================
st.set_page_config(page_title="Dashboard Prediksi Pangan", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #f8f9fa;
        }
        .title {
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }
        .sidebar .sidebar-content {
            background-color: #e9ecef;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="title">📊 Dashboard Prediksi Produksi & Konsumsi Pangan (2018–2028)</p>', unsafe_allow_html=True)

# =========================================================
# 2. Load Data
# =========================================================
@st.cache_data
def load_data():
    # Data historis 2018–2023
    df_hist = pd.read_excel("prediksi permintaan (3).xlsx")
    df_hist.rename(columns={"Produksi": "produksi", "Konsumsi": "konsumsi (ton)"}, inplace=True)

    # Data prediksi 2024–2028
    df_forecast = pd.read_excel("Forecast_2024_2028_Detail_PerKomoditas.xlsx")

    # Samakan kolom
    df_hist["Stok"] = df_hist["produksi"] - df_hist["konsumsi (ton)"]
    df_hist["Status"] = df_hist["Stok"].apply(lambda x: "Surplus" if x >= 0 else "Defisit")

    df_all = pd.concat([df_hist[["Provinsi", "Tahun", "Komoditas", "produksi", "konsumsi (ton)", "Stok", "Status"]],
                        df_forecast[["Provinsi", "Tahun", "Komoditas", "produksi", "konsumsi (ton)", "Stok", "Status"]]],
                       ignore_index=True)
    return df_all

df = load_data()

# =========================================================
# 3. Sidebar Filter
# =========================================================
provinsi = st.sidebar.selectbox("📍 Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.sidebar.selectbox("🌾 Pilih Komoditas", sorted(df["Komoditas"].unique()))
tahun_options = ["Semua Tahun"] + sorted(df["Tahun"].unique().astype(str).tolist())
tahun = st.sidebar.selectbox("📅 Pilih Tahun", tahun_options)

df_filtered = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)]
if tahun != "Semua Tahun":
    df_filtered = df_filtered[df_filtered["Tahun"] == int(tahun)]

# =========================================================
# 4. Visualisasi
# =========================================================
st.subheader(f"📍 Data {komoditas} di {provinsi}")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots()
    ax.plot(df_filtered["Tahun"], df_filtered["produksi"], marker="o", label="Produksi")
    ax.plot(df_filtered["Tahun"], df_filtered["konsumsi (ton)"], marker="s", label="Konsumsi")
    ax.set_ylabel("Jumlah (ton)")
    ax.set_title("Produksi vs Konsumsi")
    ax.legend()
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots()
    ax.bar(df_filtered["Tahun"], df_filtered["Stok"], color=["green" if s == "Surplus" else "red" for s in df_filtered["Status"]])
    ax.axhline(0, color="black", linestyle="--")
    ax.set_ylabel("Stok")
    ax.set_title("Stok (Surplus/Defisit)")
    st.pyplot(fig)

# =========================================================
# 5. Plot Gabungan Semua Provinsi
# =========================================================
st.subheader(f"📊 Tren Produksi dan Konsumsi {komoditas} di Semua Provinsi")

df_komoditas = df[df["Komoditas"] == komoditas].groupby("Tahun").agg({"produksi": "sum", "konsumsi (ton)": "sum"}).reset_index()

fig, ax = plt.subplots()
ax.plot(df_komoditas["Tahun"], df_komoditas["produksi"], marker="o", label="Total Produksi")
ax.plot(df_komoditas["Tahun"], df_komoditas["konsumsi (ton)"], marker="s", label="Total Konsumsi")
ax.set_ylabel("Jumlah (ton)")
ax.set_title(f"Total Produksi vs Konsumsi {komoditas} (Semua Provinsi)")
ax.legend()
st.pyplot(fig)

# =========================================================
# 6. Tabel Data
# =========================================================
st.subheader("📋 Tabel Data")
st.dataframe(df_filtered[["Tahun", "produksi", "konsumsi (ton)", "Stok", "Status"]], use_container_width=True)
