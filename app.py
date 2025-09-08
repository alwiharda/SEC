import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =============================
# 1. LOAD DATA
# =============================
FILE_HIST = "prediksi permintaan (3).xlsx"
FILE_FORE = "forecast_5th_beras.xlsx"

@st.cache_data
def load_data():
    df_hist = pd.read_excel(FILE_HIST)
    df_fore = pd.read_excel(FILE_FORE)

    # pastikan kolom konsisten
    df_hist = df_hist.rename(columns={"Produksi (Ton)": "Produksi",
                                      "Konsumsi (Ton)": "Konsumsi"})
    if "Surplus" not in df_hist.columns:
        df_hist["Surplus"] = df_hist["Produksi"] - df_hist["Konsumsi"]

    if "Surplus" not in df_fore.columns and "Produksi" in df_fore.columns and "Konsumsi" in df_fore.columns:
        df_fore["Surplus"] = df_fore["Produksi"] - df_fore["Konsumsi"]

    # gabungkan historis (≤2023) + prediksi (≥2024)
    df = pd.concat([df_hist[df_hist["Tahun"] <= 2023], df_fore[df_fore["Tahun"] >= 2024]], ignore_index=True)

    # filter hanya 2018–2028
    df = df[df["Tahun"].between(2018, 2028)]
    return df

df = load_data()

# =============================
# 2. SIDEBAR FILTER
# =============================
st.sidebar.header("🔎 Filter Data")
provinsi = st.sidebar.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.sidebar.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))
tahun = st.sidebar.selectbox("Pilih Tahun", list(range(2018, 2029)))  # 2018–2028

# Filter data sesuai pilihan
df_filtered = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)]

# =============================
# 3. TAMPILKAN DATA TAHUN TERTENTU
# =============================
st.title("📊 Prediksi Surplus / Defisit Pangan Indonesia (2018–2028)")
st.markdown(f"### Provinsi: **{provinsi}**, Komoditas: **{komoditas}**")

row = df_filtered[df_filtered["Tahun"] == tahun]
if not row.empty:
    produksi_val = float(row["Produksi"].values[0])
    konsumsi_val = float(row["Konsumsi"].values[0])
    surplus_val = produksi_val - konsumsi_val
    status = "✅ Surplus" if surplus_val > 0 else "❌ Defisit"

    st.subheader(f"Hasil Tahun {tahun}")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Produksi", value=f"{produksi_val:,.0f} ton")
    col2.metric(label="Konsumsi", value=f"{konsumsi_val:,.0f} ton")
    col3.metric(label="Surplus / Defisit", value=f"{surplus_val:,.0f} ton", delta=status)

# =============================
# 4. VISUALISASI TREND 2018–2028
# =============================
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df_filtered["Tahun"], df_filtered["Produksi"], marker="s", color="#55A868", label="Produksi")
ax.plot(df_filtered["Tahun"], df_filtered["Konsumsi"], marker="o", color="#C44E52", label="Konsumsi")
ax.fill_between(df_filtered["Tahun"], df_filtered["Surplus"], 0,
                where=(df_filtered["Surplus"] >= 0), color="green", alpha=0.2, label="Surplus")
ax.fill_between(df_filtered["Tahun"], df_filtered["Surplus"], 0,
                where=(df_filtered["Surplus"] < 0), color="red", alpha=0.2, label="Defisit")

ax.axhline(0, color="black", linewidth=1, linestyle="--")
ax.axvspan(2024, 2028, color="gray", alpha=0.2, label="Forecast 2024–2028")

ax.set_title(f"Produksi vs Konsumsi & Surplus {komoditas} — {provinsi} (2018–2028)", fontsize=14)
ax.set_xlabel("Tahun")
ax.set_ylabel("Ton")
ax.legend()

st.pyplot(fig)

# =============================
# 5. DATAFRAME
# =============================
st.markdown("### 📑 Data Lengkap 2018–2028")
st.dataframe(df_filtered.reset_index(drop=True))

