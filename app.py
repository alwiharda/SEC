# ============================================================
# app.py – Web Prediksi Surplus / Defisit Provinsi
# ============================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re

# ---------- 1. LOAD DATA ----------
FILE_HIST = "prediksi permintaan (3).xlsx"
FILE_FORE = "forecast_5th_beras.xlsx"

# Data historis (2018–2023)
df_hist = pd.read_excel(FILE_HIST)
df_hist.columns = df_hist.columns.str.strip()

df_hist = df_hist.rename(columns={
    "produksi": "Produksi",
    "konsumsi (ton)": "Konsumsi"
})
df_hist["Tahun"] = df_hist["Tahun"].astype(int)

# Data forecast (2024–2028, format wide)
df_fore = pd.read_excel(FILE_FORE)
df_fore.columns = df_fore.columns.str.strip()

# Ubah wide ke long pakai melt manual
value_vars = [c for c in df_fore.columns if "_" in c]  # hanya kolom prediksi
df_long = df_fore.melt(
    id_vars=["Provinsi", "Komoditas"],
    value_vars=value_vars,
    var_name="Variable",
    value_name="Value"
)

# Ekstrak Tahun & Jenis (Produksi/Konsumsi/Surplus/Status)
df_long["Tahun"] = df_long["Variable"].apply(lambda x: int(re.findall(r"\d+", x)[0]))
df_long["Jenis"] = df_long["Variable"].apply(lambda x: re.sub(r"_\d+", "", x))
df_long = df_long.drop(columns=["Variable"])

# Pivot kembali supaya bentuknya rapi
df_long = df_long.pivot_table(
    index=["Provinsi", "Komoditas", "Tahun"],
    columns="Jenis",
    values="Value",
    aggfunc="first"
).reset_index()

# Gabungkan historis + forecast
df = pd.concat(
    [
        df_hist[["Provinsi", "Komoditas", "Tahun", "Produksi", "Konsumsi"]],
        df_long
    ],
    ignore_index=True
)

# Hitung surplus & status bila kosong
if "Surplus" not in df.columns:
    df["Surplus"] = df["Produksi"] - df["Konsumsi"]
else:
    df["Surplus"] = df["Surplus"].fillna(df["Produksi"] - df["Konsumsi"])

if "Status" not in df.columns:
    df["Status"] = df["Surplus"].apply(lambda x: "Surplus" if x > 0 else "Defisit")
else:
    df["Status"] = df["Status"].fillna(df["Surplus"].apply(lambda x: "Surplus" if x > 0 else "Defisit"))

df["Tahun"] = df["Tahun"].astype(int)

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
        - **Status**: {"🟢 Surplus" if status_val=="Surplus" else "🔴 Defisit"}
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
st.caption("Dibuat untuk prediksi pangan Indonesia 2018–2028 menggunakan data historis dan proyeksi forecast.")
