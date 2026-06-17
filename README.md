# 🧾 Sistema de Balanza API (FastAPI + Uvicorn)

Sistema de integración para balanzas industriales con lectura por USB Serial y API REST basada en FastAPI.

---

## 🚀 Características

- Lectura de balanza por `/dev/ttyUSB`
- API REST con FastAPI
- Servicio systemd para autoarranque
- Entorno virtual aislado
- Soporte para impresión ESC/POS
- Instalación automática vía script

---

## 📦 Requisitos

### Sistema operativo
- Ubuntu 20.04 / 22.04 / 24.04 (o Debian equivalente)

### Paquetes del sistema
El instalador los configura automáticamente:

- python3
- python3-pip
- python3-venv
- git
- udev

---

## ⚙️ Instalación automática (RECOMENDADO)

Ejecuta:

```bash
wget https://raw.githubusercontent.com/osolight/Balanza/main/install_balanza.sh
chmod +x install_balanza.sh
sudo ./install_balanza.sh

## 🔧 Instalación manual (modo desarrollo)
git clone https://github.com/osolight/Balanza.git
cd Balanza

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

## ▶️ Ejecutar el servicio
sudo systemctl start balanza.service
sudo systemctl status balanza.service

## 🌐 API
http://localhost:9000
