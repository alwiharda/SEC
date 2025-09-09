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

# Normalisasi nama kolom
df.columns = df.columns.str.strip().str.lower()  # jadi huruf kecil semua

st.write("Kolom terbaca:", df.columns.tolist())

# ============================================================
# 2. INPUT USER
# ============================================================
# Cari nama kolom sesuai
col_tahun = [c for c in df.columns if "tahun" in c][0]
col_prov = [c for c in df.columns if "prov" in c][0]
col_kom = [c for c in df.columns if "komod" in c][0]
col_prod = [c for c in df.columns if "produ" in c][0]
col_kons = [c for c in df.columns if "kons" in c][0]

provinsi = st.selectbox("Pilih Provinsi:", df[col_prov].unique())
komoditas = st.selectbox("Pilih Komoditas:", df[col_kom].unique())

# ============================================================
# 3. FILTER DATA
# ============================================================
df_filtered = df[(df[col_prov]==provinsi) & (df[col_kom]==komoditas)].copy()
df_filtered = df_filtered.sort_values(col_tahun)

# ============================================================
# 4. FIT MODEL
# ============================================================
X = df_filtered[[col_tahun]]
y_prod = df_filtered[col_prod]
y_kons = df_filtered[col_kons]

model_prod = LinearRegression().fit(X, y_prod)
model_kons = LinearRegression().fit(X, y_kons)

# ============================================================
# 5. PREDIKSI
# ============================================================
next_year = df_filtered[col_tahun].max() + 1
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
# 7. VISUALISASI
# ============================================================
df_pred = pd.DataFrame({
    col_tahun: [next_year],
    col_prod: [pred_prod],
    col_kons: [pred_kons]
})
df_plot = pd.concat([df_filtered, df_pred], ignore_index=True)

fig, ax = plt.subplots(figsize=(10,5))

ax.plot(df_plot[col_tahun], df_plot[col_prod], marker="o", label="Produksi")
ax.plot(df_plot[col_tahun], df_plot[col_kons], marker="s", label="Konsumsi")

# Bar Surplus historis
ax.bar(df_filtered[col_tahun], df_filtered[col_prod]-df_filtered[col_kons],
       alpha=0.3, label="Surplus")

# Bar Surplus prediksi
ax.bar(next_year, pred_surplus, alpha=0.3, color="gray", label="Surplus Prediksi")

ax.axvline(x=next_year, color="red", linestyle="--", label="Prediksi Tahun Berikutnya")

ax.set_title(f"Data & Prediksi Surplus — {provinsi} ({komoditas})")
ax.legend()

st.pyplot(fig)
