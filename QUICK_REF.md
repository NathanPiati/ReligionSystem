## ⚡ GUIA RÁPIDO - DEPLOY UMBANDA

### 🎯 Objetivo
Deploy do Django Umbanda em produção no Debian com Nginx + Gunicorn + PostgreSQL

### 📝 Pré-requisitos
- Acesso SSH ao servidor como **root**
- URL do repositório GitHub
- Domínio ou IP do servidor

---

## 🚀 COMEÇAR AGORA

### Windows PowerShell:
```powershell
cd "C:\Users\Nathan Piati\Documents\Script Python novos\umbanda_system"

# Opção 1: Simples (usa defaults)
bash enviar_para_servidor.sh root@seu_ip https://github.com/seu_usuario/repo.git

# Opção 2: Com domínio
bash enviar_para_servidor.sh root@seu_ip https://github.com/seu_usuario/repo.git seu_dominio.com

# Opção 3: Com domínio e senha customizada
bash enviar_para_servidor.sh root@seu_ip https://github.com/seu_usuario/repo.git seu_dominio.com MinhaSenha123
```

### Ou execute direto no servidor (via SSH):
```bash
ssh root@seu_ip

wget https://raw.githubusercontent.com/seu_usuario/seu_repo/main/deploy_umbanda_debian.sh
chmod +x deploy_umbanda_debian.sh

./deploy_umbanda_debian.sh https://github.com/seu_usuario/seu_repo.git
```

---

## 📊 O QUE SERÁ INSTALADO

| Componente | Versão | Função |
|-----------|--------|--------|
| Python3 | 3.x | Runtime |
| PostgreSQL | latest | Banco de dados |
| Nginx | latest | Reverse proxy |
| Gunicorn | latest | Application server |
| Django | 5.2.14 | Framework |
| WhiteNoise | latest | Serve static files |

---

## ✅ VERIFICAR DEPLOY

### No servidor:
```bash
# Status do app
systemctl status umbanda

# Logs em tempo real
journalctl -u umbanda -f

# Ver quem está ouvindo as portas
netstat -tulpn | grep LISTEN

# Testar conexão
curl http://seu_ip
```

### Seu computador:
```bash
ping seu_ip
curl http://seu_ip
# Abra no navegador: http://seu_ip
```

---

## 📁 ESTRUTURA PÓS-DEPLOY

```
/var/umbanda/
├── umbanda/              (app Django)
│   ├── venv/
│   ├── core/
│   ├── management/
│   ├── static/
│   └── manage.py
└── (banco PostgreSQL)

/etc/systemd/system/
├── umbanda.service      (Gunicorn config)

/etc/nginx/sites-enabled/
└── umbanda             (Nginx config)
```

---

## 🔄 OPERAÇÕES COMUNS

### Reiniciar aplicação
```bash
systemctl restart umbanda
```

### Atualizar código
```bash
su - umbanda
cd /var/umbanda/umbanda
git pull
exit
systemctl restart umbanda
```

### Ver erros
```bash
journalctl -u umbanda -n 50
tail -f /var/log/nginx/error.log
```

### Acessar banco de dados
```bash
sudo -u postgres psql umbanda_db
```

---

## 🔐 SEGURANÇA - PRÓXIMOS PASSOS

### 1. HTTPS/SSL
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d seu_dominio.com
```

### 2. Mudar senha do banco
```bash
sudo systemctl edit umbanda
# Edite: DB_PASSWORD=nova_senha
sudo systemctl restart umbanda
```

### 3. Django SECRET_KEY
```bash
ssh root@seu_ip
su - umbanda
cd /var/umbanda/umbanda
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Copie o valor e atualize em core/settings.py
```

### 4. Backup do banco
```bash
sudo -u postgres pg_dump umbanda_db > backup.sql
```

---

## 📞 TROUBLESHOOTING

**Porta já em uso?**
```bash
lsof -i :80
# Mata processo: kill -9 PID
```

**Erro de permissão?**
```bash
sudo chown -R umbanda:umbanda /var/umbanda/umbanda
```

**App não inicia?**
```bash
systemctl status umbanda
journalctl -u umbanda --no-pager
```

**Nginx erro?**
```bash
nginx -t
systemctl restart nginx
```

---

## 💾 VARIÁVEIS DE AMBIENTE DO SCRIPT

| Var | Default | Descrição |
|-----|---------|-----------|
| APP_NAME | umbanda | Nome do serviço |
| BASE_DIR | /var/umbanda | Diretório base |
| DB_NAME | umbanda_db | Nome banco |
| DB_USER | umbanda_user | Usuário banco |
| DB_PASS | UmbandaP@55 | Senha banco |
| DOMAIN | localhost | Domínio/IP |

---

## 📚 ARQUIVOS PRINCIPAIS

- `deploy_umbanda_debian.sh` - Script de instalação/setup
- `enviar_para_servidor.sh` - Wrapper para executar via SSH
- `README_DEPLOY.md` - Documentação completa
- `DEPLOY_INSTRUCOES.md` - Guia detalhado
- `QUICK_REF.md` - Este arquivo (referência rápida)
