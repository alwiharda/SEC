import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# =========================================================
# 1. LOAD DATA
# =========================================================
FILE = "prediksi permintaan (3).xlsx"
df = pd.read_excel(FILE)

# rapikan nama kolom
df.columns = df.columns.str.strip().str.lower()
df = df.rename(columns={
    "provinsi": "Provinsi",
    "komoditas": "Komoditas",
    "tahun": "Tahun",
    "produksi": "Produksi",
    "konsumsi (ton)": "Konsumsi"
})

# =========================================================
# 2. SIDEBAR FILTER
# =========================================================
st.sidebar.header("Filter Data")
provinsi = st.sidebar.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.sidebar.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

df_sel = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)].copy()
df_sel = df_sel.sort_values("Tahun")

# =========================================================
# 3. TRAIN MODEL XGBOOST
# =========================================================
def train_and_forecast(df_in, col_target, n_forecast=3):
    X = df_in[["Tahun"]]
    y = df_in[col_target]

    model = XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=3, random_state=42)
    model.fit(X, y)

    tahun_max = df_in["Tahun"].max()
    tahun_pred = np.arange(tahun_max + 1, tahun_max + n_forecast + 1)

    y_pred = model.predict(tahun_pred.reshape(-1, 1))

    df_pred = pd.DataFrame({"Tahun": tahun_pred, col_target: y_pred})
    return df_pred, model

# Prediksi produksi dan konsumsi 3 tahun ke depan
df_pred_prod, model_prod = train_and_forecast(df_sel, "Produksi", n_forecast=3)
df_pred_kons, model_kons = train_and_forecast(df_sel, "Konsumsi", n_forecast=3)

# gabungkan hasil prediksi
df_pred = pd.merge(df_pred_prod, df_pred_kons, on="Tahun")
df_pred["Surplus"] = df_pred["Produksi"] - df_pred["Konsumsi"]

# gabungkan historis + prediksi
df_all = pd.concat([df_sel[["Tahun", "Produksi", "Konsumsi"]], df_pred], ignore_index=True)
df_all["Surplus"] = df_all["Produksi"] - df_all["Konsumsi"]

# =========================================================
# 4. VISUALISASI
# =========================================================
st.subheader(f"Prediksi 3 Tahun ke Depan – {provinsi} ({komoditas})")

# tampilkan tabel
st.write("### Data Historis + Prediksi")
st.dataframe(df_all)

# plot grafik
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df_sel["Tahun"], df_sel["Produksi"], marker="o", color="green", label="Produksi (Hist)")
ax.plot(df_sel["Tahun"], df_sel["Konsumsi"], marker="o", color="red", label="Konsumsi (Hist)")

ax.plot(df_pred["Tahun"], df_pred["Produksi"], marker="s", linestyle="--", color="lime", label="Produksi (Prediksi)")
ax.plot(df_pred["Tahun"], df_pred["Konsumsi"], marker="s", linestyle="--", color="orange", label="Konsumsi (Prediksi)")

ax.axhline(0, color="black", linewidth=0.8)
ax.set_title(f"Prediksi Produksi & Konsumsi {provinsi} – {komoditas}", fontsize=14)
ax.set_xlabel("Tahun")
ax.set_ylabel("Ton")
ax.legend()
ax.grid(True, alpha=0.3)

st.pyplot(fig)

# =========================================================
# 5. INFO SURPLUS / DEFISIT
# =========================================================
st.write("### Status Surplus / Defisit (Prediksi)")
for _, row in df_pred.iterrows():
    status = "✅ Surplus" if row["Surplus"] > 0 else "❌ Defisit"
    st.write(f"Tahun {int(row['Tahun'])}: {status} ({row['Surplus']:.0f} ton)")
