import pandas as pd
import numpy as np
import datetime

def load_citrus_reference():
    """Загружает справочник по импорту из CSV"""
    try:
        return pd.read_csv("data/morocco_citrus_stats.csv")
    except Exception:
        # Fallback на случай отсутствия файла
        data = {
            "Exporter": ["Марокко (Клементины)", "Египет (Стандарт)", "Турция (Ранние сорта)"],
            "Net_Weight_Tons": [21.5, 24.0, 22.0],
            "Base_Shipping_Days": [16, 10, 7],
            "Customs_Clearance_Days": [4, 3, 2],
            "Demurrage_Daily_RUB": [45000, 40000, 35000]
        }
        return pd.DataFrame(data)

def calculate_supply_chain(retailer, supplier, store_coverage, port_storm, customs_risk):
    df_ref = load_citrus_reference()
    supplier_row = df_ref[df_ref["Exporter"].str.contains(supplier.split()[0])]
    
    if not supplier_row.empty:
        base_days = int(supplier_row["Base_Shipping_Days"].values[0])
        customs_days = int(supplier_row["Customs_Clearance_Days"].values[0])
        demurrage_cost = float(supplier_row["Demurrage_Daily_RUB"].values[0])
        net_weight = float(supplier_row["Net_Weight_Tons"].values[0])
    else:
        base_days, customs_days, demurrage_cost, net_weight = 16, 4, 45000, 21.5

    # Масштаб сети
    total_stores = 25000 if "X5" in retailer else 28000
    base_daily_per_store = 45 if "X5" in retailer else 40
    active_stores = int(total_stores * (store_coverage / 100))

    # Риски
    extra_days = 0
    if port_storm: extra_days += 7
    if customs_risk: extra_days += customs_days
    
    total_shipping_days = base_days + extra_days
    
    start_date = datetime.date(2026, 11, 1)
    order_deadline = start_date - datetime.timedelta(days=total_shipping_days)
    
    # Финансовые потери (простой + порча)
    financial_loss = extra_days * demurrage_cost

    return {
        "active_stores": active_stores,
        "total_shipping_days": total_shipping_days,
        "extra_days": extra_days,
        "order_deadline": order_deadline,
        "financial_loss": financial_loss,
        "net_weight": net_weight
    }
