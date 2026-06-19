## 📋 INSTRUÇÕES PARA DEPLOY NO SERVIDOR DEBIAN

### Pré-requisitos
- SSH acesso ao servidor como root
- URL do repositório GitHub
- (Opcional) Preferência por porta específica

---

## ✅ OPÇÃO 1: Transferir arquivo via SCP

### Passo 1: Copiar script para o servidor
```bash
scp deploy_umbanda_debian.sh root@seu_ip_servidor:/tmp/
```

### Passo 2: Conectar ao servidor
```bash
ssh root@seu_ip_servidor
```

### Passo 3: Executar o script
```bash
chmod +x /tmp/deploy_umbanda_debian.sh

# Execução com porta automática (recomendado)
/tmp/deploy_umbanda_debian.sh https://github.com/seu_usuario/seu_repositorio.git

# OU com todas as opções personalizadas
/tmp/deploy_umbanda_debian.sh \
  https://github.com/seu_usuario/seu_repositorio.git \
  /home/umbanda_app \
  8001 \
  umbanda_db \
  umbanda_user \
  SuaSenhaSegura123 \
  localhost \
  5432 \
  umbanda_app
```

---

## ✅ OPÇÃO 2: Criar arquivo diretamente no servidor

### Passo 1: Conectar ao servidor
```bash
ssh root@seu_ip_servidor
```

### Passo 2: Criar o arquivo
```bash
cat > /tmp/deploy_umbanda_debian.sh << 'ENDSCRIPT'
[COPIE E COLE TODO O CONTEÚDO DO deploy_umbanda_debian.sh AQUI]
ENDSCRIPT
```

### Passo 3: Executar
```bash
chmod +x /tmp/deploy_umbanda_debian.sh
/tmp/deploy_umbanda_debian.sh https://github.com/seu_usuario/seu_repositorio.git
```

---

## 📊 PARÂMETROS DO SCRIPT

| Posição | Variável | Padrão | Descrição |
|---------|----------|--------|-----------|
| 1 | REPO_URL | *obrigatório* | URL do repositório GitHub |
| 2 | APP_DIR | /home/umbanda_app | Diretório de instalação |
| 3 | PORT | auto | Porta da aplicação (deixar em branco = automática) |
| 4 | DB_NAME | umbanda_db | Nome do banco PostgreSQL |
| 5 | DB_USER | umbanda_user | Usuário do PostgreSQL |
| 6 | DB_PASSWORD | UmbandaP@55 | Senha do PostgreSQL |
| 7 | DB_HOST | localhost | Host do PostgreSQL |
| 8 | DB_PORT | 5432 | Porta do PostgreSQL |
| 9 | SERVICE_NAME | umbanda_app | Nome do serviço systemd |
| 10 | RUN_USER | root | Usuário que executa o app |

---

## 🔍 VERIFICAR SE FUNCIONOU

Após a execução, no servidor execute:

```bash
# Ver status do serviço
systemctl status umbanda_app

# Ver logs da aplicação
journalctl -u umbanda_app -f

# Listar porta em uso
ss -tulpn | grep 800

# Testar acesso
curl http://localhost:8001/
```

---

## 🛠️ COMANDOS ÚTEIS APÓS DEPLOY

```bash
# Reiniciar o app
systemctl restart umbanda_app

# Parar o app
systemctl stop umbanda_app

# Iniciar o app
systemctl start umbanda_app

# Ver variáveis de ambiente do app
cat /home/umbanda_app/.env

# Atualizar código do repositório
cd /home/umbanda_app
git pull
systemctl restart umbanda_app
```

---

## ❓ DÚVIDAS COMUNS

**P: Como faço se esquecer de qual porta está rodando?**
R: Execute `ss -tulpn | grep LISTEN` para ver todas as portas em uso.

**P: Posso usar outro banco de dados além de PostgreSQL?**
R: O script é específico para PostgreSQL, mas o Django também suporta MySQL, Oracle, etc. Precisaríamos ajustar o script.

**P: E se der erro de permissão?**
R: Certifique-se de executar o script com `sudo` ou sendo root.

**P: Como faço para rodar em produção com HTTPS?**
R: Use um reverse proxy como Nginx + Certbot. Posso criar um script adicional para isso.
