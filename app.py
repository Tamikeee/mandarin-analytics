import streamlit as st
import datetime
import pandas as pd
import numpy as np

# Строгий корпоративный стиль без лишних элементов
st.set_page_config(page_title="Supply Chain Analytics System", layout="wide")

# Кастомный CSS для создания строгого монохромного интерфейса
st.markdown("""
    <style>
    .reportview-container { background: #f8f9fa; }
    h1, h2, h3 { color: #111111; font-family: 'Helvetica Neue', Arial, sans-serif; font-weight: 600; }
    .stMetric { background: #ffffff; padding: 15px; border: 1px solid #e0e0e0; border-radius: 4px; }
    .stMetric label { color: #666666 !important; font-size: 14px !important; }
    .stMetric div { color: #111111 !important; font-size: 28px !important; font-weight: 700; }
    </style>
""", unsafe_allowed_html=True)

st.title("СИСТЕМА ПРЕДИКТИВНОЙ АНАЛИТИКИ ЦЕПОЧЕК ПОСТАВОК")
st.caption("Версия 2.0. Строгий монохромный режим. Расчетные параметры зафиксированы.")

st.markdown("---")

# Фиксированные константы по вашему запросу (только 60)
FIXED_COVERAGE = 60       # Процент покрытия сети жестко равен 60%
FIXED_MOTO_HOURS = 60     # Базовая нагрузка погрузчиков жестко равна 60 часам в неделю

# ПОДГРУЗКА РЕАЛЬНЫХ ДАННЫХ
try:
    historical_data = pd.read_csv("data.csv")
    historical_data['Date'] = pd.to_datetime(historical_data['Date'])
    dec_sales = historical_data[historical_data['Date'].dt.month == 12]['SalesUnits'].mean()
    oct_sales = historical_data[historical_data['Date'].dt.month == 10]['SalesUnits'].mean()
    real_seasonality_ratio = round(dec_sales / oct_sales, 2) if oct_sales > 0 else 4.0
    data_status = f"Загружен исторический файл data.csv. Коэффициент сезонности: x{real_seasonality_ratio}"
except Exception:
    real_seasonality_ratio = 4.15
    data_status = "Используются базовые системные коэффициенты ритейла (файл data.csv не найден)."

# СЕТКА ИНТЕРФЕЙСА: Слева параметры, справа аналитика
col_left, col_right = st.columns()

with col_left:
    st.subheader("ПАРАМЕТРЫ РАСЧЕТА")
    retail_network = st.selectbox("Торговая сеть", ["X5 Group", "Магнит"])
    product_category = st.selectbox("Номенклатурная группа", ["Мандарины (Марокко)", "Мандарины (Египет)", "Мандарины (Турция)"])
    
    st.markdown("---")
    date_start = datetime.date(2026, 11, 1)
    date_end = datetime.date(2027, 1, 31)
    st.text(f"Начало периода: {date_start.strftime('%d.%m.%Y')}")
    st.text(f"Конец периода: {date_end.strftime('%d.%m.%Y')}")
    st.text(f"Покрытие розничной сети: {FIXED_COVERAGE}% (зафиксировано)")
    
    st.markdown("---")
    st.caption(data_status)

with col_right:
    st.subheader("ПРОГНОЗНЫЕ ПОКАЗАТЕЛИ СНАБЖЕНИЯ")
    
    base_stores = 25000 if "X5" in retail_network else 28000
    shipping_days = 16 if "Марокко" in product_category else (10 if "Египет" in product_category else 7)
    
    # Расчет объема с учетом фиксированного покрытия 60%
    active_stores = int(base_stores * (FIXED_COVERAGE / 100))
    calculated_tons = int((active_stores * 45 * 92 * (real_seasonality_ratio / 3)) / 1000)
    order_deadline = date_start - datetime.timedelta(days=shipping_days)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Целевой объем закупки", f"{calculated_tons:,} тонн")
    m2.metric("Расчетное плечо доставки", f"{shipping_days} суток")
    m3.metric("Крайний срок размещения заказа", order_deadline.strftime("%d.%m.%Y"))
    
    st.markdown("---")
    st.subheader("График распределения суточной потребности (тонны)")
    
    days_count = (date_end - date_start).days
    np.random.seed(42)
    timeline = [date_start + datetime.timedelta(days=x) for x in range(days_count)]
    
    volumes = []
    for day in timeline:
        base = (active_stores * 45) / 1000
        coef = real_seasonality_ratio if day.month == 12 and day.day > 15 else (real_seasonality_ratio * 0.5 if day.month == 12 else 1.0)
        volumes.append(base * coef + np.random.normal(0, base * 0.05))
        
    df_chart = pd.DataFrame({"Объем поставки (т)": volumes}, index=[d.strftime("%d.%m") for d in timeline])
    st.line_chart(df_chart, color="#555555")

st.markdown("---")

# РАЗДЕЛ ТЕХНИКИ БЕЗ ПОЛЗУНКОВ
st.subheader("МОНИТОРИНГ ТЕХНИЧЕСКОГО СОСТОЯНИЯ ПАРКА ПОГРУЗЧИКОВ")
st.text(f"Анализ износа протектора на основе стандартной загрузки: {FIXED_MOTO_HOURS} моточасов в неделю")

fleet_data = {
    "Код техники": ["RT-01-TOYOTA", "RT-02-LINDE", "RT-03-JUNG", "RT-04-YALE", "RT-05-TOYOTA"],
    "Бренд шин": ["Continental", "Continental", "SolidDeal (КНР)", "Marangoni", "SolidDeal (КНР)"],
    "Наработка (моточасы)":,
    "Текущая нагрузка в неделю": [f"{FIXED_MOTO_HOURS} ч" for _ in range(5)],
    "Коэффициент износа шин (%)": [56.8, 35.6, 94.2, 12.4, 74.1],
    "Рекомендованный статус": ["Эксплуатация разрешена", "Эксплуатация разрешена", "ТРЕБУЕТСЯ СРОЧНАЯ ЗАМЕНА", "Новое оборудование", "Плановое ТО через 5 суток"]
}

df_fleet = pd.DataFrame(fleet_data)
st.dataframe(df_fleet.style.format({"Коэффициент износа шин (%)": "{:.1f}%"}), use_container_width=True)
