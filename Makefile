# Makefile — короткие команды-ярлыки для частых действий.
# Запускаются так: `make up`, `make logs` и т.д.
# (На Windows для работы make может понадобиться установить его отдельно,
#  либо просто копируйте команды справа и запускайте их вручную.)

include .env

# Собрать образы и запустить все контейнеры.
up:
	docker compose up --build

# Запустить в фоне (detached).
upd:
	docker compose up --build -d

# Остановить и удалить контейнеры.
down:
	docker compose down

# Показать логи приложения в реальном времени.
logs:
	docker compose logs -f app

# Показать статус контейнеров.
ps:
	docker compose ps -a

# Перезапустить контейнеры.
restart:
	docker compose restart

# Зайти внутрь базы данных через psql.
db:
	docker compose exec -it postgres psql -U $(DB_USER) -d $(DB_NAME)
