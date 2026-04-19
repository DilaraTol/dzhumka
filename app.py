from xmlrpc import client

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from google import genai

# ─────────────────────────────────────────────────────────────
# 1. Кэширование ML-моделей (обучается один раз за сессию)
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_ml_models():
    np.random.seed(42)
    dates = pd.date_range("2023-09-01", "2024-06-15", freq="D")
    df = pd.DataFrame({"date": dates})
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_vacation"] = df["date"].dt.month.isin([6, 7, 8]).astype(int)

    # Синтетический расход: будни > выходные, учебный год > каникулы
    base = np.where(df["is_weekend"] == 1, 400, 
             np.where(df["is_vacation"] == 1, 900, 2400))
    noise = np.random.normal(0, 120, len(df))
    season = 150 * np.sin(2 * np.pi * df["month"] / 12)
    df["usage"] = np.clip(base + noise + season, 200, None)

    # Имитация 3 утечек/протечек
    leaks = np.random.choice(df.index, 3, replace=False)
    df.loc[leaks, "usage"] += np.random.uniform(1500, 2500, 3)

    # Признаки для модели
    df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    feats = ["day_of_week", "month", "is_weekend", "is_vacation", "day_sin", "day_cos"]

    # Обучение регрессора и детектора аномалий
    reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    reg.fit(df[feats], df["usage"])

    iso = IsolationForest(contamination=0.04, random_state=42, n_jobs=-1)
    iso.fit(df[["usage"]])

    return reg, iso, feats

# ─────────────────────────────────────────────────────────────
# 2. Кэширование LLM (Gemini API)
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_llm():
    # Настройка API ключа (рекомендуется использовать st.secrets для безопасности)
    api_key = st.secrets["GEMINI_API_KEY"]  # Раскомментируйте и настройте в secrets.toml
    client = genai.Client(api_key=api_key)
    
    # Получить список доступных моделей
    models = client.models.list()
    available_models = [m.name for m in models]
    print("Доступные модели:", available_models)
    
    # Предпочитаемые модели (бесплатные или доступные)
    preferred_models = ['gemini-1.0-pro', 'gemini-pro', 'gemini-1.5-flash', 'gemini-1.5-pro']
    
    # Выбрать первую доступную предпочтительную модель
    selected_model = None
    for pref in preferred_models:
        if pref in available_models:
            selected_model = pref
            break
    
    if not selected_model:
        # Если ни одна не доступна, взять первую из списка
        selected_model = available_models[0] if available_models else 'gemini-pro'
    
    print(f"Выбрана модель: {selected_model}")
    return client, selected_model

# ─────────────────────────────────────────────────────────────
# 3. Функция анализа и генерации отчёта
# ─────────────────────────────────────────────────────────────
def analyze_and_report(date, usage, reg, iso, feats, client, model_name):
    dt = pd.to_datetime(date)
    input_data = pd.DataFrame([{
        "day_of_week": dt.dayofweek,
        "month": dt.month,
        "is_weekend": int(dt.dayofweek >= 5),
        "is_vacation": int(dt.month in [6, 7, 8]),
        "day_sin": np.sin(2 * np.pi * dt.dayofweek / 7),
        "day_cos": np.cos(2 * np.pi * dt.dayofweek / 7)
    }])

    predicted = reg.predict(input_data[feats])[0]
    anomaly_flag = iso.predict(pd.DataFrame([[usage]], columns=["usage"]))[0] == -1
    diff = usage - predicted

    prompt = f"""Ты экологический аналитик школьной системы водоснабжения.
Данные за {date}:
- Фактический расход: {usage:.0f} л
- Прогноз ML (норма): {predicted:.0f} л
- Отклонение: {diff:+.0f} л
- Аномалия/Утечка: {'Да' if anomaly_flag else 'Нет'}

Напиши краткий отчёт (4-6 предложений) на русском языке:
1. Оцени ситуацию: соответствует ли расход ожидаемому.
2. Если есть отклонение или аномалия, назови 2 вероятные причины.
3. Дай 2 конкретных и простых совета по экономии воды в школе.
Пиши простым текстом, без списков и маркдауна."""

    # Генерация с помощью Gemini
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    report = response.text.strip()
    return report, predicted, anomaly_flag, diff

# ─────────────────────────────────────────────────────────────
# 4. Streamlit Интерфейс
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="💧 Умная Школа: Вода", page_icon="💧", layout="wide")
st.title("💧 Система мониторинга и экономии воды в школе")
st.markdown("Введите данные с датчиков расхода. ИИ проверит расход на аномалии и сгенерирует отчёт с рекомендациями.")

with st.form("water_input"):
    col1, col2 = st.columns(2)
    with col1:
        date_in = st.date_input("📅 Дата замера", value=pd.Timestamp.today())
    with col2:
        usage_in = st.number_input("💧 Расход воды (литры)", min_value=0, value=1500, step=50)
    submitted = st.form_submit_button("🔍 Запустить анализ", type="primary", use_container_width=True)

if submitted:
    with st.spinner("⏳ Инициализация моделей... (загрузка ML и подключение к Gemini API)"):
        reg, iso, feats = load_ml_models()
        client, model_name = load_llm()
        
        report, predicted, is_anomaly, diff = analyze_and_report(
            date_in.isoformat(), usage_in, reg, iso, feats, client, model_name
        )

    st.success("✅ Анализ завершён!")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Фактический расход", f"{usage_in:.0f} л")
    c2.metric("Прогноз ML", f"{predicted:.0f} л")
    status_text = "⚠️ Аномалия" if is_anomaly else "✅ Норма"
    c3.metric("Статус", status_text, delta=f"{diff:+.0f} л")

    st.divider()
    st.subheader("🤖 Отчёт экологического аналитика")
    st.info(report)

    st.caption("💡 *Примечание: используется Gemini API. При подключении реальных датчиков данные будут передаваться через API.*")