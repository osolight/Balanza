#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/Balanza"
APP_REPO="https://github.com/osolight/Balanza.git"
APP_USER="balanza"
APP_GROUP="balanza"
ADMIN_USER="baloo"
SERVICE_NAME="balanza.service"
TIMEZONE="America/Caracas"
LOCALE_NAME="es_VE.UTF-8"
PORT="9000"

echo "== Instalador automático de Balanza =="

if [[ "$EUID" -ne 0 ]]; then
    echo "ERROR: Ejecuta este script como root."
    echo "Ejemplo: sudo bash install_balanza.sh"
    exit 1
fi

echo "== 1. Creando usuario administrador ${ADMIN_USER} si no existe =="

if ! id "$ADMIN_USER" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" "$ADMIN_USER"
    echo "Usuario ${ADMIN_USER} creado sin clave."
    echo "Luego puedes asignarle clave con: passwd ${ADMIN_USER}"
else
    echo "Usuario ${ADMIN_USER} ya existe."
fi

usermod -aG sudo "$ADMIN_USER"

echo "== 2. Configurando zona horaria y locale =="

timedatectl set-timezone "$TIMEZONE" || {
    ln -sf "/usr/share/zoneinfo/${TIMEZONE}" /etc/localtime
}

apt update
apt install -y locales

if ! grep -q "^${LOCALE_NAME} UTF-8" /etc/locale.gen; then
    echo "${LOCALE_NAME} UTF-8" >> /etc/locale.gen
fi

locale-gen "$LOCALE_NAME"
update-locale LANG="$LOCALE_NAME" LANGUAGE="$LOCALE_NAME" LC_ALL="$LOCALE_NAME"

echo "== 3. Actualizando sistema e instalando paquetes base =="

apt update
DEBIAN_FRONTEND=noninteractive apt full-upgrade -y

apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    ca-certificates

echo "== 4. Creando usuario/grupo de servicio ${APP_USER} =="

if ! getent group "$APP_GROUP" >/dev/null; then
    groupadd --system "$APP_GROUP"
fi

if ! id "$APP_USER" >/dev/null 2>&1; then
    useradd \
        --system \
        --gid "$APP_GROUP" \
        --home-dir "$APP_DIR" \
        --shell /usr/sbin/nologin \
        "$APP_USER"
fi

echo "== 5. Descargando o actualizando aplicación desde GitHub =="

if [[ -d "$APP_DIR/.git" ]]; then
    echo "Repositorio ya existe. Actualizando..."
    git -C "$APP_DIR" pull
else
    rm -rf "$APP_DIR"
    git clone "$APP_REPO" "$APP_DIR"
fi

chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

echo "== 6. Creando entorno virtual Python =="

if [[ ! -d "$APP_DIR/venv" ]]; then
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
fi

"$APP_DIR/venv/bin/pip" install --upgrade pip setuptools wheel

if [[ -f "$APP_DIR/requirements.txt" ]]; then
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
else
    "$APP_DIR/venv/bin/pip" install \
        uvicorn \
        gunicorn \
        fastapi \
        pyserial \
        python-escpos \
        setuptools
fi

chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

echo "== 7. Configurando permisos USB Serial /dev/ttyUSB* =="

cat > /etc/udev/rules.d/99-usb-serial-balanza.rules <<EOF
KERNEL=="ttyUSB*", GROUP="${APP_GROUP}", MODE="0660"
EOF

udevadm control --reload-rules
udevadm trigger || true

echo "== 8. Creando servicio systemd =="

cat > "/etc/systemd/system/${SERVICE_NAME}" <<EOF
[Unit]
Description=Servicio API Bascula con Uvicorn
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${APP_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${APP_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "== 9. Estado del servicio =="

systemctl --no-pager status "$SERVICE_NAME" || true

echo
echo "== Instalación terminada =="
echo "API escuchando en puerto ${PORT}"
echo
echo "Comandos útiles:"
echo "  systemctl status ${SERVICE_NAME}"
echo "  journalctl -u ${SERVICE_NAME} -f"
echo "  ss -ltnp | grep :${PORT}"
echo "  ls -l /dev/ttyUSB*"
echo
echo "Si creaste por primera vez el usuario ${ADMIN_USER}, asigna clave con:"
echo "  passwd ${ADMIN_USER}"
