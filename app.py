import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Prediksi Konsumsi & Produksi", layout="wide")

# CSS langsung ditulis di sini
st.markdown("""
<style>
/* Tampilan soft pastel */
body {
    background-color: #f9fafc;
    font-family: "Segoe UI", sans-serif;
    color: #333;
}

h1, h2, h3 {
    color: #4C72B0;
}

.stButton>button {
    background-color: #A7C7E7;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 8px 16px;
}

.stButton>button:hover {
    background-color: #7AAAE1;
}
</style>
""", unsafe_allow_html=True)

# Judul
st.title("📊 Prediksi Konsumsi & Produksi Pangan")

# Load data
df = pd.read_excel("prediksi_permintaan.xlsx")

# Pilih provinsi
provinsi = st.selectbox("Pilih Provinsi", df["Provinsi"].unique())
df_prov = df[df["Provinsi"] == provinsi]

# Plot grafik surplus
fig, ax = plt.subplots(figsize=(10,5))
ax.plot(df_prov["Tahun"], df_prov["Surplus"], marker="o", color="#4C72B0", linewidth=2)
ax.set_title(f"Prediksi Surplus {provinsi} (2018-2028)", fontsize=14)
ax.set_ylabel("Surplus (Ton)")
ax.set_xlabel("Tahun")
ax.grid(True, linestyle="--", alpha=0.6)

st.pyplot(fig)

st.info("🔍 Pilih provinsi di dropdown untuk melihat prediksi surplus.")
