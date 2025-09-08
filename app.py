import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ============================
# 1. SETTING PAGE
# ============================
st.set_page_config(
    page_title="Prediksi Surplus Pangan",
    page_icon="🌾",
    layout="wide"
)

# ============================
# 2. CSS SOFT STYLE
# ============================
st.markdown("""
<style>
body {
    background-color: #f9f9f9;
    font-family: 'Arial', sans-serif;
}
h1, h2, h3 {
    color: #2c3e50;
}
.stSelectbox, .stButton>button {
    border-radius: 10px;
}
.reportview-container {
    background: #f9f9f9;
}
</style>
""", unsafe_allow_html=True)

# ============================
# 3. LOAD DATA
# ============================
FILE = "prediksi_permintaan.xlsx"
try:
    df = pd.read_excel(FILE)
except FileNotFoundError:
    st.error(f"❌ File `{FILE}` tidak ditemukan. Pastikan sudah diunggah.")
    st.stop()

# ============================
# 4. INPUT USER
# ============================
st.title("🌾 Prediksi Surplus Pangan per Provinsi")
st.write("Visualisasi hasil forecast konsumsi vs produksi untuk menentukan surplus/defisit pangan.")

provinsi = st.selectbox("Pilih Provinsi", df["Provinsi"].unique())

# filter data sesuai provinsi
df_prov = df[df["Provinsi"] == provinsi].copy()

# hitung surplus jika belum ada
if "Surplus" not in df_prov.columns:
    if "Produksi" in df_prov.columns and "Konsumsi" in df_prov.columns:
        df_prov["Surplus"] = df_prov["Produksi"] - df_prov["Konsumsi"]
    else:
        st.error("❌ Data tidak punya kolom Produksi/Konsumsi untuk hitung surplus.")
        st.stop()

# ============================
# 5. PLOT GRAFIK
# ============================
fig, ax = plt.subplots(figsize=(10,5))
ax.plot(df_prov["Tahun"], df_prov["Surplus"], marker="o", color="#4C72B0", linewidth=2)
ax.axhline(0, color="red", linestyle="--", linewidth=1, alpha=0.7)

ax.set_title(f"Prediksi Surplus {provinsi} (2018-2028)", fontsize=14)
ax.set_ylabel("Surplus (Ton)")
ax.set_xlabel("Tahun")
ax.grid(True, linestyle="--", alpha=0.6)

st.pyplot(fig)

# ============================
# 6. DATAFRAME OUTPUT
# ============================
st.subheader("📊 Data Prediksi")
st.dataframe(df_prov.reset_index(drop=True))
