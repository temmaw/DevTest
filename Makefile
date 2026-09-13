.PHONY: help port-forward install upgrade uninstall status logs test

help:
	@echo "make port-forward - Прокинуть порт на 8080"
	@echo "make install      - Установить чарт"
	@echo "make upgrade      - Обновить чарт"
	@echo "make uninstall    - Удалить чарт"
	@echo "make status       - Показать статус"
	@echo "make logs         - Показать логи"
	@echo "make test         - Проверить приложение"
port-forward:
	kubectl port-forward service/weather-app-service 8080:80 -n weather

install:
	helm install weather-release ./helm/weather-chart -n weather --create-namespace

upgrade:
	helm upgrade weather-release ./helm/weather-chart -n weather

uninstall:
	helm uninstall weather-release -n weather

status:
	kubectl get pods,svc,pvc,ingress,hpa -n weather

logs:
	kubectl logs -f deployment/weather-app -n weather

test:
	curl http://localhost:8000/health

