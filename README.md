# Основна інформація:

1. Проект створений для отримання даних про футбольні події з сайту https://barstoolsportsbook.com
2. Отримані дані зберігаються та оновлюються в файлі output.json



## Конфігурація (settings.yaml)

```yaml
use_proxy: False # Використовувати проксі (True/False)
timeout: 10 # Таймаут (в секундах) між запитами до сайту
```
Якщо використовуються проксі, то необхідно вказати їх в файл proxies.txt в форматі `ip:port:user:pass` (по одній проксі на рядок)


## Встановлення

Для встановлення необхідно виконати наступні команди:

```bash
git clone https://github.com/barstoolsport_football_parser.git
cd barstoolsport_football_parser
pip install -r requirements.txt
python run.py
```




### Структура JSON-файлу для експорту футбольних подій

JSON-файл, створений з використанням наданих класів та функції `export_events_to_json`, має таку структуру:

```json
{
    "Назва ліги": [
        "leagueName": "NFL",
        "events": [
            {
                "id": "ідентифікатор події",
                "startDate": "час початку",
                "teams": [
                    {
                        "name": "Команда 1",
                        "score": "3",
                        "spread": "2.5",
                        "total": "45.5",
                        "moneyline": "2.00",
                        "match_spreads": [
                            {
                                "spread": "2.5",
                                "moneyline": "1.90"
                            },
                            # Інші об'єкти "match_spreads" можуть слідувати тут
                        ],
                        "total_points": [
                            {
                                "total": "45.5",
                                "moneyline": "1.85"
                            },
                            # Інші об'єкти "total_points" можуть слідувати тут
                        ]
                    },
                    {
                        "name": "Команда 2",
                        "score": "3",
                        "spread": "2.5",
                        "total": "45.5",
                        "moneyline": "2.00",
                        "match_spreads": [
                            {
                                "spread": "2.5",
                                "moneyline": "1.90"
                            },
                            # Інші об'єкти "match_spreads" можуть слідувати тут
                        ],
                        "total_points": [
                            {
                                "total": "45.5",
                                "moneyline": "1.85"
                            },
                            # Інші об'єкти "total_points" можуть слідувати тут
                        ]
                    },
                ]
            ]
        },
        # Інші події ліги
    ],
    # Інші об'єкти "Ліга"
}

