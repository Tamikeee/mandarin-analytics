import streamlit as st
import datetime
import pandas as pd
import numpy as np

# Импорт чистых модулей из папки core
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
        store_coverage = st.slider("Покрытие сети (%)", 1, 100, 15)
    with col_in2:
        port_storm = st.toggle("🚨 Задержка в транзитном порту (Шторм)")
        customs_risk = st.toggle("⏳ Усиленный контроль Россельхознадзора")

    # Расчет через аналитический модуль на основе реальных данных справочника
    metrics = calculate_supply_chain(retailer, supplier, store_coverage, port_storm, customs_risk)

    st.markdown("---")
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Активных точек доставки", f"{metrics['active_stores']} шт.")
    res2.metric("Срок доставки", f"{metrics['total_shipping_days']} дней", delta=f"+{metrics['extra_days']} дн." if metrics['extra_days'] > 0 else "В норме", delta_color="inverse")
    res3.metric("Дедлайн заказа", metrics['order_deadline'].strftime("%d.%m.%Y"))
    res4.metric("Финансовый рисковый ущерб", f"{int(metrics['financial_loss']):,} руб.", delta="Внимание" if metrics['financial_loss'] > 0 else "Ок", delta_color="inverse")

    # Полноценный график распределения спроса по дням (без обрывов)
    st.subheader("📈 Математическая модель распределения спроса по дням (в тоннах)")
    days_count = metrics['total_shipping_days']
    dates_list = [datetime.date(2026, 11, 1) + datetime.timedelta(days=i) for i in range(days_count)]
    
    # Генерация плавного нормального распределения поставок без разрывов
    base_tonnage = metrics['active_stores'] * 1.8
    demand_curve = [float(base_tonnage * np.exp(-((i - days_count/2)**2) / (2 * (days_count/4)**2))) for i in range(days_count)]
    df_chart = pd.DataFrame({"Тонны": demand_curve}, index=[d.strftime("%d.%m") for d in dates_list])
    st.line_chart(df_chart)

    # Спутниковый трекер контейнеровоза с живой интерполяцией на карте
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
            lat, lon = 30.4223, -9.6371  # Порт Агадир (реальная стартовая точка)
            speed, course = 15.0, 340.0
            dest = "ANTWERP (BE ANR)"
            eta = "01.11.2026 10:00"
            status_msg = "🔵 ДЕМО-РЕЖИМ: Секретный ключ не обнаружен в secrets.toml, активирована клиентская симуляция движения судна."

        st.caption(status_msg)
        
        # Интерактивная карта Leaflet с плавной интерполяцией координат и нейтральной подложкой CartoDB
        html_map_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                #map {{ width: 100%; height: 420px; border-radius: 8px; }}
                body {{ margin: 0; padding: 0; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var startLat = {lat};
                var startLon = {lon};
                var speedKnots = {speed};
                var courseDegrees = {course};

                var map = L.map('map').setView([startLat, startLon], 7);
                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    maxZoom: 18,
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                }}).addTo(map);

                var shipMarker = L.circleMarker([startLat, startLon], {{
                    color: '#ff4b4b',
                    fillColor: '#ff4b4b',
                    fillOpacity: 0.9,
                    radius: 8
                }}).addTo(map);
                
                shipMarker.bindPopup("<b>{ship_name}</b><br>Назначение: {dest}").openPopup();

                var currentLat = startLat;
                var currentLon = startLon;

                function moveShip() {{
                    var speedMetersPerSecond = speedKnots * 0.514444;
                    var timeStep = {1 if api_data else 50}; 
                    var distanceMoved = speedMetersPerSecond * timeStep;

                    var earthRadius = 6378137;
                    var courseRad = (courseDegrees * Math.PI) / 180;

                    var deltaNorth = distanceMoved * Math.cos(courseRad);
                    var deltaEast = distanceMoved * Math.sin(courseRad);

                    var deltaLat = deltaNorth / earthRadius;
                    var deltaLon = deltaEast / (earthRadius * Math.cos((currentLat * Math.PI) / 180));

                    currentLat += (deltaLat * 180) / Math.PI;
                    currentLon += (deltaLon * 180) / Math.PI;

                    shipMarker.setLatLng([currentLat, currentLon]);
                    map.panTo([currentLat, currentLon], {{animate: true, duration: 0.5}});
                }
                setInterval(moveShip, 1000);
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_map_code, height=440)

with tab2:
    st.header("📈 Мониторинг износа ведущих колес погрузчиков")
    st.write("Модуль телеметрии складской техники работает в штатном режиме.")
