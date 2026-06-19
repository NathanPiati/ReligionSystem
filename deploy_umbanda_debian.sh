#!/bin/bash
set -e

# ============================================
# VARIÁVEIS (ajuste conforme necessário)
# ============================================
APP_NAME="umbanda"
BASE_DIR="/var/umbanda"
APP_DIR="$BASE_DIR/$APP_NAME"
REPO_URL="${1:-https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git}"
APP_USER="umbanda"
DB_NAME="umbanda_db"
DB_USER="umbanda_user"
DB_PASS="${2:-UmbandaP@55}"
DOMAIN="${3:-localhost}"

if [ "$EUID" -ne 0 ]; then
  echo "⚠️  Execute este script como root: sudo ./deploy_umbanda_debian.sh <repo_url> [db_password] [domain]"
  exit 1
fi

echo "=================================="
echo "🚀 Deploy Umbanda em Produção"
echo "=================================="

echo ""
echo "1️⃣  Atualizando sistema..."
apt update -y && apt upgrade -y

echo ""
echo "2️⃣  Instalando pacotes essenciais..."
apt install -y python3 python3-venv python3-pip python3-dev build-essential git nginx postgresql postgresql-contrib libpq-dev ufw supervisor

echo ""
echo "3️⃣  Criando usuário do app..."
adduser --disabled-password --gecos "" $APP_USER 2>/dev/null || echo "   Usuário $APP_USER já existe"
usermod -aG sudo $APP_USER 2>/dev/null || true

echo ""
echo "4️⃣  Criando diretório do projeto..."
mkdir -p $BASE_DIR
chown -R $APP_USER:$APP_USER $BASE_DIR

echo ""
echo "5️⃣  Clonando repositório..."
su - $APP_USER -c "
  cd $BASE_DIR
  if [ ! -d $APP_NAME ]; then
    git clone $REPO_URL $APP_NAME
  else
    cd $APP_NAME
    git pull
  fi
"

echo ""
echo "6️⃣  Configurando virtualenv e dependências..."
su - $APP_USER -c "
  cd $APP_DIR
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install django psycopg2-binary dj-database-url gunicorn whitenoise
"

echo ""
echo "7️⃣  Configurando PostgreSQL..."
sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
DROP USER IF EXISTS $DB_USER;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo ""
echo "8️⃣  Ajustando settings.py para produção..."
cd $APP_DIR
if grep -q "^ALLOWED_HOSTS = \[\]" core/settings.py; then
  sed -i "s|^ALLOWED_HOSTS = \[\]|ALLOWED_HOSTS = ['$DOMAIN', 'localhost', '127.0.0.1']|" core/settings.py
fi

if grep -q "^DEBUG = True" core/settings.py; then
  sed -i "s|^DEBUG = True|DEBUG = False|" core/settings.py
fi

if ! grep -q "USE_SQLITE" core/settings.py; then
  sed -i "/if os.environ.get/a USE_SQLITE = os.environ.get('USE_SQLITE', 'False') == 'True'" core/settings.py
fi

echo ""
echo "9️⃣  Rodando migrações..."
su - $APP_USER -c "
  cd $APP_DIR
  source venv/bin/activate
  export DB_NAME=$DB_NAME
  export DB_USER=$DB_USER
  export DB_PASSWORD=$DB_PASS
  export DB_HOST=localhost
  export DB_PORT=5432
  export USE_SQLITE=False
  python manage.py migrate
  python manage.py collectstatic --noinput
"

echo ""
echo "🔟 Configurando Gunicorn..."
cat > /etc/systemd/system/$APP_NAME.service <<EOL
[Unit]
Description=Gunicorn para $APP_NAME
After=network.target

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
Environment="DB_NAME=$DB_NAME"
Environment="DB_USER=$DB_USER"
Environment="DB_PASSWORD=$DB_PASS"
Environment="DB_HOST=localhost"
Environment="DB_PORT=5432"
Environment="USE_SQLITE=False"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:/run/$APP_NAME.sock core.wsgi:application

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl enable $APP_NAME
systemctl start $APP_NAME

echo ""
echo "1️⃣1️⃣  Configurando Nginx..."
mkdir -p $APP_DIR/static
cat > /etc/nginx/sites-available/$APP_NAME <<EOL
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 20M;

    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
    }

    location /media/ {
        alias $APP_DIR/media/;
    }

    location / {
        proxy_pass http://unix:/run/$APP_NAME.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
EOL

ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo "1️⃣2️⃣  Configurando firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ""
echo "✅ Deploy finalizado!"
echo ""
echo "=================================="
echo "📊 INFORMAÇÕES DO DEPLOY"
echo "=================================="
echo "App Name: $APP_NAME"
echo "App Dir: $APP_DIR"
echo "Domain: $DOMAIN"
echo "DB: $DB_NAME"
echo "DB User: $DB_USER"
echo "URL: http://$DOMAIN"
echo ""
echo "🔧 Comandos úteis:"
echo "   systemctl status $APP_NAME"
echo "   systemctl restart $APP_NAME"
echo "   journalctl -u $APP_NAME -f"
echo "   tail -f /var/log/nginx/access.log"
echo ""
echo "🔐 Considerações de segurança:"
echo "   ✓ Instale SSL com: certbot --nginx -d $DOMAIN"
echo "   ✓ Mude DB_PASS em /etc/systemd/system/$APP_NAME.service"
echo "   ✓ Configure SECRET_KEY em core/settings.py"
echo ""
