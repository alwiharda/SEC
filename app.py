import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# 1. Load Data
# =====================================================
@st.cache_data
def load_data():
    # Data forecast 2024–2028
    df_forecast = pd.read_excel("Forecast_2024_2028_Detail_PerKomoditas.xlsx")
    return df_forecast

df = load_data()

# =====================================================
# 2. Sidebar
# =====================================================
st.set_page_config(page_title="Dashboard Prediksi Pangan", layout="wide")

st.markdown(
    """
    <style>
    .main {
        background-color: #f9f9f9;
    }
    .stSidebar {
        background-color: #2c3e50;
    }
    h1 {
        color: #2c3e50;
        text-align: center;
    }
    .stSelectbox label, .stRadio label {
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Dashboard Prediksi Produksi & Konsumsi Pangan (2024–2028)")

# Dropdown filter
provinsi = st.sidebar.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.sidebar.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

# Tambahkan opsi "Semua Tahun"
tahun_options = ["Semua Tahun"] + sorted(df["Tahun"].unique().astype(str).tolist())
tahun = st.sidebar.selectbox("Pilih Tahun", tahun_options)

# =====================================================
# 3. Filter Data
# =====================================================
df_filtered = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)]

if tahun != "Semua Tahun":
    df_filtered = df_filtered[df_filtered["Tahun"] == int(tahun)]

# =====================================================
# 4. Visualisasi
# =====================================================
st.subheader(f"📍 Data {komoditas} di {provinsi}")

col1, col2 = st.columns(2)

with col1:
    fig1 = px.bar(
        df_filtered,
        x="Tahun",
        y=["produksi", "konsumsi (ton)"],
        barmode="group",
        title="Produksi vs Konsumsi",
        labels={"value": "Jumlah (ton)", "Tahun": "Tahun"}
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.line(
        df_filtered,
        x="Tahun",
        y="Stok",
        title="Stok (Surplus/Defisit)",
        markers=True
    )
    st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# 5. Tabel Data
# =====================================================
st.subheader("📋 Tabel Data")
st.dataframe(
    df_filtered[["Tahun", "produksi", "konsumsi (ton)", "Stok", "Status"]],
    use_container_width=True
)
