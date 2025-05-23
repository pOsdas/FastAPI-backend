# Redis
Функция `get_auth_user_username` использует Redis для отслеживания неудачных попыток входа
и защиты от угадывания пароля, одновременно снижая нагрузку на сервер
## Установка и запуск Redis в Windows (через Docker)
1. скачать и запустить redis в контейнере
```shell
docker run -d --name redis -p 6379:6379 redis
```
2. проверка (ожидаем получить информацию о контейнере)
```shell
docker ps
```
3. подключение к redis
```shell
docker exec -it redis redis-cli
```
4. проверка (ожидаем получить `PONG`)
```shell
ping
```
### Автозапуск:
```shell
docker update --restart unless-stopped redis
```

# Дополнительно
📌 Документация Redis: [redis.io](https://redis.io/)\
📌 Документация Docker: [docs.docker.com](https://docs.docker.com/)