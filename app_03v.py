import streamlit as st
import datetime
import pandas as pd
import numpy as np
import requests

# Настройка страницы
st.set_page_config(page_title="X5 & Магнит: Predictive Analytics", page_icon="🍊", layout="wide")

st.title("🍊 Система предиктивной аналитики снабжения и складской логистики")
st.write("Прототип B2B-модуля для федеральных торговых сетей РФ (X5 Group / Магнит)")

tab1, tab2 = st.tabs(["🚛 Цепочки поставок фрэш-продукции", "🚜 Телеметрия и износ парка погрузчиков"])

# Функция для запроса к VesselFinder API
def get_vessel_status(api_key, imo_number):
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return None  # Если ключ не задан, уходим в демо-режим
        
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
            if data:
                return data
        return None
    except Exception:
        return None

# ==========================================
# ВКЛАДКА 1: РИТЕЙЛ (X5 / МАГНИТ) + МОРСКОЙ ТРЕКЕР
# ==========================================
with tab1:
    st.header("Прогнозирование объемов и графиков импорта цитрусовых")
    
    col_in1, col_in2 = st.columns(2)
    
    with col_in1:
        st.subheader("⚙️ Выбор ритейлера и логистики")
        retailer = st.selectbox("Торговая сеть (закупщик)", ["X5 Group (Пятёрочка, Перекрёсток)", "Магнит"])
        supplier = st.selectbox("Страна-экспортер мандаринов", ["Марокко (Клементины)", "Египет (Стандарт)", "Турция (Ранние сорта)"])
        
        # Масштаб сети
        if "X5" in retailer:
            base_daily_per_store = 45  # средний заказ мандаринов в кг на 1 точку Х5 в день
            total_stores = 25000
        else:
            base_daily_per_store = 40  # для Магнита
            total_stores = 28000
            
        store_coverage = st.slider("Процент покрытия сети этой поставкой (%)", 1, 100, 10)
        active_stores = int(total_stores * (store_coverage / 100))
        st.caption(f"Товар поставляется в {active_stores} распределительных центров и магазинов.")

    with col_in2:
        st.subheader("⚠️ Внешние факторы и риски")
        weather = st.select_slider("Погодные условия в стране отправления", options=["Засуха / Неурожай", "Норма", "Профицит урожая"], value="Норма")
        port_storm = st.toggle("🚨 Шторм / Задержка судов в транзитных портах")
        customs_risk = st.toggle("⏳ Усиленный фитосанитарный контроль Россельхознадзора")

    # Сроки логистики зависят от страны
    start_date = datetime.date(2026, 11, 1)
    end_date = datetime.date(2027, 1, 31)
    total_days = (end_date - start_date).days
    
    if "Марокко" in supplier:
        base_shipping_days = 16
        country_coeff = 1.3
    elif "Египет" in supplier:
        base_shipping_days = 10
        country_coeff = 0.9
    else:  # Турция
        base_shipping_days = 7
        country_coeff = 1.0
        
    if port_storm: base_shipping_days += 7
    if customs_risk: base_shipping_days += 4
    
    order_deadline = start_date - datetime.timedelta(days=base_shipping_days)
    
    harvest_mod = 1.0
    if "Засуха" in weather: harvest_mod = 0.7
    if "Профицит" in weather: harvest_mod = 1.15

    # ГЕНЕРАЦИЯ ГРАФИКА
    dates_list = [start_date + datetime.timedelta(days=x) for x in range(total_days)]
    demand_curve = []
    
    for d in dates_list:
        day_volume = (active_stores * base_daily_per_store) / 1000 
        if d.month == 11:
            coef = 1.0
        elif d.month == 12:
            if d.day > 15:
                coef = 4.5 * country_coeff
            else:
                coef = 2.0 * country_coeff
        elif d.month == 1:
            if d.day < 8:
                coef = 1.5
            else:
                coef = 0.7
                
        final_day_volume = day_volume * coef * harvest_mod
        final_day_volume += np.random.normal(0, day_volume * 0.05)
        demand_curve.append(max(0, final_day_volume))
        
    total_needed_tons = sum(demand_curve)

    # Вывод результатов коммерческого департамента
    st.markdown("---")
    st.subheader("📊 Рекомендация коммерческого департамента")
    
    res1, res2, res3 = st.columns(3)
    res1.metric(f"Необходимый объем для {retailer}", f"{round(total_needed_tons, 1)} тонн")
    res2.metric("Срок доставки с учетом рисков", f"{base_shipping_days} дней")
    res3.metric("Крайний срок размещения заказа", order_deadline.strftime("%d.%m.%Y"))
    
    st.subheader("📈 Математическая модель распределения спроса по дням (в тоннах)")
    df_chart = pd.DataFrame({"Тонны": demand_curve}, index=[d.strftime("%d.%m") for d in dates_list])
    st.line_chart(df_chart)

    # ==========================================
    # ИНТЕГРАЦИЯ: МОНИТОРИНГ СУДОВ В РЕАЛЬНОМ ВРЕМЕНИ
    # ==========================================
    if "Марокко" in supplier:
        st.markdown("---")
        st.subheader("🚢 Мониторинг морского судна в реальном времени (Плечо №1: Марокко — Бельгия)")
        
        # Поле ввода API ключа для пользователя
        with st.sidebar:
            st.header("🔑 Настройки API")
            vf_api_key = st.text_input("VesselFinder User Key", type="password", placeholder="Введите ваш ключ для live-данных")
        
        # Целевое судно с мандаринами (MSC NEDERLAND III)
        target_imo = 8918954
        
        # Получаем данные (Live или Demo)
        api_data = get_vessel_status(vf_api_key, target_imo)
        
        if api_data:
            # Если сработал реальный ключ API
            ship_name = api_data.get("name", "MSC NEDERLAND III")
            nav_status = api_data.get("nav_status", "Moored")
            lat = float(api_data.get("latitude", 30.42))
            lon = float(api_data.get("longitude", -9.63))
            dest = api_data.get("destination", "BEANR")
            eta = api_data.get("eta", "2026-11-01 10:00:00")
            data_source = "🟢 Данные со спутников/станций AIS (VesselFinder Live API)"
        else:
            # Реалистичный демо-режим на основе текущего состояния судна
            ship_name = "MSC NEDERLAND III"
            nav_status = "Moored (Швартовка / На погрузке)"
            lat = 30.4223  # Точные координаты порта Агадир, Марокко
            lon = -9.6371
            dest = "ANTWERP (BE ANR)"
            eta = "01.11.2026 10:00 (GMT+1)"
            data_source = "🔵 Режим симуляции (Укажите валидный API Key на боковой панели для синхронизации)"

        # Отрисовка интерфейса трекера
        st.caption(data_source)
        track1, track2, track3, track4 = st.columns(4)
        track1.metric("Судно контейнеровоз", ship_name)
        track2.metric("Навигационный статус", nav_status)
        track3.metric("Следующий транзитный порт", dest)
        track4.metric("Расчетное прибытие (ETA)", eta)
        
        # Карта местоположения судна
        st.write("📍 **Текущая геопозиция судна на глобальной карте:**")
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_data, zoom=10 if api_data else 12)

# ==========================================
# ВКЛАДКА 2: ПОГРУЗЧИКИ
# ==========================================
with tab2:
    st.header("📈 Мониторинг износа ведущих колес парка ричтраков и погрузчиков")
    st.write("Реальный износ рассчитывается на базе бренда шин, интенсивности смен и качества покрытия склада")
    
    st.subheader("🔮 Симулятор износа конкретного погрузчика")
    col_fork1, col_fork2, col_fork3 = st.columns(3)
    
    with col_fork1:
        forklift_brand = st.selectbox("Марка техники", ["Toyota 8FBMK20", "Linde E20SL", "Jungheinrich EFG"])
        tire_brand = st.selectbox("Бренд установленных колес/шин", ["Continental (Премиум)", "Marangoni (Средний)", "SolidDeal (Бюджетный Китай)"])
    
    with col_fork2:
        hours_per_day = st.slider("Интенсивность работы (часов в сутки)", 1, 24, 12)
        floor_type = st.selectbox("Тип покрытия на складе", ["Идеальный наливной пол", "Бетон с дефектами/порогами", "Асфальт (Уличная рампа)"])
        
    with col_fork3:
        current_hours = st.number_input("Текущий налет колес (моточасы)", min_value=0, max_value=4000, value=1200)

    base_resource = 2500
    
    if "Continental" in tire_brand: tire_coef = 1.2
    elif "Marangoni" in tire_brand: tire_coef = 1.0
    else: tire_coef = 0.7
    
    if "Идеальный" in floor_type: floor_coef = 1.0
    elif "Бетон" in floor_type: floor_coef = 0.8
    else: floor_coef = 0.6
    
    real_max_resource = base_resource * tire_coef * floor_coef
    wear_percentage = min(100, int((current_hours / real_max_resource) * 100))
    remaining_hours = max(0, real_max_resource - current_hours)
    days_left = int(remaining_hours / hours_per_day) if hours_per_day > 0 else 999

    st.markdown("---")
    st.subheader(f"📊 Анализ состояния для {forklift_brand}")
    
    w1, w2, w3 = st.columns(3)
    w1.metric("Текущий износ колес (%)", f"{wear_percentage}%")
    w2.metric("Оставшийся ресурс шины", f"{int(remaining_hours)} моточасов")
    w3.metric("Прогнозное время замены", f"через {days_left} дн.")
    
    if wear_percentage >= 90:
        st.error(f"🚨 КРИТИЧЕСКИЙ ИЗНОС! Колесо на {forklift_brand} сотрется до диска через {days_left} дней. Срочно оформите заявку на замену шин в WMS!")
    elif wear_percentage >= 70:
        st.warning(f"⚠️ ВНИМАНИЕ: Повышенный износ шины. Рекомендуется заказать запчасти. Замена потребуется через {days_left} дней.")
    else:
        st.success("✅ Состояние колес в пределах нормы. Плановое ТО не требуется.")