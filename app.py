import streamlit as st
import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
import matplotlib.pyplot as plt
import pathlib

# =====================================================
# 1. LOAD DATA & MODEL
# =====================================================
DATA_FILE = r"prediksi permintaan (3).xlsx"
MODEL_DIR = pathlib.Path("model_output")

df = pd.read_excel(DATA_FILE, sheet_name="Sheet1")
df.columns = df.columns.str.strip().str.lower()

# identifikasi nama kolom target
konsumsi_col = [c for c in df.columns if "konsumsi" in c and "ton" in c][0]
produksi_col = [c for c in df.columns if "produksi" in c][0]

df["konsumsi (ton)"] = pd.to_numeric(df[konsumsi_col], errors="coerce")
df["produksi"] = pd.to_numeric(df[produksi_col], errors="coerce")

FEAT_BASE = ["curah hujan (mm)", "suhu (c)", "jumlah penduduk", "pdrb (tahunan)"]

# =====================================================
# 2. STREAMLIT UI
# =====================================================
st.title("📊 Prediksi Produksi & Konsumsi Pangan")
st.markdown("Prediksi berbasis **XGBoost** untuk 3 tahun ke depan.")

provinsi = st.selectbox("Pilih Provinsi", sorted(df["provinsi"].unique()))
komoditas = st.selectbox("Pilih Komoditas", sorted(df["komoditas"].unique()))
target = st.radio("Pilih Target", ["Produksi", "Konsumsi (ton)"])

# filter data sesuai pilihan
df_sel = df[(df["provinsi"] == provinsi) & (df["komoditas"] == komoditas)].copy()
df_sel = df_sel.sort_values("tahun")

st.subheader("📑 Data Aktual")
st.dataframe(df_sel[["tahun", "produksi", "konsumsi (ton)"]])

# =====================================================
# 3. LOAD MODEL
# =====================================================
target_col = target.lower()
model_file = MODEL_DIR / f"{target_col}_{komoditas}.pkl"
if not model_file.exists():
    st.error("Model belum tersedia untuk komoditas ini.")
    st.stop()

mdl = joblib.load(model_file)
model, feat = mdl["model"], mdl["feat"]

# =====================================================
# 4. PREDIKSI 3 TAHUN KE DEPAN (REKURSIF)
# =====================================================
tahun_max = df_sel["tahun"].max()
pred_years = [tahun_max + i for i in range(1, 4)]
df_pred = df_sel.copy()

for tahun in pred_years:
    df_next = df_pred[df_pred["tahun"] == df_pred["tahun"].max()].copy()
    df_next["tahun"] = tahun

    # update lag
    df_next[f"{target_col}_lag2"] = df_next[f"{target_col}_lag1"]
    df_next[f"{target_col}_lag1"] = df_next[target_col]

    X_new = df_next[feat]
    y_pred = np.expm1(model.predict(X_new))

    df_next[target_col] = y_pred
    df_next = df_next[["provinsi", "komoditas", "tahun", target_col,
                       f"{target_col}_lag1", f"{target_col}_lag2"]]

    df_pred = pd.concat([df_pred, df_next], ignore_index=True)

# =====================================================
# 5. VISUALISASI
# =====================================================
plt.figure(figsize=(8, 4))
plt.plot(df_sel["tahun"], df_sel[target_col], marker="o", label="Aktual")
plt.plot(pred_years, df_pred[df_pred["tahun"].isin(pred_years)][target_col],
         marker="o", linestyle="--", color="red", label="Prediksi")
plt.xlabel("Tahun")
plt.ylabel(target)
plt.title(f"{target} {komoditas} di {provinsi}")
plt.legend()
st.pyplot(plt)

st.subheader("📈 Hasil Prediksi")
st.dataframe(df_pred[df_pred["tahun"].isin(pred_years)][["tahun", target_col]])
