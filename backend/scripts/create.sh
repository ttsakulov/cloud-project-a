#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
REW='\033[0;31m'
NC='\033[0m'

NAME=""
TEMPLATE="lemp"
CORES=2
MEMORY=4
DISK_SIZE=20
API_URL="http://localhost:8000/api/servers"

show_help() {
	echo "Использование: $0 [ОПЦИИ]"
	echo ""
	echo "Опции:"
	echo "	-n, --name NAME		ИМЯ СЕРВЕРА (если не указано, генерируется автоматически)"
	echo "	-t, --template TEMP 	Шаблон (lemp, ml-gpu, kafka) по умолчанию lemp"
	echo "	-c, --cores NUM		Количество ядер (по умолчанию: 2)"
	echo "	-m, --memory NUM	Память в ГБ (по умолчанию: 4)"
	echo "	-d, --disk NUM		Размер диска в ГБ (по умолчанию: 20)"
	echo "	-h, --help		Показать эту помощь"
	echo ""
}

while [[ $# -gt 0 ]]; do
	case $1 in
		-n|--name)
			NAME="$2"
			shift 2
			;;
		-t|--template)
			TEMPLATE="$2"
			shift 2
			;;
		-c|--cores)
			CORES="$2"
			shift 2
			;;
		-m|--memory)
			MEMORY="$2"
			shift 2
			;;
		-d|--disk)
			DISK_SIZE="$2"
			shift 2
			;;
		-h|--help)
			show_help
			exit 0
			;;
		*)
			echo -e "${RED}Неизвестная опция: $1${NC}"
			show_help
			exit 1
			;;
	esac
done

if [ -n "$NAME" ]; then
    JSON_DATA="{\"name\":\"$NAME\",\"template\":\"$TEMPLATE\",\"cores\":$CORES,\"memory\":$MEMORY,\"disk_size\":$DISK_SIZE}"
else
    JSON_DATA="{\"template\":\"$TEMPLATE\",\"cores\":$CORES,\"memory\":$MEMORY,\"disk_size\":$DISK_SIZE}"
fi

echo "📡 Отправка запроса..."
echo "JSON: $JSON_DATA"

echo -e "${YELLOW}Отправка запроса на создание сервера...${NC}"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$JSON_DATA")

echo "Ответ: $RESPONSE"

if echo "$RESPONSE" | grep -q '"id"'; then
	echo -e "${GREEN}Сервер успешно создан!${NC}"
	echo ""

	ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
	NAME=$(echo "$RESPONSE" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
    	TEMPLATE=$(echo "$RESPONSE" | grep -o '"template":"[^"]*"' | head -1 | cut -d'"' -f4)
    	STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)

	echo "Информация о сервере:"
	echo "   ID:       $ID"
   	 echo "   Имя:      $NAME"
    	echo "   Шаблон:   $TEMPLATE"
    	echo "   Статус:   $STATUS"
    	echo ""
    	echo -e "${YELLOW} Сервер создаётся. Через 2-3 минуты проверьте статус:${NC}"
    	echo "   curl http://localhost:8000/api/servers/$ID"
else
    	echo -e "${RED} Ошибка при создании сервера${NC}"
    	echo "$RESPONSE" | grep -o '"detail":"[^"]*"' | cut -d'"' -f4
    	exit 1
fi
