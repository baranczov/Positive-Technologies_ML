# SOC Log Clustering & Anomaly Detection Service

Сервис для автоматической кластеризации логов и выявления аномалий, разработанный в рамках тестового задания на стажировку в команду ML **Positive Technologies**.

---

## Архитектура и Выбор технологий

Проект реализован в микросервисной архитектуре и упакован в **Docker Compose**.

1. **Backend (FastAPI):** Выбран за асинхронность, высокую скорость работы, автоматическую генерацию документации (Swagger) и строгую типизацию (Pydantic). 
2. **База данных (SQLite + SQLAlchemy):** Использован ORM-подход (ООП). SQLite выбрана для обеспечения портативности тестового задания (не требует подъема тяжелого контейнера с PostgreSQL, но легко масштабируется при смене строки подключения).
3. **Frontend (Streamlit):** Выбран для быстрой реализации Web UI. Позволяет аналитикам SOC взаимодействовать с ML-моделями через удобный дашборд.
4. **ML Stack (Scikit-Learn, Joblib):** Использованы классические ML-алгоритмы для обеспечения высокой скорости инференса (ответа API) в production.

---

## ML Методология и Оценка качества

Данные для обучения взяты из открытого датасета **LogHub (Linux)**.

### 1. Предобработка (Masking)
В рамках кибербезопасности недопустимо обучать модель на сырых логах. Был реализован парсер на основе регулярных выражений, который заменяет изменяемые сущности на токены:
* `218.188.2.4` $\rightarrow$ `<IP>`
* `hinet-ip.hinet.net` $\rightarrow$ `<HOST>`
* `uid=0` $\rightarrow$ `uid=<NUM>`

### 2. Эксперименты с моделями (Выбор алгоритма)
В процессе исследования (EDA) были протестированы два подхода к кластеризации TF-IDF векторов:

* **DBSCAN (eps=0.3, cosine metric):** Показал отличный результат. Выделил 15 смысловых кластеров и 4.5% аномалий. <br> **ARI = 0.9275, Silhouette Score = 0.7821**. <br>
[https://www.kaggle.com/code/danilbarantsov/pt-ml-dbscan](https://www.kaggle.com/code/danilbarantsov/pt-ml-dbscan)
* **K-Means:** При поиске оптимального $k$ выявлена проблема переобучения на микро-шаблоны (Оптимальным значением является $k = 8$). <br> **ARI = 0.9169, Silhouette Score = 0.5594** <br>
[https://www.kaggle.com/code/danilbarantsov/pt-ml-k-means](https://www.kaggle.com/code/danilbarantsov/pt-ml-k-means)

Несмотря на превосходство DBSCAN, алгоритм не поддерживает метод `.predict()` для быстрой обработки единичных логов (требуется O(N) пересчет). Для обеспечения времени ответа API в `O(1)` в production-версию был интегрирован алгоритм **K-Means (k=8)**.
* **Качество в проде:** Silhouette Score: `0.5594`, Adjusted Rand Index (ARI): `0.9169`.

### 3. Детектирование аномалий (Anomaly Detection)
Аномалия определяется математически: вычисляется Евклидово расстояние от вектора нового лога до центроида присвоенного кластера. Если дистанция превышает 95-й перцентиль расстояний обучающей выборки (порог `0.9768`), лог маркируется флагом `is_anomaly: True`.

---

## Запуск проекта

Требования: Установленный `Docker` и `Docker Compose`.

1. Склонируйте репозиторий:
```bash
git clone https://github.com/baranczov/Positive-Technologies_ML.git
cd Positive-Technologies_ML
```

2. Запустите инфраструктуру одной командой:
```bash
docker compose up -d --build
```

3. Доступные сервисы:
* **Web UI Дашборд:** [http://localhost:8501](http://localhost:8501)
* **API Документация (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Примеры API-запросов

Сервис предоставляет REST API. Вы можете отправлять логи программно.

**Запрос (POST /clusterize):**
```bash
curl -X 'POST' \
  'http://localhost:8000/clusterize' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "log_message": "Jun 14 15:16:01 combo sshd(pam_unix)[19939]: authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4"
}'
```

**Ответ (JSON):**
```json
{
  "id": 1,
  "original_log": "Jun 14 15:16:01 combo sshd(pam_unix)[19939]: authentication failure; logname= uid=0 euid=0 tty=NODEVssh ruser= rhost=218.188.2.4",
  "cleaned_log": "jun <NUM> <NUM>:<NUM>:<NUM> combo sshd(pam_unix)[<NUM>]: authentication failure; logname= uid=<NUM> euid=<NUM> tty=nodevssh ruser= rhost=<IP>",
  "cluster_id": 2,
  "distance": 0.6609,
  "is_anomaly": false,
  "created_at": "2023-11-20T14:45:18"
}
```

---

## Интерфейс (Web UI)

*Вид Web UI*
<img width="1481" height="764" alt="Web UI" src="https://github.com/user-attachments/assets/1b8a54ef-3d5a-4396-9bd8-bc083220c049" />

*Пример обработки стандартного события авторизации.*
<img width="1474" height="812" alt="Good log" src="https://github.com/user-attachments/assets/c6230580-d5e4-40f7-b664-69544cb99083" />

*Пример выявления неизвестной аномалии (хакерской команды).*
<img width="1444" height="791" alt="Bad log" src="https://github.com/user-attachments/assets/cbbe8561-5e05-4483-82ca-023a6a10e646" />

*История событий*
<img width="1472" height="722" alt="History" src="https://github.com/user-attachments/assets/c618ebad-6a43-4789-9b79-8835be95c090" />

---

## Планы по улучшению
Если бы проект развивался дальше, я бы внедрил:
1. **Гибридный ML-пайплайн:** Использование DBSCAN в offline-режиме для эталонной разметки датасета + обучение алгоритма KNN поверх этих меток для быстрого online-инференса.
2. **LLM Naming:** Интеграция легковесной LLM (например, Llama.cpp) для автоматической генерации человекочитаемых названий кластеров вместо ID (например, `"Cluster 2"` $\rightarrow$ `"SSH Auth Failures"`).
3. **Alerting:** Интеграция вебхуков (Telegram/Slack) для мгновенного оповещения аналитиков при `is_anomaly == True`.
