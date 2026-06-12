#!/bin/bash

# Pastikan script dijalankan sebagai root (menggunakan sudo)
if [ "$EUID" -ne 0 ]; then
  echo "Harap jalankan script ini menggunakan sudo: sudo bash install_service.sh"
  exit
fi

SERVICE_NAME="mikrotik-reporter"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
USER="user"
WORK_DIR="project_directory"
PYTHON_BIN="${WORK_DIR}/venv/bin/python"

echo "Membuat file konfigurasi systemd di ${SERVICE_FILE}..."

cat <<EOF > ${SERVICE_FILE}
[Unit]
Description=Mikrotik Telegram Reporter Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${WORK_DIR}
# Gunakan tanda kutip pada ExecStart karena ada spasi pada path direktori
ExecStart="${PYTHON_BIN}" main.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=mikrotik-reporter

[Install]
WantedBy=multi-user.target
EOF

echo "Konfigurasi berhasil dibuat!"

# Reload systemd untuk mengenali file service baru
echo "Me-reload systemd daemon..."
systemctl daemon-reload

# Mengaktifkan service agar otomatis menyala saat server direstart (boot)
echo "Mengaktifkan service (enable)..."
systemctl enable ${SERVICE_NAME}

# Menyalakan service sekarang juga
echo "Menyalakan service (start)..."
systemctl start ${SERVICE_NAME}

echo "================================================="
echo "✅ Instalasi Selesai!"
echo "Bot Anda sekarang berjalan sebagai systemd service."
echo ""
echo "Untuk melihat status bot, gunakan:"
echo "sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "Untuk melihat log error/output secara real-time, gunakan:"
echo "sudo journalctl -u ${SERVICE_NAME} -f"
echo "================================================="
