# File: main_bot.py
import time
import random
import json
from datetime import date
import mysql.connector
from mysql.connector import Error

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

import config

def get_db_connection():
    """Membuat koneksi ke database MySQL."""
    try:
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error saat terhubung ke MySQL: {e}")
        return None

def setup_database():
    """Membuat tabel di database jika belum ada. Dijalankan sekali."""
    conn = get_db_connection()
    if conn is None: 
        print("Koneksi DB gagal, setup dibatalkan.")
        return
    
    cursor = conn.cursor()
    print("Membuat tabel 'log_perkembangan' jika belum ada...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS log_perkembangan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            target_url VARCHAR(255) NOT NULL,
            jumlah_tercatat INT NOT NULL,
            tanggal_cek DATE NOT NULL,
            UNIQUE KEY unique_entry (target_url, tanggal_cek)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()
    print("Setup database MySQL berhasil.")

def save_to_db(url, count):
    """Menyimpan atau memperbarui data ke database MySQL untuk hari ini."""
    conn = get_db_connection()
    if conn is None: return

    cursor = conn.cursor()
    today = date.today()
    # Coba update dulu jika data hari ini sudah ada, jika tidak ada, baru insert
    # Ini untuk mencegah duplikasi jika bot dijalankan lebih dari sekali sehari
    query = """
    INSERT INTO log_perkembangan (target_url, jumlah_tercatat, tanggal_cek) 
    VALUES (%s, %s, %s) 
    ON DUPLICATE KEY UPDATE jumlah_tercatat = VALUES(jumlah_tercatat)
    """
    values = (url, count, today)
    
    cursor.execute(query, values)
    conn.commit()
    
    cursor.close()
    conn.close()
    print(f"Data disimpan ke MySQL: {url} - {count}")

def setup_driver():
    """Menyiapkan driver Chrome dengan opsi yang diperlukan."""
    chrome_options = Options()
    # Opsi ini penting agar bisa berjalan di server/streamlit cloud
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service() 
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login_with_cookies(driver, cookies_string):
    """Fungsi untuk login ke Facebook menggunakan data cookie."""
    print("Mencoba login dengan cookie...")
    driver.get("https://www.facebook.com")
    
    try:
        cookies = json.loads(cookies_string)
    except json.JSONDecodeError:
        print("Error: Format cookie JSON tidak valid.")
        return False

    for cookie in cookies:
        if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
            del cookie['sameSite']
        driver.add_cookie(cookie)
    
    driver.refresh()
    time.sleep(5)
    
    if "Facebook" in driver.title and "Log in" not in driver.title:
        print("Login dengan cookie berhasil.")
        return True
    else:
        print("Gagal login dengan cookie. Coba perbarui cookie Anda.")
        return False

def get_follower_count(driver, url):
    """Mengunjungi URL target dan mengambil jumlah pengikut/anggota."""
    print(f"Mengunjungi: {url}")
    driver.get(url)
    time.sleep(random.uniform(3, 7))

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    try:
        # Mencari angka detail di dalam link yang mengandung kata kunci
        keywords = ['followers', 'members', 'pengikut', 'anggota', 'suka', 'likes']
        target_element = soup.find(lambda tag: tag.name == 'a' and any(keyword in tag.text.lower() for keyword in keywords))
        
        if target_element:
            full_text = target_element.text
            numbers = ''.join(filter(str.isdigit, full_text))
            if numbers:
                print(f"Angka ditemukan: {numbers}")
                return int(numbers)
        
        print("Gagal menemukan jumlah pengikut/anggota dengan metode pertama. Mencoba metode kedua...")
        # Metode kedua jika pertama gagal: cari semua teks dan temukan yang paling relevan
        all_text = soup.get_text(" ", strip=True)
        # Ini adalah contoh pencarian sederhana, bisa dikembangkan lebih lanjut
        for word in all_text.split():
            if 'K' in word.upper() or 'RB' in word.upper() or 'M' in word.upper() or 'JT' in word.upper():
                # Logika untuk mengubah '50K' atau '32rb' menjadi angka
                num_part = word.upper().replace('RB', 'K').replace('JT', 'M')
                if 'K' in num_part:
                    return int(float(num_part.replace('K','').replace(',','.')) * 1000)
                if 'M' in num_part:
                    return int(float(num_part.replace('M','').replace(',','.')) * 1000000)

        print("Gagal menemukan jumlah pengikut/anggota.")
        return None

    except Exception as e:
        print(f"Error saat scraping: {e}")
        return None

# Fungsi ini bisa dijalankan terpisah jika mau, tapi sekarang kita panggil dari dashboard
if __name__ == "__main__":
    # Jalankan ini untuk membuat tabel di database untuk pertama kali
    print("Menjalankan setup database mandiri...")
    setup_database()
