#!/bin/bash
# Script para verificar seguridad antes de commit

echo "🔍 Verificando seguridad del repositorio..."
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# 1. Verificar que .env no esté trackeado
echo "1. Verificando archivo .env..."
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo -e "${RED}❌ ERROR: .env está trackeado en git!${NC}"
    echo "   Ejecuta: git rm --cached .env"
    ERRORS=$((ERRORS+1))
else
    echo -e "${GREEN}✅ .env NO está trackeado${NC}"
fi

# 2. Buscar archivos .pem, .key
echo ""
echo "2. Buscando archivos de claves privadas..."
KEYS=$(git ls-files | grep -E "\.(pem|key|p12|pfx)$")
if [ ! -z "$KEYS" ]; then
    echo -e "${RED}❌ ERROR: Archivos de claves encontrados:${NC}"
    echo "$KEYS"
    ERRORS=$((ERRORS+1))
else
    echo -e "${GREEN}✅ No hay archivos de claves trackeados${NC}"
fi

# 3. Buscar credenciales en archivos
echo ""
echo "3. Buscando credenciales hardcodeadas..."
CREDS=$(git grep -i -E "aws_access_key|aws_secret|password.*=.*['\"]|secret_key.*=.*['\"]" -- '*.py' | grep -v "config(" | grep -v ".env" | grep -v "# " || true)
if [ ! -z "$CREDS" ]; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: Posibles credenciales encontradas:${NC}"
    echo "$CREDS"
    echo "   Verifica que sean variables de entorno, no valores reales"
else
    echo -e "${GREEN}✅ No se encontraron credenciales hardcodeadas${NC}"
fi

# 4. Verificar que .gitignore existe
echo ""
echo "4. Verificando .gitignore..."
if [ ! -f .gitignore ]; then
    echo -e "${RED}❌ ERROR: .gitignore no existe!${NC}"
    ERRORS=$((ERRORS+1))
else
    echo -e "${GREEN}✅ .gitignore existe${NC}"
fi

# 5. Verificar archivos .log
echo ""
echo "5. Verificando archivos .log..."
LOGS=$(git ls-files | grep "\.log$")
if [ ! -z "$LOGS" ]; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: Archivos .log trackeados:${NC}"
    echo "$LOGS"
    echo "   Los logs no deberían estar en git"
else
    echo -e "${GREEN}✅ No hay archivos .log trackeados${NC}"
fi

# 6. Verificar dumps de base de datos
echo ""
echo "6. Verificando dumps de base de datos..."
DUMPS=$(git ls-files | grep -E "\.(sql|dump|backup)$")
if [ ! -z "$DUMPS" ]; then
    echo -e "${RED}❌ ERROR: Dumps de base de datos encontrados:${NC}"
    echo "$DUMPS"
    ERRORS=$((ERRORS+1))
else
    echo -e "${GREEN}✅ No hay dumps de base de datos trackeados${NC}"
fi

# Resumen
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ TODO CORRECTO - Puedes hacer commit de forma segura${NC}"
    exit 0
else
    echo -e "${RED}❌ ERRORES ENCONTRADOS ($ERRORS)${NC}"
    echo "   Por favor, corrige los errores antes de hacer commit"
    exit 1
fi
