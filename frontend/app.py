import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="SOC Log Analyzer",
    page_icon="🛡️",
    layout="wide"
)

API_URL = "http://soc-api:8000"

st.title("SOC Log Analyzer & Anomaly Detection")
st.markdown("Сервис автоматической кластеризации логов и выявления аномалий для аналитиков SOC.")

st.header("Анализ нового события")
with st.form("log_form"):
    log_input = st.text_area("Вставьте сырой лог сюда:", height=100, 
                             placeholder="Например: Jun 14 15:16:01 combo sshd(pam_unix)[19939]: authentication failure...")
    submit_button = st.form_submit_button("Анализировать")

if submit_button and log_input:
    with st.spinner("Обработка ML-моделью..."):
        try:
            response = requests.post(f"{API_URL}/clusterize", json={"log_message": log_input})
            
            if response.status_code == 200:
                result = response.json()
                
                st.subheader("Результат анализа:")
                
                col1, col2, col3 = st.columns(3)
                
                if result['is_anomaly']:
                    col1.error("Обнаружена аномалия!")
                else:
                    col1.success("Стандартное событие!")
                    
                col2.metric("ID Кластера", f"Кластер {result['cluster_id']}")
                col3.metric("Дистанция (отклонение)", f"{result['distance']:.4f}")
                
                st.markdown("**Очищенный шаблон (после маскировки):**")
                st.code(result['cleaned_log'], language="text")
                
            else:
                st.error(f"Ошибка API: {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("Не удалось подключиться к Бэкенду.")

st.markdown("---")
st.header("История событий из базы данных")

if st.button("Обновить данные"):
    try:
        response = requests.get(f"{API_URL}/logs?limit=50")
        
        if response.status_code == 200:
            logs_data = response.json()
            
            if logs_data:
                df = pd.DataFrame(logs_data)
                
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
                
                df = df.rename(columns={
                    "id": "ID",
                    "original_log": "Сырой лог",
                    "cleaned_log": "Шаблон",
                    "cluster_id": "Кластер",
                    "distance": "Дистанция",
                    "is_anomaly": "Аномалия",
                    "created_at": "Время"
                })
                
                def highlight_anomalies(row):
                    if row['Аномалия']:
                        return ['background-color: rgba(255, 0, 0, 0.2)'] * len(row)
                    return [''] * len(row)
                
                styled_df = df.style.apply(highlight_anomalies, axis=1)
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.info("База данных пока пуста.")
        else:
            st.error("Ошибка при получении истории.")
            
    except requests.exceptions.ConnectionError:
        st.error("Не удалось подключиться к Бэкенду.")