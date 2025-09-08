# app.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import pathlib
import matplotlib.pyplot as plt
from tqdm import tqdm

# ============================
# Config & paths
# ============================
st.set_page_config(page_title="Prediksi Surplus Pangan (2018-2028)", layout="wide", page_icon="🌾")
BASE = pathlib.Path.cwd()
MODEL_DIR = BASE / "model_output"
DATA_FILE = BASE / "prediksi permintaan (3).xlsx"   # sesuai file praktikan

# ============================
# CSS (soft)
# ============================
st.markdown("""
<style>
body { background-color: #f7f9fc; font-family: 'Segoe UI', Tahoma, sans-serif; color: #233044; }
h1 { color: #2b4865; }
.card { background: white; padding: 16px; border-radius: 12px; box-shadow: 0 6px 18px rgba(35,48,68,0.06); }
.stButton>button { background-color: #6c8ebf; color: white; border-radius: 8px; padding: 6px 12px; }
</style>
""", unsafe_allow_html=True)

# ============================
# Utility: rolling forecast using saved models (with lag)
# - expects models per komoditas at MODEL_DIR/konsumsi_{kom}.pkl
# - input df_train must contain columns: Provinsi, Komoditas, Tahun, produksi, konsumsi (ton)
# ============================
@st.cache_data(ttl=3600)
def compute_forecast_2018_2028(df_train):
    """
    Returns df_all with columns: Provinsi, Komoditas, Tahun, produksi, konsumsi (ton), Surplus
    Uses model files in MODEL_DIR; if missing model for a komoditas, it will skip forecasting that komoditas.
    Approach:
      - keep historical rows 2018-2023 as-is (consumption historical)
      - for each (Provinsi, Komoditas), start from latest available year (assume 2023 present),
        create lag1 & lag2 from historical, then iterate predict 2024..2028 updating lag1/lag2 each step.
      - produksi is assumed constant = produksi of 2023 for forecast years (change if you have a production projection)
    """
    years_forecast = list(range(2024, 2029))
    hist_years = list(range(2018, 2024))

    # ensure needed columns exist
    required = {"Provinsi", "Komoditas", "Tahun", "produksi", "konsumsi (ton)"}
    if not required.issubset(set(df_train.columns)):
        raise ValueError(f"Data tidak lengkap. Harap pastikan kolom ada: {required}")

    # take historical 2018-2023 (we will not change them)
    df_hist = df_train[df_train["Tahun"].isin(hist_years)].copy()

    # Prepare container for forecast rows
    preds = []

    # iterate per provinsi+komoditas
    groups = df_train.groupby(["Provinsi", "Komoditas"])
    total_groups = len(groups)
    for (prov, kom), group in tqdm(groups, desc="Rolling forecast", disable=True):
        # sort by year
        g = group.sort_values("Tahun").reset_index(drop=True)

        # get model file
        model_path = MODEL_DIR / f"konsumsi_{kom}.pkl"
        if not model_path.exists():
            # skip forecasting for this komoditas (keep historical only)
            # continue to next group
            continue

        # load model
        try:
            mdl = joblib.load(model_path)
            model = mdl["model"]
            feat_cols = mdl["feat"]
        except Exception as e:
            # couldn't load model; skip
            continue

        # ensure we have at least two previous years to build lag1/lag2
        # but if group lacks earlier years, we still try with available values (fillna)
        # create a working row representing the last available year (assume 2023 present)
        # pick last row by tahun (prefer 2023)
        if 2023 in g["Tahun"].values:
            last = g[g["Tahun"] == 2023].iloc[-1].copy()
        else:
            last = g.iloc[-1].copy()

        # compute lag1 & lag2 from group if not present
        # lag1 = konsumsi(t-1), lag2 = konsumsi(t-2)
        g_sorted = g.sort_values("Tahun")
        g_sorted["lag1"] = g_sorted["konsumsi (ton)"].shift(1)
        g_sorted["lag2"] = g_sorted["konsumsi (ton)"].shift(2)

        # if last year has lag values in g_sorted, use them; else use NaN and fill later
        try:
            last_idx = g_sorted[g_sorted["Tahun"] == last["Tahun"]].index[-1]
            last_lag1 = g_sorted.loc[last_idx, "lag1"]
            last_lag2 = g_sorted.loc[last_idx, "lag2"]
        except Exception:
            last_lag1 = np.nan
            last_lag2 = np.nan

        # create a mutable dict for the "current" state we'll update each forecast year
        cur = last.copy()
        # ensure columns required by model exist in cur (fill missing with reasonable defaults)
        for c in feat_cols:
            if c not in cur.index:
                cur[c] = np.nan

        # set lag1/lag2 in cur if model expects them
        if "lag1" in feat_cols:
            cur["lag1"] = last_lag1
        if "lag2" in feat_cols:
            cur["lag2"] = last_lag2

        # for safety: fill any NaN numeric features by the group's 2023 mean or overall mean
        # Compute fallback defaults from group's last year (or group means)
        fallback = {}
        for c in feat_cols:
            if pd.isna(cur.get(c, np.nan)):
                # try to take group's mean of that feature for 2023 if present, else overall group's mean
                if 2023 in g_sorted["Tahun"].values and c in g_sorted.columns:
                    val = g_sorted[g_sorted["Tahun"] == 2023][c].mean()
                elif c in g_sorted.columns:
                    val = g_sorted[c].mean()
                else:
                    val = 0.0
                cur[c] = val
                fallback[c] = val

        # iterate forecast years
        for y in years_forecast:
            # prepare X row with feature columns in same order
            X_row = pd.DataFrame([cur[feat_cols].values], columns=feat_cols)

            # some models expect no NaN - fill any remaining NaN with zeros
            X_row = X_row.fillna(0)

            # predict log -> expm1
            try:
                pred_log = model.predict(X_row)[0]
                pred_ton = float(np.expm1(pred_log))
            except Exception:
                pred_ton = float(np.nan)

            # prepare predicted row
            pred_row = cur.copy()
            pred_row["Tahun"] = y
            pred_row["konsumsi (ton)"] = pred_ton
            # produksi: assume same as cur['produksi'] (i.e., 2023 production)
            # If produksi missing, set 0
            if "produksi" not in pred_row.index or pd.isna(pred_row["produksi"]):
                pred_row["produksi"] = cur.get("produksi", 0.0)
            # compute surplus
            pred_row["Surplus"] = pred_row["produksi"] - pred_row["konsumsi (ton)"]

            # append to preds
            preds.append(pred_row[["Provinsi","Komoditas","Tahun","produksi","konsumsi (ton)","Surplus"]].to_dict())

            # update cur for next year: shift lag2 <- lag1, lag1 <- pred_ton
            if "lag2" in feat_cols:
                cur["lag2"] = cur.get("lag1", np.nan)
            if "lag1" in feat_cols:
                cur["lag1"] = pred_ton

            # also set Tahun to next for completeness
            cur["Tahun"] = y

    # create dataframe of predictions
    if preds:
        df_pred = pd.DataFrame(preds)
    else:
        df_pred = pd.DataFrame(columns=["Provinsi","Komoditas","Tahun","produksi","konsumsi (ton)","Surplus"])

    # combine hist + preds
    df_hist_sel = df_hist[["Provinsi","Komoditas","Tahun","produksi","konsumsi (ton)"]].copy()
    df_hist_sel["Surplus"] = df_hist_sel["produksi"] - df_hist_sel["konsumsi (ton)"]

    df_all = pd.concat([df_hist_sel, df_pred], ignore_index=True, sort=False)

    # ensure types
    df_all["Tahun"] = df_all["Tahun"].astype(int)
    df_all = df_all.sort_values(["Provinsi","Komoditas","Tahun"]).reset_index(drop=True)

    return df_all

# ============================
# Load data & compute forecast
# ============================
st.title("🌾 Prediksi Surplus/Defisit Pangan (2018–2028) — dengan model lag")
st.write("Model XGBoost (dengan lag) digunakan untuk melakukan forecast konsumsi 2024–2028. Produksi diasumsikan sama dengan produksi 2023 jika tidak ada proyeksi produksi.")

# load excel
try:
    df_raw = pd.read_excel(DATA_FILE)
except FileNotFoundError:
    st.error(f"File data tidak ditemukan: `{DATA_FILE.name}`. Upload file ini ke repo atau rename sesuai.")
    st.stop()

# rename columns to consistent lowercase names if needed
df_raw.columns = [c.strip() for c in df_raw.columns]

# check presence of required columns
if not {"Provinsi","Komoditas","Tahun","produksi","konsumsi (ton)"}.issubset(set(df_raw.columns)):
    st.error("File data harus punya kolom: Provinsi, Komoditas, Tahun, produksi, konsumsi (ton). Periksa header Excel.")
    st.stop()

# compute (cached)
with st.spinner("Menghitung forecast 2024–2028 (menggunakan model XGBoost)..."):
    try:
        df_all = compute_forecast_2018_2028(df_raw)
    except Exception as e:
        st.error(f"Gagal melakukan forecast: {e}")
        st.stop()

# ============================
# UI: selectors
# ============================
left, right = st.columns([2,1])
with left:
    provinsi = st.selectbox("Pilih Provinsi", sorted(df_all["Provinsi"].unique()))
    komoditas = st.selectbox("Pilih Komoditas", sorted(df_all["Komoditas"].unique()))
with right:
    tahun = st.selectbox("Pilih Tahun", sorted(df_all["Tahun"].unique()), index=len(sorted(df_all["Tahun"].unique()))-1)

# filter
df_filtered = df_all[(df_all["Provinsi"]==provinsi) & (df_all["Komoditas"]==komoditas)].copy()
if df_filtered.empty:
    st.warning("Data untuk kombinasi Provinsi/Komoditas tidak tersedia.")
else:
    # get selected year row
    row = df_filtered[df_filtered["Tahun"] == int(tahun)]
    if not row.empty:
        r = row.iloc[0]
        produksi = r["produksi"]
        konsumsi = r["konsumsi (ton)"]
        surplus = r["Surplus"]
        st.subheader("📊 Hasil Prediksi")
        st.markdown(f"**Provinsi:** {provinsi}  \n**Komoditas:** {komoditas}  \n**Tahun:** {int(tahun)}")
        st.markdown(f"- Produksi: **{produksi:,.0f} ton**")
        st.markdown(f"- Konsumsi: **{konsumsi:,.0f} ton**")
        if surplus >= 0:
            st.markdown(f"<p style='color:green; font-weight:700'>✅ Surplus: {surplus:,.0f} ton</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color:red; font-weight:700'>❌ Defisit: {abs(surplus):,.0f} ton</p>", unsafe_allow_html=True)
    else:
        st.warning("Data untuk tahun tersebut tidak tersedia.")

    # plot trend 2018-2028 (Surplus)
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(df_filtered["Tahun"], df_filtered["Surplus"], marker="o", linewidth=2, label="Surplus")
    ax.axhline(0, color="black", linestyle="--", linewidth=1, alpha=0.7)
    # shade forecast years
    ax.axvspan(2023.5, 2028.5, color="gray", alpha=0.15, label="Forecast 2024-2028")
    ax.set_title(f"Tren Surplus {komoditas} — {provinsi} (2018–2028)")
    ax.set_xlabel("Tahun")
    ax.set_ylabel("Surplus (Ton)")
    ax.set_xticks(sorted(df_filtered["Tahun"].unique()))
    ax.grid(alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    st.subheader("📑 Data (historis + prediksi)")
    st.dataframe(df_filtered.reset_index(drop=True))

# footer / tips
st.markdown("---")
st.caption("Catatan: Prediksi konsumsi 2024–2028 dihasilkan oleh model XGBoost (dengan fitur lag1 & lag2). Produksi diasumsikan sama seperti produksi 2023 jika tidak ada proyeksi produksi.")
