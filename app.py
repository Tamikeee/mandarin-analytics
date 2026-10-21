import streamlit as st
import datetime
import random
import pandas as pd

# 1. Настройка страницы
st.set_page_config(page_title="Supply Chain & Fleet Analytics", page_icon="📦", layout="wide")

st.title("📦 Модуль предиктивной аналитики для ритейла и логистики")
st.write("Прототип B2B-системы учета рисков цепочки поставок и износа оборудования")

# Разделяем экран на две вкладки, чтобы показать обе ваши идеи
tab1, tab2 = st.tabs(["🍊 Аналитика поставок (Мандарины)", "🚜 Износ техники на складе"])

# ==========================================
# ВКЛАДКА 1: МАНДАРИНЫ
# ==========================================
with tab1:
    st.header("Управление сезонными поставками фрэш-продукции")
    
    col_in1, col_in2 = st.columns(2)
    
    with col_in1:
        st.subheader("⚙️ Базовые параметры")
        supplier = st.selectbox("Страна-экспортер", ["Марокко", "Турция", "Египет"], key="supplier")
        store_count = st.slider("Количество супермаркетов в сети", 5, 100, 25)
        
        # Период планирования
        start_date = datetime.date(2026, 11, 1)
        end_date = datetime.date(2027, 1, 31)
        st.caption(f"Период анализа спроса: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}")

    with col_in2:
        st.subheader("⚠️ Внешние факторы риска (Данные телеметрии/погоды)")
        # Те самые крутые фичи, которые вы хотели прокинуть руками!
        weather = st.select_slider("Прогноз погоды в регионе сбора", options=["Засуха (-30% урожая)", "Норма", "Отличный урожай (+15%)"], value="Норма")
        port_storm = st.toggle("🚨 Шторм / Забастовки в транзитных портах", value=False)
        customs_delay = st.toggle("⏳ Повышенный досмотр на таможне (очереди)", value=False)

    # ЛОГИКА РАСЧЕТА
    days = (end_date - start_date).days
    base_tonnage = store_count * days * 0.15 # условно 150 кг в день на магазин
    
    # Модификаторы урожайности
    if "Засуха" in weather:
        base_tonnage *= 0.7
    elif "Отличный" in weather:
        base_tonnage *= 1.15
        
    # Считаем сроки логистики
    logistic_days = 14 # базовые дни в пути
    if port_storm:
        logistic_days += 7
    if customs_delay:
        logistic_days += 4
        
    order_deadline = start_date - datetime.timedelta(days=logistic_days)
    
    # Вывод результатов
    st.markdown("---")
    st.subheader("📊 Рекомендация системы")
    
    res1, res2, res3 = st.columns(3)
    res1.metric("Необходимый объем закупки", f"{round(base_tonnage, 1)} тонн")
    res2.metric("Дней в пути (с учетом рисков)", f"{logistic_days} дней")
    res3.metric("Крайний срок заказа", order_deadline.strftime("%d.%m.%Y"))
    
    if port_storm or customs_delay:
        st.error(f"⚠️ Внимание! Из-за логистических рисков дедлайн заказа сдвинут. Отправьте заявку не позднее {order_deadline.strftime('%d.%m.%Y')}.")

    # Рисуем график
    st.subheader("📈 Моделирование графика распределения продаж")
    chart_data = []
    current = start_date
    while current <= end_date:
        # Предновогодний пик
        if current.month == 12 and current.day > 15:
            day_demand = random.randint(800, 1200) * (store_count / 10)
        else:
            day_demand = random.randint(100, 250) * (store_count / 10)
        
        # Если шторм — поставки в начале периода просядут
        if port_storm and current.month == 11 and current.day < 10:
            day_demand *= 0.2
            
        chart_data.append(day_demand)
        current += datetime.timedelta(days=1)
        
    st.line_chart(chart_data)

# ==========================================
# ВКЛАДКА 2: ПОГРУЗЧИКИ
# ==========================================
with tab2:
    st.header("Прогнозное обслуживание складской техники (Predictive Maintenance)")
    st.write("Система считывает моточасы и нагрузку с погрузчиков и предсказывает замену колес")
    
    # Эмуляция данных из WMS системы склада
    machinery_data = {
        "ID техники": ["Погрузчик #01 (Toyota)", "Погрузчик #02 (Linde)", "Погрузчик #03 (Jungheinrich)", "Погрузчик #04 (Yale)"],
        "Текущие моточасы":,
        "Интенсивность работы": ["Высокая (Зона приемки)", "Средняя", "Критическая (24/7 Хранение)", "Низкая"],
        "Износ протектора колес": ["78% (Требует внимания)", "32% (Норма)", "94% (КРИТИЧЕСКИЙ ИЗНОС)", "10% (Новое)"]
    }
    
    df_machinery = pd.DataFrame(machinery_data)
    st.dataframe(df_machinery, use_container_width=True)
    
    st.warning("🚨 Система рекомендует: Запланировать замену ведущих колес для **Погрузчика #03** в течение следующих 48 рабочих часов, чтобы избежать аварийной остановки склада.")
