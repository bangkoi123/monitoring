# File: dashboard.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import config
import mysql.connector

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Dashboard Monitoring Facebook",
    page_icon="🕵️‍♂️",
    layout="wide"
)

# --- Judul dan Deskripsi ---
st.title("🕵️‍♂️ Tools Monitoring Facebook")
st.markdown("Selamat datang! Masukkan cookie sesi Facebook Anda untuk memulai pengecekan pertumbuhan Halaman dan Grup.")

# --- Fungsi untuk mengambil data dari DB MySQL ---
def get_data_from_db():
    try:
        conn = mysql.connector.connect(
            host=st.secrets.get("DB_HOST", config.DB_HOST),
            user=st.secrets.get("DB_USER", config.DB_USER),
            password=st.secrets.get("DB_PASSWORD", config.DB_PASSWORD),
            database=st.secrets.get("DB_NAME", config.DB_NAME)
        )
        df = pd.read_sql_query("SELECT * FROM log_perkembangan", conn)
        conn.close()
        if not df.empty:
            df['tanggal_cek'] = pd.to_datetime(df['tanggal_cek'])
        return df
    except Exception as e:
        st.error(f"Gagal terhubung ke database: {e}")
        return pd.DataFrame()

# --- Langkah 1: Input Cookie dari Pengguna ---
st.header("Langkah 1: Masukkan Sesi Login Anda", divider="blue")
st.info("""
**Bagaimana cara mendapatkan cookie?**
1.  Di Browser Chrome/Firefox, install ekstensi **'EditThisCookie'**.
2.  Login ke **facebook.com** seperti biasa.
3.  Klik ikon ekstensi 'EditThisCookie', lalu klik tombol **'Export'** (panah ke kanan).
4.  Salin semua teks yang muncul dan tempel di bawah ini.
""")
cookie_input = st.text_area("Tempelkan data cookie JSON di sini", height=250, key="cookie_area")

# --- Langkah 2: Tombol untuk Menjalankan Bot ---
st.header("Langkah 2: Mulai Pengecekan", divider="blue")
if st.button("🚀 Mulai Pengecekan & Simpan Data", type="primary"):
    if cookie_input:
        st.info("Sesi diterima! Memulai proses pengecekan di latar belakang...")
        
        # Panggil fungsi-fungsi dari main_bot
        from main_bot import setup_driver, get_follower_count, save_to_db, login_with_cookies

        with st.spinner('Menyiapkan bot...'):
            driver = setup_driver()
        
        try:
            if login_with_cookies(driver, cookie_input):
                with open('targets.txt', 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                
                st.success(f"Login berhasil! Akan memproses {len(urls)} target.")
                progress_bar = st.progress(0, text=f"Memproses 0/{len(urls)}...")
                
                for i, url in enumerate(urls):
                    text_placeholder = st.empty()
                    text_placeholder.text(f"Mengunjungi: {url.split('/')[-1]}")
                    count = get_follower_count(driver, url)
                    if count is not None:
                        save_to_db(url, count)
                    progress_bar.progress((i + 1) / len(urls), text=f"Memproses {i+1}/{len(urls)}")
                
                st.success("🎉 Semua target berhasil diperiksa dan data telah disimpan!")
                st.balloons()
            else:
                st.error("Login gagal. Pastikan cookie yang Anda masukkan benar dan masih valid.")
        
        except Exception as e:
            st.error(f"Terjadi error saat menjalankan bot: {e}")

        finally:
            driver.quit()
            print("Driver ditutup.")

    else:
        st.warning("Harap masukkan data cookie terlebih dahulu.")

# --- Langkah 3: Tampilkan Laporan ---
st.header("Langkah 3: Lihat Hasil Laporan", divider="blue")

df = get_data_from_db()

if df.empty:
    st.info("Database masih kosong. Lakukan pengecekan di atas untuk melihat laporan.")
else:
    today = pd.to_datetime(date.today())
    yesterday = pd.to_datetime(date.today() - timedelta(days=1))
    unique_urls = df['target_url'].unique()
    
    st.subheader("Ringkasan Pertumbuhan Harian")
    cols = st.columns(3)
    col_index = 0
    for url in unique_urls:
        today_data = df[(df['target_url'] == url) & (df['tanggal_cek'] == today)]
        yesterday_data = df[(df['target_url'] == url) & (df['tanggal_cek'] == yesterday)]
        if not today_data.empty:
            count_today = today_data.iloc[0]['jumlah_tercatat']
            count_yesterday = yesterday_data.iloc[0]['jumlah_tercatat'] if not yesterday_data.empty else 0
            growth = count_today - count_yesterday
            with cols[col_index]:
                label = url.split('/')[-1] if 'profile.php' not in url else 'Profil ' + url.split('=')[-1]
                st.metric(label=label, value=f"{count_today:,}", delta=f"{growth:,}")
            col_index = (col_index + 1) % 3

    st.subheader("Analisis Tren & Data Historis")
    selected_url = st.selectbox("Pilih Target untuk Melihat Grafik Pertumbuhan:", unique_urls)
    if selected_url:
        chart_data = df[df['target_url'] == selected_url]
        chart_data = chart_data.set_index('tanggal_cek')
        st.line_chart(chart_data['jumlah_tercatat'], use_container_width=True)
    
    with st.expander("Lihat semua data mentah"):
        st.dataframe(df.sort_values(by=['tanggal_cek', 'target_url'], ascending=False))
