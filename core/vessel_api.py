import streamlit as st
import requests

def get_vessel_api_key():
    """
    Безопасно получает ключ API. 
    Сначала проверяет секреты Streamlit (.streamlit/secrets.toml),
    затем fallback на поле ввода в интерфейсе.
    """
    try:
        if "VESSEL_FINDER_KEY" in st.secrets:
            return st.secrets["VESSEL_FINDER_KEY"]
    except Exception:
        pass
    return None

def fetch_vessel_data(imo_number: int):
    """
    Запрашивает реальные данные судна по IMO через VesselFinder API.
    Если ключ отсутствует или сеть недоступна, возвращает None (триггер для демо-режима).
    """
    api_key = get_vessel_api_key()
    if not api_key:
        return None
        
    url = "https://vesselfinder.com"
    params = {
        "userkey": api_key,
        "imo": imo_number,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, dict):
                return data
        return None
    except Exception:
        return None
