import streamlit as st
import pkg_resources  # Library untuk memeriksa paket yang terinstal

st.set_page_config(layout="wide")

st.title("🕵️‍♂️ Alat Detektif Lingkungan Streamlit")
st.write("Laporan ini menunjukkan semua library Python yang benar-benar terinstal di server saat ini.")

# Dapatkan daftar semua paket yang terinstal
try:
    installed_packages_list = sorted([f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set])
    
    st.header("Library yang Terinstal:")
    # Tampilkan dalam beberapa kolom agar rapi
    col1, col2, col3 = st.columns(3)
    chunk_size = (len(installed_packages_list) + 2) // 3
    
    col1.write(installed_packages_list[0:chunk_size])
    col2.write(installed_packages_list[chunk_size:2*chunk_size])
    col3.write(installed_packages_list[2*chunk_size:])

    # Cek spesifik untuk mysql-connector-python
    st.header("Hasil Investigasi `mysql-connector-python`", divider="red")
    if any('mysql-connector-python' in s for s in installed_packages_list):
        st.success("✅ SUKSES: Library `mysql-connector-python` DITEMUKAN di lingkungan ini!")
    else:
        st.error("❌ GAGAL: Library `mysql-connector-python` TIDAK DITEMUKAN.")
        st.warning(
            "Ini mengonfirmasi bahwa ada masalah saat Streamlit membaca atau menginstal dari `requirements.txt`. "
            "Pastikan nama file sudah benar (`requirements.txt`) dan berada di folder utama repository GitHub Anda."
        )

except Exception as e:
    st.error(f"Terjadi error saat mencoba memeriksa library: {e}")
