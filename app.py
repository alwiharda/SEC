import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from xgboost import XGBRegressor

# ==========================================================
# Fungsi Training & Forecast
# ==========================================================
def train_and_forecast(df_in, target_col, n_forecast=3):
    # pakai fitur tambahan selain tahun
    fitur = ["Tahun", "curah hujan (mm)", "suhu (c)", "jumlah penduduk", "pdrb (tahunan)"]
    fitur = [f for f in fitur if f in df_in.columns]

    # siapkan data
    X = df_in[fitur]
    y = df_in[target_col]

    # train model
    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    model.fit(X, y)

    # buat data prediksi
    tahun_max = int(df_in["Tahun"].max())
    pred_rows = []
    last_row = df_in.iloc[-1].to_dict()

    for i in range(1, n_forecast + 1):
        tahun_next = tahun_max + i
        row_pred = {k: last_row[k] for k in fitur if k != "Tahun"}
        row_pred["Tahun"] = tahun_next
        pred_rows.append(row_pred)

    X_pred = pd.DataFrame(pred_rows)[fitur]   # <- urutan kolom sama
    y_pred = model.predict(X_pred)

    df_pred = X_pred.copy()
    df_pred[target_col] = y_pred
    return df_pred, model

# ==========================================================
# Aplikasi Streamlit (tanpa upload file)
# ==========================================================
st.set_page_config(page_title="Prediksi Surplus Pangan", layout="wide")
st.title("📊 Prediksi Produksi, Konsumsi & Surplus Pangan")

# baca data langsung
FILE = "prediksi permintaan (3).xlsx"
df = pd.read_excel(FILE)

# pilih provinsi & komoditas
provinsi = st.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

df_filtered = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)].copy()

if len(df_filtered) > 3:
    # training produksi & konsumsi
    df_pred_prod, model_prod = train_and_forecast(df_filtered, "Produksi", n_forecast=3)
    df_pred_kons, model_kons = train_and_forecast(df_filtered, "Konsumsi (ton)", n_forecast=3)

    # gabungkan hasil prediksi
    df_forecast = pd.DataFrame({
        "Tahun": df_pred_prod["Tahun"],
        "Produksi": df_pred_prod["Produksi"],
        "Konsumsi": df_pred_kons["Konsumsi (ton)"]
    })
    df_forecast["Surplus"] = df_forecast["Produksi"] - df_forecast["Konsumsi"]

    # gabung data asli + prediksi
    df_show = pd.concat([
        df_filtered[["Tahun", "Produksi", "Konsumsi (ton)"]].rename(columns={"Konsumsi (ton)": "Konsumsi"}),
        df_forecast.rename(columns={"Konsumsi (ton)": "Konsumsi"})
    ], ignore_index=True)

    # tampilkan tabel hasil
    st.subheader(f"📑 Data & Prediksi {komoditas} — {provinsi}")
    st.dataframe(df_show.tail(7))

    # plot
    fig, ax = plt.subplots(figsize=(10, 5))
    tahun = df_show["Tahun"]
    ax.plot(tahun, df_show["Produksi"], marker="o", label="Produksi")
    ax.plot(tahun, df_show["Konsumsi"], marker="s", label="Konsumsi")
    ax.bar(tahun, df_show["Surplus"], alpha=0.3, label="Surplus")

    tahun_max = df_filtered["Tahun"].max()
    ax.axvline(x=tahun_max + 0.5, color="red", linestyle="--", label="Prediksi dimulai")

    ax.set_title(f"Data & Prediksi Surplus — {provinsi} ({komoditas})")
    ax.set_xlabel("Tahun")
    ax.set_ylabel("Jumlah (ton)")
    ax.legend()
    st.pyplot(fig)

else:
    st.warning("Data terlalu sedikit untuk membuat prediksi.")

