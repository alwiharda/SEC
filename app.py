import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xgboost import XGBRegressor

# ============================================================
# 1. LOAD DATA
# ============================================================
DATA_FILE = "prediksi_permintaan.xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    return df

df = load_data()

# ============================================================
# 2. TITLE & FILTERS
# ============================================================
st.set_page_config(page_title="Prediksi Permintaan", layout="wide")

st.markdown(
    """
    <style>
    body {
        background-color: #f9fafb;
        color: #333333;
    }
    .stApp {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Prediksi Kebutuhan & Surplus Pangan per Provinsi")

provinsi = st.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

# ============================================================
# 3. FILTER DATA & HITUNG SURPLUS HISTORIS
# ============================================================
df_prov = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)].copy()

if df_prov.empty:
    st.warning("Data tidak tersedia untuk pilihan ini.")
    st.stop()

df_prov["Surplus"] = df_prov["produksi"] - df_prov["konsumsi (ton)"]

# ============================================================
# 4. TRAINING MODEL XGBOOST
# ============================================================
X = df_prov[["Tahun"]]
y_prod = df_prov["produksi"]
y_cons = df_prov["konsumsi (ton)"]

model_prod = XGBRegressor(n_estimators=200, random_state=42)
model_cons = XGBRegressor(n_estimators=200, random_state=42)

model_prod.fit(X, y_prod)
model_cons.fit(X, y_cons)

# ============================================================
# 5. FORECAST 2024–2028
# ============================================================
tahun_forecast = np.arange(2024, 2029)
X_future = pd.DataFrame({"Tahun": tahun_forecast})

y_pred_prod = model_prod.predict(X_future)
y_pred_cons = model_cons.predict(X_future)

df_future = pd.DataFrame({
    "Provinsi": provinsi,
    "Komoditas": komoditas,
    "Tahun": tahun_forecast,
    "produksi": y_pred_prod,
    "konsumsi (ton)": y_pred_cons
})
df_future["Surplus"] = df_future["produksi"] - df_future["konsumsi (ton)"]

# ============================================================
# 6. GABUNGKAN DATA HISTORIS + FORECAST
# ============================================================
df_plot = pd.concat([df_prov, df_future])

# ============================================================
# 7. VISUALISASI
# ============================================================
fig, ax = plt.subplots(figsize=(10,5))

# Plot historis
ax.plot(df_prov["Tahun"], df_prov["Surplus"], marker="o", label="Surplus Historis")

# Plot prediksi
ax.plot(df_future["Tahun"], df_future["Surplus"], marker="x", linestyle="--", label="Surplus Prediksi")

# Shading area prediksi
ax.fill_between(df_future["Tahun"], df_future["Surplus"].min(), df_future["Surplus"].max(),
                color="gray", alpha=0.2, label="Forecast 2024-2028")

ax.axhline(0, color="black", linestyle="--")
ax.set_title(f"Prediksi Surplus {komoditas} — {provinsi} (2018-2028)")
ax.set_ylabel("Surplus (Ton)")
ax.set_xlabel("Tahun")
ax.legend()

st.pyplot(fig)

# ============================================================
# 8. TAMPILKAN DATA
# ============================================================
st.subheader("📋 Data Historis + Prediksi")
st.dataframe(df_plot.reset_index(drop=True))

# ============================================================
# 9. CEK KEKURANGAN ATAU SURPLUS
# ============================================================
st.subheader("📌 Analisis Surplus / Kekurangan")

last_year = df_plot["Tahun"].max()
last_data = df_plot[df_plot["Tahun"] == last_year].iloc[0]

if last_data["Surplus"] >= 0:
    st.success(f"✅ Tahun {last_year}, {provinsi} diprediksi **SURPLUS** {komoditas} sebesar {last_data['Surplus']:.2f} ton.")
else:
    st.error(f"⚠️ Tahun {last_year}, {provinsi} diprediksi **KEKURANGAN** {komoditas} sebesar {abs(last_data['Surplus']):.2f} ton.")
