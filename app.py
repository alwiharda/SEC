# ============================================================
# app.py – Prediksi Surplus Pangan Dinamis dengan Input Baru
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt

# -------------------------
# 1. LOAD DATA HISTORIS
# -------------------------
FILE = "prediksi permintaan (3).xlsx"

df = pd.read_excel(FILE)
df.columns = df.columns.str.strip()
df = df.rename(columns={
    "produksi": "Produksi",
    "konsumsi (ton)": "Konsumsi"
})
df["Tahun"] = df["Tahun"].astype(int)

# -------------------------
# 2. ENCODING
# -------------------------
le_prov = LabelEncoder()
le_komod = LabelEncoder()

df["Provinsi_enc"] = le_prov.fit_transform(df["Provinsi"])
df["Komoditas_enc"] = le_komod.fit_transform(df["Komoditas"])

# -------------------------
# 3. STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Prediksi Surplus Dinamis", layout="wide")
st.title("📊 Prediksi Surplus Pangan Dinamis (XGBoost)")

col1, col2 = st.columns(2)
with col1:
    provinsi = st.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
with col2:
    komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

# Filter data historis
df_filtered = df[(df["Provinsi"]==provinsi) & (df["Komoditas"]==komoditas)].copy()

# -------------------------
# 4. INPUT DATA BARU
# -------------------------
st.subheader("➕ Tambah Data Baru")
latest_year = df_filtered["Tahun"].max()

with st.form("input_data"):
    tahun_baru = st.number_input("Tahun", min_value=latest_year+1, step=1, value=latest_year+1)
    produksi_baru = st.number_input("Produksi (ton)", min_value=0, step=1000)
    konsumsi_baru = st.number_input("Konsumsi (ton)", min_value=0, step=1000)
    submit = st.form_submit_button("Simpan Data")

if submit:
    new_row = {
        "Provinsi": provinsi,
        "Komoditas": komoditas,
        "Tahun": tahun_baru,
        "Produksi": produksi_baru,
        "Konsumsi": konsumsi_baru,
        "Provinsi_enc": le_prov.transform([provinsi])[0],
        "Komoditas_enc": le_komod.transform([komoditas])[0],
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    st.success(f"✅ Data tahun {tahun_baru} berhasil ditambahkan!")

# -------------------------
# 5. TRAIN MODEL
# -------------------------
X = df[["Tahun", "Provinsi_enc", "Komoditas_enc"]]
y_prod = df["Produksi"]
y_kons = df["Konsumsi"]

model_prod = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
model_kons = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)

model_prod.fit(X, y_prod)
model_kons.fit(X, y_kons)

# -------------------------
# 6. PREDIKSI TAHUN BERIKUTNYA
# -------------------------
next_year = df_filtered["Tahun"].max() + 1
X_pred = pd.DataFrame({
    "Tahun": [next_year],
    "Provinsi_enc": [le_prov.transform([provinsi])[0]],
    "Komoditas_enc": [le_komod.transform([komoditas])[0]]
})

pred_prod = model_prod.predict(X_pred)[0]
pred_kons = model_kons.predict(X_pred)[0]
pred_surplus = pred_prod - pred_kons

st.subheader(f"📈 Prediksi Tahun {next_year}")
st.markdown(f"""
- **Produksi**: {pred_prod:,.0f} ton  
- **Konsumsi**: {pred_kons:,.0f} ton  
- **Surplus**: {pred_surplus:,.0f} ton  
- **Status**: {"🟢 Surplus" if pred_surplus > 0 else "🔴 Defisit"}
""")

# -------------------------
# 7. VISUALISASI TREND
# -------------------------
df_filtered = df[(df["Provinsi"]==provinsi) & (df["Komoditas"]==komoditas)]

fig, ax = plt.subplots(figsize=(10,5))
ax.plot(df_filtered["Tahun"], df_filtered["Produksi"], marker="o", label="Produksi")
ax.plot(df_filtered["Tahun"], df_filtered["Konsumsi"], marker="s", label="Konsumsi")
ax.bar(df_filtered["Tahun"], df_filtered["Produksi"]-df_filtered["Konsumsi"], alpha=0.3, label="Surplus")

ax.axvline(x=next_year, color="red", linestyle="--", label="Prediksi Tahun Berikutnya")
ax.legend()
ax.set_title(f"Data & Prediksi Surplus — {provinsi} ({komoditas})")
st.pyplot(fig)

