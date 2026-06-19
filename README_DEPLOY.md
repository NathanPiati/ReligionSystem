## 🚀 DEPLOY UMBANDA EM PRODUÇÃO

### ⚡ Forma rápida (recomendada)

No seu PowerShell local:

```powershell
bash enviar_para_servidor.sh root@seu_ip_servidor https://github.com/seu_usuario/seu_repositorio.git seu_dominio.com
```

### 📋 Exemplos práticos

#### Porta automática e IP
```powershell
bash enviar_para_servidor.sh root@192.168.1.100 https://github.com/NathanPiati/umbanda_system.git 192.168.1.100
```

#### Com domínio e senha personalizada
```powershell
bash enviar_para_servidor.sh root@192.168.1.100 https://github.com/NathanPiati/umbanda_system.git meudominio.com SenhaSegura123
```

### ✅ O que o script faz

✓ Instala Python3, PostgreSQL, Nginx, Gunicorn  
✓ Clona repositório GitHub  
✓ Cria virtualenv e instala dependências  
✓ Configura banco PostgreSQL  
✓ Roda migrações Django  
✓ Coleta arquivos estáticos  
✓ Configura Gunicorn com systemd  
✓ Configura Nginx como reverse proxy  
✓ Ativa firewall UFW  
✓ Deploy em PRODUÇÃO pronto para usar  

### 📊 Verificar se está funcionando

```bash
# No servidor, via SSH
ssh root@seu_ip_servidor

# Ver status do app
systemctl status umbanda

# Ver logs
journalctl -u umbanda -f

# Testar acesso
curl http://seu_dominio
```

### 🔄 Comandos após deploy

```bash
# Reiniciar app
systemctl restart umbanda

# Ver logs do Nginx
tail -f /var/log/nginx/access.log

# Atualizar código
su - umbanda
cd /var/umbanda/umbanda
git pull
exit
systemctl restart umbanda
```

### 🔐 Próximos passos (Segurança)

1. **Instalar SSL/TLS (HTTPS)**
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d seu_dominio.com
   ```

2. **Mudar senha do banco PostgreSQL**
   - Edite `/etc/systemd/system/umbanda.service`
   - Procure `DB_PASSWORD` e altere

3. **Configurar SECRET_KEY em core/settings.py**
   - Gere nova chave segura

### ⚠️ Estrutura do servidor

- **App**: `/var/umbanda/umbanda`
- **Usuário**: `umbanda`
- **Banco**: `umbanda_db`
- **Proxy**: Nginx → Gunicorn
- **Service**: systemd

