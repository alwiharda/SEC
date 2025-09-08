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
.dataframe {
    background: white;
}
.surplus {
    color: green;
    font-weight: bold;
    font-size: 20px;
}
.defisit {
    color: red;
    font-weight: bold;
    font-size: 20px;
}
</style>
""", unsafe_allow_html=True)

# ============================
# 3. LOAD DATA
# ============================
FILE = "prediksi permintaan (3).xlsx"
try:
    df = pd.read_excel(FILE)
except FileNotFoundError:
    st.error(f"❌ File `{FILE}` tidak ditemukan. Pastikan sudah diunggah ke folder yang sama dengan app.py.")
    st.stop()

# pastikan kolom benar
if "produksi" not in df.columns or "konsumsi (ton)" not in df.columns:
    st.error("❌ Data tidak punya kolom 'produksi' atau 'konsumsi (ton)'.")
    st.stop()

# hitung surplus
df["Surplus"] = df["produksi"] - df["konsumsi (ton)"]

# ============================
# 4. INPUT USER
# ============================
st.title("🌾 Prediksi Surplus/Defisit Pangan")

provinsi = st.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))
tahun = st.selectbox("Pilih Tahun", sorted(df["Tahun"].unique()))

# filter data sesuai input
df_filtered = df[(df["Provinsi"] == provinsi) & 
                 (df["Komoditas"] == komoditas)].copy()

# ambil data tahun spesifik
row = df_filtered[df_filtered["Tahun"] == tahun]

if not row.empty:
    produksi = row["produksi"].values[0]
    konsumsi = row["konsumsi (ton)"].values[0]
    surplus = row["Surplus"].values[0]

    st.subheader("📊 Hasil Prediksi")
    st.write(f"**Provinsi:** {provinsi}")
    st.write(f"**Komoditas:** {komoditas}")
    st.write(f"**Tahun:** {tahun}")
    st.write(f"Produksi: **{produksi:,.0f} ton**")
    st.write(f"Konsumsi: **{konsumsi:,.0f} ton**")

    if surplus >= 0:
        st.markdown(f"<p class='surplus'>✅ Surplus {surplus:,.0f} ton</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<p class='defisit'>❌ Defisit {abs(surplus):,.0f} ton</p>", unsafe_allow_html=True)
else:
    st.warning("⚠️ Data untuk tahun ini tidak tersedia.")

# ============================
# 5. PLOT GRAFIK
# ============================
if not df_filtered.empty:
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(df_filtered["Tahun"], df_filtered["Surplus"], marker="o", color="#4C72B0", linewidth=2)
    ax.axhline(0, color="red", linestyle="--", linewidth=1, alpha=0.7)

    ax.set_title(f"Tren Surplus {komoditas} - {provinsi} (2018-2028)", fontsize=14)
    ax.set_ylabel("Surplus (Ton)")
    ax.set_xlabel("Tahun")
    ax.grid(True, linestyle="--", alpha=0.6)

    st.pyplot(fig)

# ============================
# 6. TAMPILKAN DATAFRAME
# ============================
st.subheader("📑 Data Lengkap")
st.dataframe(df_filtered.reset_index(drop=True))
