# ============================================================
# app.py – Training + Prediksi Produksi & Konsumsi (Streamlit)
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold
import xgboost as xgb
import joblib, pathlib, warnings, os

warnings.filterwarnings("ignore")

# ---------- 1. KONFIG ----------
st.set_page_config(page_title="Prediksi Pangan", layout="wide")
MODEL_DIR = pathlib.Path("model_output")
MODEL_DIR.mkdir(exist_ok=True)

FILE = r"prediksi permintaan (3).xlsx"

# ---------- 2. LOAD DATA ----------
@st.cache_data
def load_data():
    df = pd.read_excel(FILE, sheet_name="Sheet1")
    df.columns = df.columns.str.strip()
    df["konsumsi (ton)"] = pd.to_numeric(df["konsumsi (ton)"], errors="coerce")
    df["produksi"] = pd.to_numeric(df["produksi"], errors="coerce")
    df = df.dropna()
    df["Tahun"] = df["Tahun"].astype(int)

    # Tambahkan lag
    df = df.sort_values(["Provinsi", "Komoditas", "Tahun"])
    for target in ["konsumsi (ton)", "produksi"]:
        df[f"{target}_lag1"] = df.groupby(["Provinsi", "Komoditas"])[target].shift(1)
        df[f"{target}_lag2"] = df.groupby(["Provinsi", "Komoditas"])[target].shift(2)
    df = df.dropna()
    return df

df = load_data()

# ---------- 3. TRAIN MODEL (jika belum ada) ----------
def train_and_save_models(df):
    def train_target(target):
        feat = ["curah hujan (mm)", "suhu (C)", "Jumlah Penduduk", "PDRB (tahunan)",
                f"{target}_lag1", f"{target}_lag2"]

        for kom in df["Komoditas"].unique():
            fname = MODEL_DIR / f"{kom.lower()}_{target.split()[0].lower()}.pkl"
            if fname.exists():
                continue  # skip kalau sudah ada

            sub = df[df["Komoditas"] == kom].copy()
            X = sub[feat]
            y = sub[target]
            y_log = np.log1p(y)

            groups = sub["Provinsi"].factorize()[0]
            gkf = GroupKFold(n_splits=5)

            for tr_idx, vl_idx in gkf.split(X, y_log, groups):
                X_tr, X_vl = X.iloc[tr_idx], X.iloc[vl_idx]
                y_tr, y_vl = y_log.iloc[tr_idx], y_log.iloc[vl_idx]

                model = xgb.XGBRegressor(
                    n_estimators=200, learning_rate=0.05, max_depth=3,
                    subsample=0.6, colsample_bytree=0.6, reg_lambda=5.0,
                    objective="reg:tweedie", tweedie_variance_power=1.2,
                    eval_metric="mae", random_state=42, n_jobs=-1,
                )
                model.fit(X_tr, y_tr)

            # full train
            full_model = xgb.XGBRegressor(**model.get_params())
            full_model.fit(X, y_log)

            joblib.dump({"model": full_model, "feat": feat}, fname)
            st.success(f"✅ Model {kom} ({target}) tersimpan → {fname.name}")

    train_target("konsumsi (ton)")
    train_target("produksi")

# Panggil sekali (auto training kalau model belum ada)
train_and_save_models(df)

# ---------- 4. UI ----------
st.title("📊 Prediksi Produksi & Konsumsi Komoditas")

komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))
target = st.radio("Pilih Target", ["Produksi", "Konsumsi"])
target_file = "produksi" if target == "Produksi" else "konsumsi"
model_file = MODEL_DIR / f"{komoditas.lower()}_{target_file.lower()}.pkl"

# ---------- 5. DATA AKTUAL ----------
st.subheader("📑 Data Aktual")
sub = df[df["Komoditas"] == komoditas][["Tahun", "produksi", "konsumsi (ton)"]]
st.dataframe(sub.sort_values("Tahun"))

# ---------- 6. PREDIKSI ----------
if not model_file.exists():
    st.error("Model belum tersedia untuk komoditas ini.")
    st.stop()

mdl = joblib.load(model_file)
model, feat = mdl["model"], mdl["feat"]

# pakai data terakhir buat prediksi 3 tahun ke depan
df_last = df[df["Komoditas"] == komoditas].sort_values("Tahun").copy().iloc[-1:]
preds = []

for t in range(1, 4):
    tahun_next = int(df_last["Tahun"].values[0]) + t
    lag1 = df_last[target_file.lower()].values[0]
    lag2 = df_last[target_file.lower()].shift(1, fill_value=lag1).values[0]

    X_new = pd.DataFrame([{
        "curah hujan (mm)": df_last["curah hujan (mm)"].values[0],
        "suhu (C)": df_last["suhu (C)"].values[0],
        "Jumlah Penduduk": df_last["Jumlah Penduduk"].values[0],
        "PDRB (tahunan)": df_last["PDRB (tahunan)"].values[0],
        f"{target_file}_lag1": lag1,
        f"{target_file}_lag2": lag2,
    }])

    y_pred = np.expm1(model.predict(X_new))[0]
    preds.append({"Tahun": tahun_next, target: y_pred})
    df_last[target_file.lower()] = y_pred  # update untuk prediksi berikutnya

st.subheader("🔮 Prediksi 3 Tahun ke Depan")
st.dataframe(pd.DataFrame(preds).round(2))
