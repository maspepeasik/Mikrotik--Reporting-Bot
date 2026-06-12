# Mikrotik Telegram Reporter Bot 🤖📊

Sebuah bot Telegram berbasis Python yang dirancang khusus untuk memantau performa jaringan dan status *interface* pada router **MikroTik (khususnya seri RB5009 atau sejenisnya)** menggunakan protokol SNMP. Bot ini secara otomatis mengumpulkan data lalu lintas (traffic) harian dan mengirimkan laporan terekap ke grup Telegram Anda.

## 🚀 Fitur Utama
- **Pemantauan Otomatis (Polling)**: Menarik data CPU, RAM, Status Interface (Up/Down), dan Trafik (Byte In/Out) dari MikroTik setiap 5 menit.
- **Kalkulasi Akurat**: Secara otomatis menghitung akumulasi trafik *real-time* (selisih byte) meskipun *counter* Mikrotik mereset dirinya sendiri (menangani *64-bit integer wrap*).
- **Penyimpanan Lokal & Auto-Rotasi (SQLite)**: Semua data disimpan dengan aman ke dalam `data.db`. Untuk menghemat kapasitas server, database dikonfigurasi untuk hanya menyimpan data **maksimal 6 bulan**. Data yang usianya melewati 6 bulan akan dihapus otomatis (dirotasi) setiap jam 1 pagi.
- **Deteksi Downtime**: Menghitung dan melaporkan berapa kali sebuah *interface* mengalami *link down*.
- **Laporan Terjadwal & On-Demand**:
  - Mengirim laporan mingguan otomatis setiap hari Jumat pukul 08:00.
  - Mengirim laporan bulanan otomatis setiap tanggal 1 pukul 08:05.
  - Mendukung perintah `/report_week` dan `/report_month` langsung dari obrolan Telegram.
- **Sistem Service Bawaan**: Sudah dilengkapi *script* untuk menjadikannya *background service* di Linux/Ubuntu menggunakan `systemd`.

---

## 🛠️ Prasyarat (Prerequisites)

1. **Sistem Operasi**: Linux (Ubuntu/Debian direkomendasikan).
2. **Python**: Python 3.10 atau versi lebih baru.
3. **SNMP Tool**: Sistem Anda harus memiliki *utility* `snmpget`. 
   *(Bisa diinstall dengan: `sudo apt install snmp`)*
4. **Router MikroTik**: Fitur SNMP harus diaktifkan pada router.

---

## ⚙️ Persiapan Router MikroTik

Pastikan SNMP di MikroTik Anda sudah menyala. Jalankan perintah ini di Terminal MikroTik Anda:

```routeros
/snmp community add name="co2" addresses=0.0.0.0/0 read-access=yes write-access=no
/snmp set enabled=yes
```
*(Ganti `name="co2"` dengan nama komunitas rahasia Anda jika diperlukan)*

---

## 📥 Instalasi

**1. Masuk ke direktori pilihan Anda dan clone repository ini:**
```bash
git clone https://github.com/USERNAME_ANDA/reporting-mikrotik-bot.git
cd reporting-mikrotik-bot
```

**2. Instal lingkungan virtual (Virtual Environment) Python:**
*(Jika menggunakan Ubuntu, pastikan package `python3-venv` sudah terinstal: `sudo apt install python3.10-venv`)*
```bash
python3 -m venv venv
```

**3. Instal semua library yang dibutuhkan:**
```bash
./venv/bin/pip install -r requirements.txt
```

**4. Konfigurasi File `.env`:**
Buat atau edit file bernama `.env` di dalam folder proyek, lalu isi dengan data Anda:
```ini
TELEGRAM_BOT_TOKEN="TOKEN_BOT_TELEGRAM_ANDA"
TELEGRAM_CHAT_IDS="ID_GRUP_TELEGRAM_ANDA"
ROUTER_IP="192.168.1.1"
SNMP_COMMUNITY="co2"
POLL_INTERVAL_MINUTES=5
```

*(Catatan: Anda dapat memasukkan lebih dari satu Chat ID Telegram dengan memisahkannya menggunakan tanda koma, misal: `1234567, -987654321`)*

---

## 🧪 Pengujian (Manual Testing)

Sebelum menyalakan bot secara permanen, pastikan konfigurasi sudah benar:

**Test Koneksi SNMP ke MikroTik:**
```bash
./venv/bin/python main.py --test-snmp
```
*Output yang diharapkan: Mencetak data mentah JSON mengenai trafik.*

**Test Pengiriman Pesan Telegram:**
```bash
./venv/bin/python main.py --test-telegram
```
*Output yang diharapkan: Pesan test terkirim ke Grup Telegram Anda.*

---

## 🖥️ Menjalankan Bot sebagai Service (Ubuntu/Debian)

Agar bot terus menyala di latar belakang dan otomatis aktif saat server direstart, instal bot ini sebagai *systemd service*:

**1. Jalankan script instalasi:**
```bash
sudo bash install_service.sh
```

**2. Perintah berguna lainnya untuk memanajemen bot:**
- **Mengecek Status**: `sudo systemctl status mikrotik-reporter`
- **Melihat Log Real-time**: `sudo journalctl -u mikrotik-reporter -f`
- **Restart Bot**: `sudo systemctl restart mikrotik-reporter`
- **Menghentikan Bot**: `sudo systemctl stop mikrotik-reporter`

---

## 🗂️ Struktur Proyek
- `main.py`: File utama yang menjalankan *event loop*, jadwal (*scheduler*), dan bot Telegram.
- `snmp_poller.py`: Berisi logika *subprocess* `snmpget` untuk berkomunikasi dengan Mikrotik.
- `database.py`: Sistem pencatatan harian menggunakan SQLite (`data.db`).
- `reporter.py`: Fungsi merangkum data dari database dan merapikan format laporan ke Telegram.
- `config.py`: Sentralisasi *mapping* antarmuka (Ether1, Ether2, dsb) dan pembacaan `.env`.
- `install_service.sh`: Script instalasi otomatis *systemd service*.
