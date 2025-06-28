import streamlit as st
import pandas as pd
from datetime import date, timedelta
import config
import mysql.connector

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Laporan Monitoring Facebook",
    page_icon="📈",
    layout="wide"
)

# --- Judul Dashboard ---
st.title("📈 Laporan Pertumbuhan Facebook")
st.markdown("Laporan ini menampilkan data terbaru yang diambil oleh bot Anda.")

# --- Fungsi untuk mengambil data dari DB MySQL ---
def get_data_from_db():
    try:
        # Menggunakan secrets untuk koneksi
        conn = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"]
        )
        df = pd.read_sql_query("SELECT * FROM log_perkembangan ORDER BY tanggal_cek DESC", conn)
        conn.close()
        if not df.empty:
            df['tanggal_cek'] = pd.to_datetime(df['tanggal_cek'])
        return df
    except Exception as e:
        st.error(f"Gagal terhubung ke database: {e}")
        return pd.DataFrame()

# --- Muat dan Tampilkan Data ---
df = get_data_from_db()

if df.empty:
    st.warning("Database masih kosong atau gagal memuat data. Jalankan bot Anda terlebih dahulu.")
else:
    # Kode untuk menampilkan metrik dan grafik (sama seperti sebelumnya)
    st.header("Ringkasan Pertumbuhan Terakhir", divider="rainbow")
    
    today = pd.to_datetime(date.today())
    yesterday = pd.to_datetime(date.today() - timedelta(days=1))
    
    # Dapatkan data terakhir untuk setiap URL
    latest_df = df.loc[df.groupby('target_url')['tanggal_cek'].idxmax()]
    
    cols = st.columns(3)
    col_index = 0
    for index, row in latest_df.iterrows():
        url = row['target_url']
        count_today = row['jumlah_tercatat']
        
        # Cari data kemarin
        yesterday_data = df[(df['target_url'] == url) & (df['tanggal_cek'] == yesterday)]
        count_yesterday = yesterday_data.iloc[0]['jumlah_tercatat'] if not yesterday_data.empty else 0
        growth = count_today - count_yesterday

        with cols[col_index]:
            label = url.split('/')[-1].replace('.', ' ') if 'profile.php' not in url else 'Profil ' + url.split('=')[-1]
            st.metric(label=label, value=f"{count_today:,}", delta=f"{growth:,}")
        col_index = (col_index + 1) % 3

    # ... (Sisa kode untuk grafik dan data mentah bisa tetap sama) ...
    st.header("Analisis Tren & Data Historis", divider="gray")
    unique_urls = df['target_url'].unique()
    selected_url = st.selectbox("Pilih Target untuk Melihat Grafik Pertumbuhan:", unique_urls)
    if selected_url:
        chart_data = df[df['target_url'] == selected_url]
        chart_data = chart_data.set_index('tanggal_cek')
        st.line_chart(chart_data['jumlah_tercatat'], use_container_width=True)
    
    with st.expander("Lihat semua data mentah"):
        st.dataframe(df)
