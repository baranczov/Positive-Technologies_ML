from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Импортируем наши модули
from app.database import engine, get_db, Base
from app import models, schemas
from app.ml_service import ml_service

# Создаем таблицы в базе данных (если их еще нет)
# Это супер-удобная фича SQLAlchemy
models.Base.metadata.create_all(bind=engine)

# Инициализируем FastAPI приложение
app = FastAPI(
    title="SOC Log Clustering API",
    description="Сервис для автоматической кластеризации логов и выявления аномалий для аналитиков SOC.",
    version="1.0.0"
)

@app.post("/clusterize", response_model=schemas.LogResponse)
def clusterize_log(request: schemas.LogRequest, db: Session = Depends(get_db)):
    """
    Эндпоинт для обработки одного нового лога.
    Принимает сырой текст, прогоняет через ML-модель и сохраняет результат в БД.
    """
    if not request.log_message.strip():
        raise HTTPException(status_code=400, detail="Лог не может быть пустым")

    # 1. Прогоняем лог через наш ML сервис
    ml_result = ml_service.process_log(request.log_message)

    # 2. Создаем запись для базы данных (ORM модель)
    db_log = models.LogEvent(
        original_log=request.log_message,
        cleaned_log=ml_result["cleaned_log"],
        cluster_id=ml_result["cluster_id"],
        distance=ml_result["distance"],
        is_anomaly=ml_result["is_anomaly"]
    )

    # 3. Сохраняем в базу SQLite
    db.add(db_log)
    db.commit()
    db.refresh(db_log) # Обновляем объект, чтобы получить его ID из базы

    # 4. Возвращаем ответ пользователю
    return db_log

@app.get("/logs", response_model=List[schemas.LogResponse])
def get_all_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Эндпоинт для получения истории логов из базы данных.
    Полезно для будущего Web UI или дашбордов аналитиков.
    """
    logs = db.query(models.LogEvent).offset(skip).limit(limit).all()
    return logs

@app.get("/health")
def health_check():
    """
    Эндпоинт для проверки, что сервис жив.
    """
    return {"status": "ok", "ml_threshold": ml_service.threshold}