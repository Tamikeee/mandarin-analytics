import streamlit as st
import datetime
import pandas as pd
import numpy as np

# Импорт наших чистых модулей
from core.vessel_api import fetch_vessel_data, get_vessel_api_key
from core.analytics import calculate_supply_chain

st.set_page_config(page_title="X5 & Магнит: Enterprise Analytics", page_icon="🍊", layout="wide")

st.title("🍊 Система предиктивной аналитики снабжения и складской логистики")
st.markdown("**Enterprise-модуль | Интеграция с реальными данными и спутниковым трекингом**")

tab1, tab2 = st.tabs(["🚛 Цепочки поставок фрэш-продукции & Трекер", "🚜 Телеметрия и износ парка погрузчиков"])

with tab1:
    st.header("Прогнозирование поставок и спутниковый мониторинг")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        retailer = st.selectbox("Торговая сеть", ["X5 Group (Пятёрочка, Перекрёсток)", "Магнит"])
        supplier = st.selectbox("Страна-экспортер", ["Марокко (Клементины)", "Египет (Стандарт)", "Турция (Ранние сорта)"])
        store_coverage = st.slider("Покрытие сети (%)", 1, 100, 10)
    with col_in2:
        port_storm = st.toggle("🚨 Задержка в транзитном порту (Шторм)")
        customs_risk = st.toggle("⏳ Усиленный контроль Россельхознадзора")

    # Расчет через аналитический модуль
    metrics = calculate_supply_chain(retailer, supplier, store_coverage, port_storm, customs_risk)

    st.markdown("---")
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Активных точек доставки", f"{metrics['active_stores']} шт.")
    res2.metric("Срок доставки", f"{metrics['total_shipping_days']} дней", delta=f"+{metrics['extra_days']} дн." if metrics['extra_days'] > 0 else "В норме", delta_color="inverse")
    res3.metric("Дедлайн заказа", metrics['order_deadline'].strftime("%d.%m.%Y"))
    res4.metric("Финансовый рисковый ущерб", f"{int(metrics['financial_loss']):,} руб.", delta="Внимание" if metrics['financial_loss'] > 0 else "Ок", delta_color="inverse")

    # Спутниковый трекер с реальным или демо-режимом
    if "Марокко" in supplier:
        st.markdown("---")
        st.subheader("🚢 Спутниковый трекинг контейнеровоза (MSC NEDERLAND III)")
        
        target_imo = 8918954
        api_data = fetch_vessel_data(target_imo)
        
        if api_data:
            ship_name = api_data.get("name", "MSC NEDERLAND III")
            lat = float(api_data.get("latitude", 30.4223))
            lon = float(api_data.get("longitude", -9.6371))
            speed = float(api_data.get("speed", 14.5))
            course = float(api_data.get("course", 65.0))
            dest = api_data.get("destination", "BEANR")
            eta = api_data.get("eta", "2026-11-01 10:00:00")
            status_msg = "🟢 РЕЖИМ LIVE: Ключ найден, данные синхронизированы со спутником через VesselFinder API."
        else:
            ship_name = "MSC NEDERLAND III (IMO: 8918954)"
            lat, lon = 30.4223, -9.6371  # Порт Агадир
            speed, course = 15.0, 340.0
            dest = "ANTWERP (BE ANR)"
            eta = "01.11.2026 10:00"
            status_msg = "🔵 ДЕМО-РЕЖИМ: Секретный ключ не обнаружен в secrets.toml, активирована клиентская симуляция для экономии лимитов."

        st.caption(status_msg)
        
        # Рендер карты Leaflet
        html_map_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                #map {{ width: 100%; height: 400px; border-radius: 8px; }}
                body {{ margin: 0; padding: 0; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([{lat}, {lon}], 7);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 18 }}).addTo(map);
                var marker = L.circleMarker([{lat}, {lon}], {{ color: '#ff4b4b', fillColor: '#ff4b4b', fillOpacity: 0.9, radius: 8 }}).addTo(map);
                marker.bindPopup("<b>{ship_name}</b><br>Назначение: {dest}").openPopup();
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_map_code, height=420)

with tab2:
    st.header("📈 Мониторинг износа ведущих колес погрузчиков")
    st.write("Модуль телеметрии складской техники работает в штатном режиме.")
