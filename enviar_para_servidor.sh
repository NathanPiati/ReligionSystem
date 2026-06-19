#!/bin/bash

# Script para transferir e executar o deploy automaticamente
# Uso: ./enviar_para_servidor.sh <usuario@host> <url_repositorio> [domain] [db_password]

if [ $# -lt 2 ]; then
  echo "❌ Parâmetros insuficientes"
  echo ""
  echo "Uso: $0 <usuario@host> <url_repositorio> [domain] [db_password]"
  echo ""
  echo "Exemplos:"
  echo "  $0 root@192.168.1.100 https://github.com/seu_usuario/seu_repo.git"
  echo "  $0 root@192.168.1.100 https://github.com/seu_usuario/seu_repo.git seu_dominio.com"
  echo "  $0 root@192.168.1.100 https://github.com/seu_usuario/seu_repo.git seu_dominio.com SenhaSegura123"
  exit 1
fi

SERVER="$1"
REPO_URL="$2"
DOMAIN="${3:-localhost}"
DB_PASS="${4:-UmbandaP@55}"
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/deploy_umbanda_debian.sh"

if [ ! -f "$SCRIPT_PATH" ]; then
  echo "❌ Erro: deploy_umbanda_debian.sh não encontrado em $SCRIPT_PATH"
  exit 1
fi

echo "=========================================="
echo "📤 ENVIANDO DEPLOY PARA O SERVIDOR"
echo "=========================================="
echo ""
echo "Servidor: $SERVER"
echo "Repo: $REPO_URL"
echo "Domain: $DOMAIN"
echo ""

echo "🔄 Transferindo script..."
scp "$SCRIPT_PATH" "$SERVER:/tmp/"

if [ $? -ne 0 ]; then
  echo "❌ Erro ao transferir arquivo via SCP"
  exit 1
fi

echo "✅ Script transferido"
echo ""
echo "🚀 Executando deploy no servidor..."
echo ""

ssh "$SERVER" "chmod +x /tmp/deploy_umbanda_debian.sh && /tmp/deploy_umbanda_debian.sh '$REPO_URL' '$DB_PASS' '$DOMAIN'"

if [ $? -eq 0 ]; then
  echo ""
  echo "=========================================="
  echo "✅ DEPLOY CONCLUÍDO COM SUCESSO!"
  echo "=========================================="
  echo ""
  echo "🌐 Acesse: http://$DOMAIN"
  echo ""
  echo "📊 Para verificar o status:"
  echo "   ssh $SERVER"
  echo "   systemctl status umbanda"
  echo "   journalctl -u umbanda -f"
  echo ""
else
  echo ""
  echo "❌ ERRO DURANTE O DEPLOY"
  echo "Para mais detalhes, conecte ao servidor e veja os logs:"
  echo "   ssh $SERVER"
  echo "   journalctl -u umbanda -n 100"
  exit 1
fi
