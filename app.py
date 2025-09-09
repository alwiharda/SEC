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
    fitur = [f for f in fitur if f.lower() in [c.lower() for c in df_in.columns]]

    # samakan nama kolom (lowercase)
    df_in = df_in.rename(columns={c: c.lower() for c in df_in.columns})
    target_col = target_col.lower()
    fitur = [f.lower() for f in fitur]

    X = df_in[fitur]
    y = df_in[target_col]

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    model.fit(X, y)

    # buat data prediksi 3 tahun ke depan
    tahun_max = int(df_in["tahun"].max())
    pred_rows = []
    for i in range(1, n_forecast + 1):
        tahun_next = tahun_max + i
        # ambil data terakhir untuk variabel selain tahun
        last_row = df_in.iloc[-1].to_dict()
        row_pred = {k: last_row[k] for k in fitur if k != "tahun"}
        row_pred["tahun"] = tahun_next
        pred_rows.append(row_pred)

    X_pred = pd.DataFrame(pred_rows)
    y_pred = model.predict(X_pred)

    df_pred = X_pred.copy()
    df_pred[target_col] = y_pred
    return df_pred, model

# ==========================================================
# Aplikasi Streamlit
# ==========================================================
st.set_page_config(page_title="Prediksi Surplus Pangan", layout="wide")
st.title("📊 Prediksi Produksi, Konsumsi & Surplus Pangan")

# upload file
uploaded_file = st.file_uploader("Upload data (prediksi_permintaan.xlsx)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Data berhasil diupload!")
    st.dataframe(df.head())

    # pilih provinsi & komoditas
    provinsi = st.selectbox("Pilih Provinsi", sorted(df["Provinsi"].unique()))
    komoditas = st.selectbox("Pilih Komoditas", sorted(df["Komoditas"].unique()))

    df_filtered = df[(df["Provinsi"] == provinsi) & (df["Komoditas"] == komoditas)].copy()

    if len(df_filtered) > 3:
        # training produksi & konsumsi
        df_pred_prod, model_prod = train_and_forecast(df_filtered, "produksi", n_forecast=3)
        df_pred_kons, model_kons = train_and_forecast(df_filtered, "konsumsi (ton)", n_forecast=3)

        # gabungkan hasil prediksi
        df_forecast = pd.DataFrame({
            "Tahun": df_pred_prod["tahun"],
            "Produksi": df_pred_prod["produksi"],
            "Konsumsi": df_pred_kons["konsumsi (ton)"]
        })
        df_forecast["Surplus"] = df_forecast["Produksi"] - df_forecast["Konsumsi"]

        # gabung data asli + prediksi
        df_show = pd.concat([
            df_filtered.rename(columns={"produksi": "Produksi", "konsumsi (ton)": "Konsumsi"}),
            df_forecast
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

        # garis prediksi
        tahun_max = df_filtered["Tahun"].max()
        ax.axvline(x=tahun_max + 1, color="red", linestyle="--", label="Prediksi dimulai")

        ax.set_title(f"Data & Prediksi Surplus — {provinsi} ({komoditas})")
        ax.set_xlabel("Tahun")
        ax.set_ylabel("Jumlah (ton)")
        ax.legend()
        st.pyplot(fig)

    else:
        st.warning("Data terlalu sedikit untuk membuat prediksi.")

else:
    st.info("Silakan upload file data terlebih dahulu.")
