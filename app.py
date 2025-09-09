# ============================================================
# app.py – Prediksi Surplus Pangan dengan XGBoost
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt

# -------------------------
# 1. LOAD DATA
# -------------------------
FILE = "prediksi permintaan (3).xlsx"

df = pd.read_excel(FILE)
df.columns = df.columns.str.strip()

# Pastikan konsisten
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

# Fitur
X = df[["Tahun", "Provinsi_enc", "Komoditas_enc"]]

# -------------------------
# 3. TRAIN MODEL PRODUKSI
# -------------------------
y_prod = df["Produksi"]
X_train, X_test, y_train, y_test = train_test_split(X, y_prod, test_size=0.2, random_state=42)

model_prod = xgb.XGBRegressor(
    n_estimators=300,
    learning_rate=0.1,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model_prod.fit(X_train, y_train)

# -------------------------
# 4. TRAIN MODEL KONSUMSI
# -------------------------
y_kons = df["Konsumsi"]
X_train, X_test, y_train, y_test = train_test_split(X, y_kons, test_size=0.2, random_state=42)

model_kons = xgb.XGBRegressor(
    n_estimators=300,
    learning_rate=0.1,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
model_kons.fit(X_train, y_train)

# -------------------------
# 5. STREAMLIT UI
# -------------------------
st.set_page_config(page_title="Prediksi Surplus XGBoost", layout="wide")
st.title("📊 Prediksi Surplus Pangan 2024–2028 (XGBoost)")

col1, col2 = st.columns(2)
with col1:
    provinsi = st.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
with col2:
    komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

tahun_pred = st.slider("Pilih Tahun Prediksi", 2024, 2028, 2024)

# Encode input
prov_enc = le_prov.transform([provinsi])[0]
komod_enc = le_komod.transform([komoditas])[0]

# -------------------------
# 6. PREDIKSI
# -------------------------
X_input = pd.DataFrame({
    "Tahun": [tahun_pred],
    "Provinsi_enc": [prov_enc],
    "Komoditas_enc": [komod_enc]
})

pred_prod = model_prod.predict(X_input)[0]
pred_kons = model_kons.predict(X_input)[0]
pred_surplus = pred_prod - pred_kons

st.subheader(f"Hasil Prediksi {tahun_pred}")
st.markdown(f"""
- **Produksi**: {pred_prod:,.0f} ton  
- **Konsumsi**: {pred_kons:,.0f} ton  
- **Surplus**: {pred_surplus:,.0f} ton  
- **Status**: {"🟢 Surplus" if pred_surplus>0 else "🔴 Defisit"}
""")

# -------------------------
# 7. VISUALISASI TREND
# -------------------------
future_years = list(range(2024, 2029))
X_future = pd.DataFrame({
    "Tahun": future_years,
    "Provinsi_enc": [prov_enc]*len(future_years),
    "Komoditas_enc": [komod_enc]*len(future_years)
})

future_prod = model_prod.predict(X_future)
future_kons = model_kons.predict(X_future)
future_surplus = future_prod - future_kons

fig, ax = plt.subplots(figsize=(10,5))
ax.plot(future_years, future_prod, marker="o", label="Produksi")
ax.plot(future_years, future_kons, marker="s", label="Konsumsi")
ax.bar(future_years, future_surplus, alpha=0.3, label="Surplus")
ax.set_title(f"Prediksi Tren 2024–2028 – {provinsi} ({komoditas})")
ax.set_xlabel("Tahun")
ax.set_ylabel("Ton")
ax.legend()
st.pyplot(fig)

