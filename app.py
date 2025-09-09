# ============================================================
# 0. IMPORT
# ============================================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import streamlit as st

# ============================================================
# 1. LOAD DATA
# ============================================================
FILE = "prediksi permintaan (3).xlsx"

df = pd.read_excel(FILE)

# Normalisasi nama kolom biar aman
df.columns = df.columns.str.strip()

# Pastikan ada kolom Tahun, Provinsi, Komoditas, Produksi, Konsumsi
st.write("📌 Data yang terbaca:", df.head())

# ============================================================
# 2. INPUT USER
# ============================================================
provinsi = st.selectbox("Pilih Provinsi:", df["Provinsi"].unique())
komoditas = st.selectbox("Pilih Komoditas:", df["Komoditas"].unique())

# ============================================================
# 3. FILTER DATA
# ============================================================
df_filtered = df[(df["Provinsi"]==provinsi) & (df["Komoditas"]==komoditas)].copy()
df_filtered = df_filtered.sort_values("Tahun")

# ============================================================
# 4. FIT MODEL LINEAR REGRESSION
# ============================================================
X = df_filtered[["Tahun"]]
y_prod = df_filtered["Produksi"]
y_kons = df_filtered["Konsumsi"]

model_prod = LinearRegression().fit(X, y_prod)
model_kons = LinearRegression().fit(X, y_kons)

# ============================================================
# 5. PREDIKSI
# ============================================================
next_year = df_filtered["Tahun"].max() + 1
pred_prod = model_prod.predict([[next_year]])[0]
pred_kons = model_kons.predict([[next_year]])[0]
pred_surplus = pred_prod - pred_kons

# ============================================================
# 6. TAMPILKAN HASIL
# ============================================================
st.markdown(f"""
### 📊 Prediksi Tahun {next_year}
- **Produksi:** {pred_prod:,.0f} ton  
- **Konsumsi:** {pred_kons:,.0f} ton  
- **Surplus:** {pred_surplus:,.0f} ton  
- **Status:** {"🟢 Surplus" if pred_surplus>0 else "🔴 Defisit"}
""")

# ============================================================
# 7. VISUALISASI TREND
# ============================================================
# Tambahkan prediksi ke DataFrame untuk diplot
df_pred = pd.DataFrame({
    "Tahun": [next_year],
    "Produksi": [pred_prod],
    "Konsumsi": [pred_kons]
})
df_plot = pd.concat([df_filtered, df_pred], ignore_index=True)

fig, ax = plt.subplots(figsize=(10,5))

# Garis Produksi & Konsumsi (termasuk prediksi)
ax.plot(df_plot["Tahun"], df_plot["Produksi"], marker="o", label="Produksi")
ax.plot(df_plot["Tahun"], df_plot["Konsumsi"], marker="s", label="Konsumsi")

# Bar Surplus historis
ax.bar(df_filtered["Tahun"], df_filtered["Produksi"]-df_filtered["Konsumsi"],
       alpha=0.3, label="Surplus")

# Bar Surplus prediksi
ax.bar(next_year, pred_surplus, alpha=0.3, color="gray", label="Surplus Prediksi")

# Garis vertikal tahun prediksi
ax.axvline(x=next_year, color="red", linestyle="--", label="Prediksi Tahun Berikutnya")

ax.set_title(f"Data & Prediksi Surplus — {provinsi} ({komoditas})")
ax.legend()

st.pyplot(fig)
