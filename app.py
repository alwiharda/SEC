import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import xgboost as xgb

# ============================================================
# 1. Load Data
# ============================================================
DATA_FILE = "prediksi permintaan (3).xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    return df

df = load_data()

# ============================================================
# 2. Sidebar Pilihan
# ============================================================
st.sidebar.header("🔎 Pilih Parameter")
provinsi = st.sidebar.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.sidebar.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

# Filter data
df_filtered = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)].copy()
df_filtered = df_filtered.sort_values("Tahun")

col_prod = "produksi"
col_kons = "konsumsi (ton)"

# Hitung surplus aktual
df_filtered["Surplus"] = df_filtered[col_prod] - df_filtered[col_kons]

# ============================================================
# 3. Input Data Tahun Terbaru
# ============================================================
st.sidebar.subheader("➕ Input Data Tahun Terbaru")
tahun_input = st.sidebar.number_input("Tahun", min_value=int(df_filtered["Tahun"].max())+1, step=1, value=int(df_filtered["Tahun"].max())+1)
produksi_input = st.sidebar.number_input("Produksi (ton)", min_value=0.0, step=1000.0, value=0.0)
konsumsi_input = st.sidebar.number_input("Konsumsi (ton)", min_value=0.0, step=1000.0, value=0.0)

if st.sidebar.button("Tambahkan Data"):
    new_row = {
        "Provinsi": provinsi,
        "Komoditas": komoditas,
        "Tahun": tahun_input,
        col_prod: produksi_input,
        col_kons: konsumsi_input,
        "Surplus": produksi_input - konsumsi_input
    }
    df_filtered = pd.concat([df_filtered, pd.DataFrame([new_row])], ignore_index=True)
    st.success(f"Data tahun {tahun_input} berhasil ditambahkan!")

# ============================================================
# 4. Train Model
# ============================================================
X = df_filtered[["Tahun"]]
y_prod = df_filtered[col_prod]
y_kons = df_filtered[col_kons]

model_prod = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=3)
model_prod.fit(X, y_prod)

model_kons = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=3)
model_kons.fit(X, y_kons)

# ============================================================
# 5. Prediksi 5 Tahun ke Depan
# ============================================================
tahun_terakhir = int(df_filtered["Tahun"].max())
tahun_prediksi = list(range(tahun_terakhir+1, tahun_terakhir+6))

X_pred = pd.DataFrame({"Tahun": tahun_prediksi})
y_pred_prod = model_prod.predict(X_pred)
y_pred_kons = model_kons.predict(X_pred)
y_pred_surplus = y_pred_prod - y_pred_kons

df_pred = pd.DataFrame({
    "Tahun": tahun_prediksi,
    "Produksi (Prediksi)": y_pred_prod,
    "Konsumsi (Prediksi)": y_pred_kons,
    "Surplus (Prediksi)": y_pred_surplus
})

# ============================================================
# 6. Tampilkan Hasil Prediksi
# ============================================================
st.subheader("📊 Prediksi 5 Tahun ke Depan")
st.dataframe(df_pred.style.format("{:,.0f}"))

# ============================================================
# 7. Visualisasi
# ============================================================
fig, ax = plt.subplots(figsize=(10,6))

# Plot data historis
ax.plot(df_filtered["Tahun"], df_filtered[col_prod], marker="o", label="Produksi Aktual")
ax.plot(df_filtered["Tahun"], df_filtered[col_kons], marker="s", label="Konsumsi Aktual")
ax.bar(df_filtered["Tahun"], df_filtered["Surplus"], alpha=0.3, label="Surplus Aktual")

# Plot prediksi
ax.plot(df_pred["Tahun"], df_pred["Produksi (Prediksi)"], marker="o", linestyle="--", color="blue", label="Produksi Prediksi")
ax.plot(df_pred["Tahun"], df_pred["Konsumsi (Prediksi)"], marker="s", linestyle="--", color="orange", label="Konsumsi Prediksi")
ax.bar(df_pred["Tahun"], df_pred["Surplus (Prediksi)"], alpha=0.3, color="gray", label="Surplus Prediksi")

ax.set_title(f"Data & Prediksi Surplus — {provinsi} ({komoditas})")
ax.set_xlabel("Tahun")
ax.set_ylabel("Jumlah (ton)")
ax.legend()
st.pyplot(fig)
