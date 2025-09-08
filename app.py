# ============================================================
# app.py – Web Prediksi Surplus / Defisit Provinsi
# ============================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------- 1. LOAD DATA ----------
FILE_HIST = "prediksi permintaan (3).xlsx"
FILE_FORE = "forecast_5th_beras.xlsx"

# Data historis (sampai 2023)
df_hist = pd.read_excel(FILE_HIST)
df_hist.columns = df_hist.columns.str.strip()

# Samakan nama kolom supaya konsisten
df_hist = df_hist.rename(columns={
    "produksi": "Produksi",
    "konsumsi (ton)": "Konsumsi"
})
df_hist["Tahun"] = df_hist["Tahun"].astype(int)

# Data prediksi (2024–2028)
df_fore = pd.read_excel(FILE_FORE)
df_fore.columns = df_fore.columns.str.strip()

# Pastikan ada kolom "Produksi" dan "Konsumsi"
for col in ["Produksi", "Konsumsi"]:
    if col not in df_fore.columns:
        if "produksi" in df_fore.columns:
            df_fore = df_fore.rename(columns={"produksi": "Produksi"})
        if "konsumsi (ton)" in df_fore.columns:
            df_fore = df_fore.rename(columns={"konsumsi (ton)": "Konsumsi"})

df_fore["Tahun"] = df_fore["Tahun"].astype(int)

# Gabungkan historis + prediksi
df = pd.concat([df_hist, df_fore], ignore_index=True)

# Hitung Surplus
df["Surplus"] = df["Produksi"] - df["Konsumsi"]
df["Status"] = df["Surplus"].apply(lambda x: "Surplus" if x > 0 else "Defisit")

# ---------- 2. STREAMLIT UI ----------
st.set_page_config(page_title="Prediksi Surplus/Defisit", layout="wide")

st.title("📊 Prediksi Surplus / Defisit Pangan 2018–2028")

col1, col2, col3 = st.columns(3)
with col1:
    provinsi = st.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
with col2:
    komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))
with col3:
    tahun = st.selectbox("Pilih Tahun", sorted(df["Tahun"].unique()))

# Filter data sesuai pilihan
df_prov = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)]

# ---------- 3. TAMPILKAN DATA ----------
st.subheader(f"Data {provinsi} – {komoditas}")
st.dataframe(df_prov[["Tahun", "Produksi", "Konsumsi", "Surplus", "Status"]])

# Ambil data tahun terpilih
row_selected = df_prov[df_prov["Tahun"] == tahun]
if not row_selected.empty:
    surplus_val = row_selected["Surplus"].values[0]
    status_val = row_selected["Status"].values[0]

    st.markdown(
        f"""
        ### 📌 Hasil Prediksi {tahun}
        - **Produksi**: {row_selected['Produksi'].values[0]:,.0f} ton  
        - **Konsumsi**: {row_selected['Konsumsi'].values[0]:,.0f} ton  
        - **Surplus**: {surplus_val:,.0f} ton  
        - **Status**: 🟢 **{status_val}** jika Surplus, 🔴 **{status_val}** jika Defisit
        """
    )

# ---------- 4. VISUALISASI ----------
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df_prov["Tahun"], df_prov["Produksi"], marker="o", label="Produksi", color="#1f77b4")
ax.plot(df_prov["Tahun"], df_prov["Konsumsi"], marker="s", label="Konsumsi", color="#ff7f0e")
ax.bar(df_prov["Tahun"], df_prov["Surplus"], alpha=0.3, label="Surplus")

ax.set_title(f"Tren Produksi, Konsumsi, dan Surplus – {provinsi} ({komoditas})", fontsize=14)
ax.set_xlabel("Tahun")
ax.set_ylabel("Ton")
ax.legend()
ax.grid(alpha=0.3)

st.pyplot(fig)

# ---------- 5. FOOTER ----------
st.markdown("---")
st.caption("Dibuat untuk prediksi pangan Indonesia 2018–2028 menggunakan XGBoost + data historis dan proyeksi.")
