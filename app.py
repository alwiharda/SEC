import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==============================
# 1. LOAD DATA
# ==============================
df_aktual = pd.read_excel("prediksi permintaan (3).xlsx")
df_forecast = pd.read_excel("Forecast_2024_2028_Detail_PerKomoditas.xlsx")

# Samakan nama kolom
df_aktual.rename(columns={
    "Produksi": "produksi",
    "Konsumsi (ton)": "konsumsi"
}, inplace=True)

df_forecast.rename(columns={
    "Produksi": "produksi",
    "Konsumsi (ton)": "konsumsi"
}, inplace=True)

# Gabungkan data aktual dan forecast
df_all = pd.concat([df_aktual, df_forecast], ignore_index=True)

# Hitung surplus
df_all["surplus"] = df_all["produksi"] - df_all["konsumsi"]

# ==============================
# 2. CSS STYLING
# ==============================
st.markdown(
    """
    <style>
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #f9f9f9, #eef6f9);
        color: #333333;
        font-family: "Arial", sans-serif;
    }

    /* Title */
    h1 {
        color: #2C3E50;
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        margin-bottom: 20px;
    }

    /* Subheader */
    h2, h3 {
        color: #34495E;
        margin-top: 30px;
    }

    /* Dataframe styling */
    .dataframe {
        border-radius: 10px;
        border: 1px solid #ddd;
    }

    /* Dropdown & widgets */
    div[data-baseweb="select"] {
        border-radius: 10px;
        border: 1px solid #aaa;
    }

    /* Info box */
    .stAlert {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# 3. STREAMLIT UI
# ==============================
st.title("📊 Prediksi Produksi, Konsumsi, dan Surplus Komoditas Pangan")

# Dropdown pilihan
provinsi = st.selectbox("🏙️ Pilih Provinsi", df_all["Provinsi"].unique())
komoditas = st.selectbox("🌾 Pilih Komoditas", df_all["Komoditas"].unique())

# Filter provinsi + komoditas
df_selected = df_all[(df_all["Provinsi"] == provinsi) & (df_all["Komoditas"] == komoditas)]

# Dropdown tahun (ditambah opsi 'Semua Tahun')
tahun_opsi = ["Semua Tahun"] + sorted(df_selected["Tahun"].unique().tolist())
tahun = st.selectbox("📅 Pilih Tahun", tahun_opsi)

if tahun != "Semua Tahun":
    df_selected = df_selected[df_selected["Tahun"] == tahun]

# ==============================
# 4. DATA TABEL
# ==============================
st.subheader(f"📋 Data Aktual + Prediksi {komoditas} ({provinsi})")
st.dataframe(df_selected[["Tahun", "produksi", "konsumsi", "surplus"]])

# ==============================
# 5. VISUALISASI
# ==============================
if tahun == "Semua Tahun":
    # Plot 1: Produksi, Konsumsi, Surplus (provinsi terpilih)
    st.subheader("📈 Tren Produksi, Konsumsi, dan Surplus (2018–2028)")

    fig1, ax1 = plt.subplots(figsize=(8,5))
    ax1.plot(df_selected["Tahun"], df_selected["produksi"], marker="o", label="Produksi", color="#3498DB")
    ax1.plot(df_selected["Tahun"], df_selected["konsumsi"], marker="o", label="Konsumsi", color="#E74C3C")
    ax1.plot(df_selected["Tahun"], df_selected["surplus"], marker="o", label="Surplus", color="#2ECC71")
    ax1.legend()
    ax1.set_xlabel("Tahun")
    ax1.set_ylabel("Ton")
    ax1.set_title(f"Produksi, Konsumsi, dan Surplus {komoditas} - {provinsi}")
    st.pyplot(fig1)

    # Plot 2: Perbandingan semua provinsi
    st.subheader("🌍 Perbandingan Antar Provinsi (2018–2028)")

    df_compare = df_all[df_all["Komoditas"] == komoditas]

    fig2, ax2 = plt.subplots(figsize=(10,6))
    for prov in df_compare["Provinsi"].unique():
        dprov = df_compare[df_compare["Provinsi"] == prov]
        ax2.plot(dprov["Tahun"], dprov["produksi"], label=f"{prov}", linewidth=2)

    ax2.set_xlabel("Tahun")
    ax2.set_ylabel("Produksi (Ton)")
    ax2.set_title(f"Perbandingan Produksi {komoditas} Antar Provinsi (2018–2028)")
    ax2.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    st.pyplot(fig2)
else:
    st.info("📌 Grafik hanya muncul jika memilih 'Semua Tahun'")
