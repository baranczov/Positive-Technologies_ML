import joblib
import re
import numpy as np
import os

class LogClusterer:
    def __init__(self, model_dir="ml_models"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_model_dir = os.path.join(base_dir, model_dir)
        
        try:
            self.vectorizer = joblib.load(os.path.join(full_model_dir, "vectorizer.pkl"))
            self.kmeans = joblib.load(os.path.join(full_model_dir, "kmeans_model.pkl"))
            with open(os.path.join(full_model_dir, "anomaly_threshold.txt"), "r") as f:
                self.threshold = float(f.read().strip())
        except Exception as e:
            print(f"Ошибка загрузки ML моделей.")
            raise e

    def _clean_log(self, text: str) -> str:
        """Приватный метод для очистки лога (Инкапсуляция)"""
        text = str(text).lower()
        text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '<IP>', text)
        text = re.sub(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', '<HOST>', text)
        text = re.sub(r'\b\d+\b', '<NUM>', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def process_log(self, raw_log: str) -> dict:
        """
        Основной метод: принимает сырой лог, чистит, векторизует, 
        кластеризует и проверяет на аномальность.
        """
        cleaned = self._clean_log(raw_log)
        
        vectorized = self.vectorizer.transform([cleaned])
        
        cluster_id = int(self.kmeans.predict(vectorized)[0])
        
        cluster_center = self.kmeans.cluster_centers_[cluster_id]
        distance = float(np.linalg.norm(vectorized.toarray()[0] - cluster_center))
        is_anomaly = bool(distance > self.threshold)
        
        return {
            "cleaned_log": cleaned,
            "cluster_id": cluster_id,
            "distance": distance,
            "is_anomaly": is_anomaly
        }

ml_service = LogClusterer()