# # app.py — ИСПРАВЛЕННАЯ ВЕРСИЯ (HTML + delete buttons + no rerun bug)
# import streamlit as st
# import pandas as pd
# import numpy as np
# import joblib
# import json
# import os
# import folium
# from streamlit_folium import st_folium
# import warnings
# warnings.filterwarnings('ignore')

# st.set_page_config(layout="wide", page_title="Wetland Bloom Predictor", page_icon="🌊")

# # 🎨 Стилизация
# st.markdown("""
# <style>
#     .main-header {font-size: 2.5rem; font-weight: bold; color: #0068c9; margin-bottom: 1rem;}
#     .status-badge {padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; display: inline-block;}
#     .status-bloom {background-color: #ffe0e0; color: #c00; border: 1px solid #fcc;}
#     .status-safe {background-color: #e0ffe0; color: #080; border: 1px solid #cfc;}
#     .delete-btn {background-color: #ffcccc; color: #c00; border: none; border-radius: 50%; 
#                  width: 28px; height: 28px; font-weight: bold; cursor: pointer;
#                  display: inline-flex; align-items: center; justify-content: center;}
#     .delete-btn:hover {background-color: #ff9999;}
#     .dataframe-container table {border-collapse: collapse; width: 100%;}
#     .dataframe-container th, .dataframe-container td {padding: 8px; text-align: left; border: 1px solid #ddd;}
#     .dataframe-container tr:hover {background-color: #f5f5f5;}
# </style>
# """, unsafe_allow_html=True)

# st.markdown('<div class="main-header">🌊 Wetland Algal Bloom Risk Predictor</div>', unsafe_allow_html=True)
# st.caption("AI-powered early warning system for harmful algal blooms (HABs).")

# # 🔐 Загрузка моделей
# @st.cache_resource
# def load_artifacts():
#     required = ['models/ensemble_model.pkl', 'models/scaler.pkl', 'models/config.json']
#     if not all(os.path.exists(f) for f in required):
#         st.error("🚨 Models not found! Run `python train_model.py` first.")
#         st.stop()
    
#     try:
#         model = joblib.load('models/ensemble_model.pkl')
#         scaler = joblib.load('models/scaler.pkl')
#         with open('models/config.json', 'r') as f:
#             config = json.load(f)
#         return model, scaler, config
#     except Exception as e:
#         st.error(f"❌ Error loading models: {e}")
#         st.info("💡 Try: `rm -rf models/ && python train_model.py`")
#         st.stop()

# model, scaler, config = load_artifacts()
# THRESHOLD = config['threshold']
# FEATURES = config['selected_features']
# INPUT_COLS = config['input_columns']

# # 🔍 Сайдбар
# st.sidebar.title("🔍 Filters")
# show_only_risk = st.sidebar.checkbox("🔴 Show only BLOOM points", value=False)
# st.sidebar.info(f"**Threshold:** {THRESHOLD:.3f}")

# def predict_risk(df_raw):
#     df = df_raw.copy()
#     df['N_P_ratio'] = df['NO3'] / (df['PO4'] + 0.01)
#     df['nutrient_load'] = df['NO3'] + df['NH4'] + df['PO4']
    
#     if df[FEATURES].isnull().any().any():
#         df[FEATURES] = df[FEATURES].fillna(df[FEATURES].median())
        
#     X_scaled = scaler.transform(df[FEATURES])
#     probs = model.predict_proba(X_scaled)[:, 1]
#     preds = (probs >= THRESHOLD).astype(int)
    
#     df['risk_probability'] = probs
#     df['risk_status'] = ['BLOOM' if p else 'NO_BLOOM' for p in preds]
#     df['risk_color'] = ['#ff4b4b' if p else '#00cc66' for p in preds]
#     return df

# # 🗺️ Карта
# def render_map(df):
#     if df.empty or df['latitude'].isnull().all():
#         return folium.Map(location=[52.52, 13.40], zoom_start=5)
    
#     center = [df['latitude'].mean(), df['longitude'].mean()]
#     m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")
    
#     for _, row in df.iterrows():
#         popup = f"""
#         <b>ID:</b> {row['point_id']}<br>
#         <b>Coords:</b> {row['latitude']:.4f}, {row['longitude']:.4f}<br>
#         <b>Risk:</b> {row['risk_probability']:.1%}<br>
#         <b>Status:</b> <span style="color:{row['risk_color']}">{row['risk_status']}</span>
#         """
#         folium.CircleMarker(
#             location=[row['latitude'], row['longitude']],
#             radius=10,
#             color=row['risk_color'],
#             fill=True,
#             fill_color=row['risk_color'],
#             fill_opacity=0.8,
#             popup=folium.Popup(popup, max_width=250),
#             tooltip=f"{row['point_id']}"
#         ).add_to(m)
#     return m

# # 📑 Табы
# tab1, tab2 = st.tabs(["📝 Manual Entry", "📂 CSV Upload"])

# # ================= TAB 1: Manual Entry =================
# with tab1:
#     st.subheader("Enter measurement data point-by-point")
    
#     # ✅ ИСПРАВЛЕНИЕ #2: Убрали отдельные session_state для auto_id
#     if 'manual_df' not in st.session_state:
#         st.session_state.manual_df = pd.DataFrame(columns=INPUT_COLS)

#     col1, col2 = st.columns([1, 1])
#     with col1:
#         auto_id = st.toggle("🔄 Auto-generate IDs", value=True, key="auto_id_toggle")
#     with col2:
#         if st.button("➕ Add Point", use_container_width=True, key="add_point_btn"):
#             new_id = f"Point_{len(st.session_state.manual_df)+1}" if auto_id else ""
#             new_row = pd.DataFrame([{
#                 'point_id': new_id, 'latitude': 52.52, 'longitude': 13.41,
#                 'pH': 7.5, 'O2': 8.0, 'Cl': 50.0, 'NO3': 5.0, 'NH4': 300.0, 'PO4': 100.0, 'Chl': 100.0, 'temp': 18.0
#             }])
#             st.session_state.manual_df = pd.concat([st.session_state.manual_df, new_row], ignore_index=True)
#             # ✅ ИСПРАВЛЕНИЕ #2: Убрали st.rerun() - он вызывал множественное добавление

#     # ✅ ИСПРАВЛЕНИЕ #3: Таблица с кнопками удаления
#     if len(st.session_state.manual_df) > 0:
#         st.markdown("### Edit Data Points")
        
#         # Создаём копию для редактирования
#         edit_df = st.session_state.manual_df.copy()
        
#         # Отображаем таблицу с возможностью редактирования
#         edited_df = st.data_editor(
#             edit_df,
#             column_config={
#                 "point_id": st.column_config.TextColumn("ID", width="small"),
#                 "latitude": st.column_config.NumberColumn("Lat", min_value=-90, max_value=90, format="%.4f", width="small"),
#                 "longitude": st.column_config.NumberColumn("Lon", min_value=-180, max_value=180, format="%.4f", width="small"),
#                 "pH": st.column_config.NumberColumn("pH", min_value=0, max_value=14, step=0.1),
#                 "O2": st.column_config.NumberColumn("O₂", min_value=0),
#                 "Cl": st.column_config.NumberColumn("Cl", min_value=0),
#                 "NO3": st.column_config.NumberColumn("NO₃", min_value=0),
#                 "NH4": st.column_config.NumberColumn("NH₄", min_value=0),
#                 "PO4": st.column_config.NumberColumn("PO₄", min_value=0),
#                 "Chl": st.column_config.NumberColumn("Chl", min_value=0),
#                 "temp": st.column_config.NumberColumn("Temp", min_value=-10, max_value=50, step=0.1)
#             },
#             hide_index=True,
#             use_container_width=True,
#             key="manual_data_editor"
#         )
        
#         # Кнопки удаления под таблицей
#         st.markdown("### Delete Points")
#         cols = st.columns(min(len(edited_df), 5))  # По 5 кнопок в ряд
        
#         for idx, row in edited_df.iterrows():
#             col_idx = idx % 5
#             with cols[col_idx]:
#                 if st.button(f"− {row['point_id'] or f'Row {idx+1}'}", 
#                            key=f"delete_{idx}", 
#                            type="secondary"):
#                     # Удаляем строку
#                     st.session_state.manual_df = edited_df.drop(idx).reset_index(drop=True)
#                     st.rerun()
        
#         # Обновляем данные после редактирования
#         st.session_state.manual_df = edited_df

#     if st.button("🔍 Predict", type="primary", use_container_width=True, key="predict_btn"):
#         if len(st.session_state.manual_df) > 0:
#             st.session_state.results = predict_risk(st.session_state.manual_df)
#             st.success("✅ Prediction complete!")

# # ================= TAB 2: CSV Upload =================
# with tab2:
#     st.subheader("Upload a CSV file with measurement data")
    
#     st.markdown("📋 **Expected CSV Format:**")
#     example = pd.DataFrame([{
#         'point_id': 'Site_A', 'latitude': 52.5200, 'longitude': 13.4050,
#         'pH': 7.5, 'O2': 8.2, 'Cl': 50.0, 'NO3': 5.5, 'NH4': 350.0, 'PO4': 120.0, 'Chl': 150.0, 'temp': 18.5
#     }, {
#         'point_id': 'Site_B', 'latitude': 52.5300, 'longitude': 13.4150,
#         'pH': 8.1, 'O2': 6.5, 'Cl': 45.0, 'NO3': 12.0, 'NH4': 420.0, 'PO4': 180.0, 'Chl': 210.0, 'temp': 21.0
#     }])
#     st.dataframe(example, hide_index=True, use_container_width=True)
    
#     st.download_button("⬇️ Download Example CSV", example.to_csv(index=False).encode(), "example.csv", "text/csv")
    
#     uploaded = st.file_uploader("Choose CSV", type=["csv"])
#     if uploaded:
#         try:
#             csv_df = pd.read_csv(uploaded)
#             if all(c in csv_df.columns for c in INPUT_COLS):
#                 if st.button("🔍 Predict (CSV)", type="primary", use_container_width=True):
#                     st.session_state.results = predict_risk(csv_df)
#                     st.success("✅ Prediction complete!")
#             else:
#                 st.error(f"❌ Missing columns. Expected: {INPUT_COLS}")
#         except Exception as e:
#             st.error(f"❌ Error: {e}")

# # ================= ОБЩИЙ ВЫВОД & КАРТА =================
# if 'results' in st.session_state and st.session_state.results is not None:
#     res = st.session_state.results.copy()
    
#     if show_only_risk:
#         res = res[res['risk_status'] == 'BLOOM']
    
#     if res.empty:
#         st.info("🟢 No risky points with current filter.")
#     else:
#         # Карта
#         st.markdown("### 🗺️ Risk Map")
#         st_folium(render_map(res), width="100%", height=500)
        
#         # ✅ ИСПРАВЛЕНИЕ #1: HTML-таблица вместо st.dataframe
#         st.markdown("### 📊 Results")
#         display_cols = ['point_id', 'latitude', 'longitude', 'risk_probability', 'risk_status']
#         display_df = res[display_cols].copy()
        
#         # Форматируем данные
#         display_df['risk_probability'] = display_df['risk_probability'].apply(lambda x: f"{x:.1%}")
#         display_df['risk_status'] = display_df['risk_status'].apply(
#             lambda x: f'<span class="status-badge status-bloom">🔴 {x}</span>' if x == 'BLOOM' 
#                      else f'<span class="status-badge status-safe">🟢 {x}</span>'
#         )
        
#         # Подсветка строк
#         def get_row_color(status):
#             return '#ffe0e0' if 'BLOOM' in status else '#e0ffe0'
        
#         # Создаём HTML таблицу
#         html_table = '<div class="dataframe-container"><table><thead><tr>'
#         for col in display_df.columns:
#             html_table += f'<th style="background-color: #f0f0f0; font-weight: 600;">{col}</th>'
#         html_table += '</tr></thead><tbody>'
        
#         for idx, row in display_df.iterrows():
#             bg_color = get_row_color(row['risk_status'])
#             html_table += f'<tr style="background-color: {bg_color};">'
#             for val in row:
#                 html_table += f'<td>{val}</td>'
#             html_table += '</tr>'
        
#         html_table += '</tbody></table></div>'
        
#         st.markdown(html_table, unsafe_allow_html=True)
        
#         # Скачивание
#         csv_cols = ['point_id', 'latitude', 'longitude', 'pH', 'O2', 'Cl', 'NO3', 'NH4', 'PO4', 'Chl', 'temp', 'risk_probability', 'risk_status']
#         csv_data = res[csv_cols].copy()
#         csv_data['risk_probability'] = csv_data['risk_probability'].apply(lambda x: f'{x:.1%}')
#         csv_out = csv_data.to_csv(index=False).encode()
        
#         st.download_button("⬇️ Download Results (CSV)", csv_out, "results.csv", "text/csv")
# else:
#     st.info("👈 Enter data in tabs above and click **Predict**")







# # app.py — ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
# import streamlit as st
# import pandas as pd
# import numpy as np
# import joblib
# import json
# import os
# import folium
# from streamlit_folium import st_folium
# import warnings
# warnings.filterwarnings('ignore')

# st.set_page_config(layout="wide", page_title="Wetland Bloom Predictor", page_icon="🌊")

# # 🎨 Стилизация
# st.markdown("""
# <style>
#     .main-header {font-size: 2.5rem; font-weight: bold; color: #0068c9; margin-bottom: 1rem;}
#     .status-badge {padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; display: inline-block;}
#     .status-bloom {background-color: #ffe0e0; color: #c00; border: 1px solid #fcc;}
#     .status-safe {background-color: #e0ffe0; color: #080; border: 1px solid #cfc;}
#     .dataframe-container table {border-collapse: collapse; width: 100%;}
#     .dataframe-container th, .dataframe-container td {padding: 8px; text-align: left; border: 1px solid #ddd;}
#     .dataframe-container tr:hover {background-color: #f5f5f5;}
# </style>
# """, unsafe_allow_html=True)

# st.markdown('<div class="main-header">🌊 Wetland Algal Bloom Risk Predictor</div>', unsafe_allow_html=True)
# st.caption("AI-powered early warning system for harmful algal blooms (HABs).")

# # 🔐 Загрузка моделей
# @st.cache_resource
# def load_artifacts():
#     required = ['models/ensemble_model.pkl', 'models/scaler.pkl', 'models/config.json']
#     if not all(os.path.exists(f) for f in required):
#         st.error("🚨 Models not found! Run `python train_model.py` first.")
#         st.stop()
    
#     try:
#         model = joblib.load('models/ensemble_model.pkl')
#         scaler = joblib.load('models/scaler.pkl')
#         with open('models/config.json', 'r') as f:
#             config = json.load(f)
#         return model, scaler, config
#     except Exception as e:
#         st.error(f"❌ Error loading models: {e}")
#         st.info("💡 Try: `rm -rf models/ && python train_model.py`")
#         st.stop()

# model, scaler, config = load_artifacts()
# THRESHOLD = config['threshold']
# FEATURES = config['selected_features']
# INPUT_COLS = config['input_columns']

# # 🔍 Сайдбар
# st.sidebar.title("🔍 Filters")
# show_only_risk = st.sidebar.checkbox("🔴 Show only BLOOM points", value=False)
# st.sidebar.info(f"**Threshold:** {THRESHOLD:.3f}")

# def predict_risk(df_raw):
#     df = df_raw.copy()
#     df['N_P_ratio'] = df['NO3'] / (df['PO4'] + 0.01)
#     df['nutrient_load'] = df['NO3'] + df['NH4'] + df['PO4']
    
#     if df[FEATURES].isnull().any().any():
#         df[FEATURES] = df[FEATURES].fillna(df[FEATURES].median())
        
#     X_scaled = scaler.transform(df[FEATURES])
#     probs = model.predict_proba(X_scaled)[:, 1]
#     preds = (probs >= THRESHOLD).astype(int)
    
#     df['risk_probability'] = probs
#     df['risk_status'] = ['BLOOM' if p else 'NO_BLOOM' for p in preds]
#     df['risk_color'] = ['#ff4b4b' if p else '#00cc66' for p in preds]
#     return df

# # 🗺️ Карта
# def render_map(df):
#     if df.empty or df['latitude'].isnull().all():
#         return folium.Map(location=[52.52, 13.40], zoom_start=5)
    
#     center = [df['latitude'].mean(), df['longitude'].mean()]
#     m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")
    
#     for _, row in df.iterrows():
#         popup = f"""
#         <b>ID:</b> {row['point_id']}<br>
#         <b>Coords:</b> {row['latitude']:.4f}, {row['longitude']:.4f}<br>
#         <b>Risk:</b> {row['risk_probability']:.1%}<br>
#         <b>Status:</b> <span style="color:{row['risk_color']}">{row['risk_status']}</span>
#         """
#         folium.CircleMarker(
#             location=[row['latitude'], row['longitude']],
#             radius=10,
#             color=row['risk_color'],
#             fill=True,
#             fill_color=row['risk_color'],
#             fill_opacity=0.8,
#             popup=folium.Popup(popup, max_width=250),
#             tooltip=f"{row['point_id']}"
#         ).add_to(m)
#     return m

# # 📑 Табы
# tab1, tab2 = st.tabs(["📝 Manual Entry", "📂 CSV Upload"])

# # ================= TAB 1: Manual Entry =================
# with tab1:
#     st.subheader("Enter measurement data point-by-point")
    
#     # Инициализация
#     if 'manual_df' not in st.session_state:
#         st.session_state.manual_df = pd.DataFrame(columns=INPUT_COLS)
#     if 'last_saved_df' not in st.session_state:
#         st.session_state.last_saved_df = pd.DataFrame(columns=INPUT_COLS)

#     col1, col2 = st.columns([1, 1])
#     with col1:
#         auto_id = st.toggle("🔄 Auto-generate IDs", value=True, key="auto_id_toggle")
#     with col2:
#         if st.button("➕ Add Point", use_container_width=True, key="add_point_btn"):
#             new_id = f"Point_{len(st.session_state.manual_df)+1}" if auto_id else ""
#             new_row = pd.DataFrame([{
#                 'point_id': new_id, 'latitude': 52.52, 'longitude': 13.41,
#                 'pH': 7.5, 'O2': 8.0, 'Cl': 50.0, 'NO3': 5.0, 'NH4': 300.0, 'PO4': 100.0, 'Chl': 100.0, 'temp': 18.0
#             }])
#             st.session_state.manual_df = pd.concat([st.session_state.manual_df, new_row], ignore_index=True)
#             st.rerun()

#     # ✅ ИСПРАВЛЕНИЕ #3: Правильная работа с data_editor
#     if len(st.session_state.manual_df) > 0:
#         st.markdown("### Edit Data Points")
        
#         # Отображаем таблицу с возможностью редактирования
#         edited_df = st.data_editor(
#             st.session_state.manual_df,
#             column_config={
#                 "point_id": st.column_config.TextColumn("ID", width="small"),
#                 "latitude": st.column_config.NumberColumn("Lat", min_value=-90, max_value=90, format="%.4f", width="small"),
#                 "longitude": st.column_config.NumberColumn("Lon", min_value=-180, max_value=180, format="%.4f", width="small"),
#                 "pH": st.column_config.NumberColumn("pH", min_value=0, max_value=14, step=0.1),
#                 "O2": st.column_config.NumberColumn("O₂", min_value=0),
#                 "Cl": st.column_config.NumberColumn("Cl", min_value=0),
#                 "NO3": st.column_config.NumberColumn("NO₃", min_value=0),
#                 "NH4": st.column_config.NumberColumn("NH₄", min_value=0),
#                 "PO4": st.column_config.NumberColumn("PO₄", min_value=0),
#                 "Chl": st.column_config.NumberColumn("Chl", min_value=0),
#                 "temp": st.column_config.NumberColumn("Temp", min_value=-10, max_value=50, step=0.1)
#             },
#             hide_index=True,
#             use_container_width=True,
#             key="manual_data_editor",
#             num_rows="dynamic"
#         )
        
#         # ✅ ИСПРАВЛЕНИЕ #3: Сохраняем только если данные реально изменились
#         if not edited_df.equals(st.session_state.last_saved_df):
#             st.session_state.manual_df = edited_df
#             st.session_state.last_saved_df = edited_df.copy()

#         # ✅ ИСПРАВЛЕНИЕ #1: Кнопки удаления с правильными индексами
#         st.markdown("### Delete Points")
#         cols = st.columns(min(len(st.session_state.manual_df), 5))
        
#         # Сбрасываем индекс для корректного удаления
#         df_reset = st.session_state.manual_df.reset_index(drop=True)
        
#         for idx in range(len(df_reset)):
#             row = df_reset.iloc[idx]
#             col_idx = idx % 5
#             with cols[col_idx]:
#                 if st.button(f"− {row['point_id'] or f'Row {idx+1}'}", 
#                            key=f"delete_{idx}", 
#                            type="secondary"):
#                     # ✅ ИСПРАВЛЕНИЕ #1: Удаляем по правильному индексу
#                     st.session_state.manual_df = df_reset.drop(idx).reset_index(drop=True)
#                     st.session_state.last_saved_df = st.session_state.manual_df.copy()
#                     st.rerun()

#     if st.button("🔍 Predict", type="primary", use_container_width=True, key="predict_btn"):
#         if len(st.session_state.manual_df) > 0:
#             st.session_state.results = predict_risk(st.session_state.manual_df)
#             st.success("✅ Prediction complete!")

# # ================= TAB 2: CSV Upload =================
# with tab2:
#     st.subheader("Upload a CSV file with measurement data")
    
#     st.markdown("📋 **Expected CSV Format:**")
#     example = pd.DataFrame([{
#         'point_id': 'Site_A', 'latitude': 52.5200, 'longitude': 13.4050,
#         'pH': 7.5, 'O2': 8.2, 'Cl': 50.0, 'NO3': 5.5, 'NH4': 350.0, 'PO4': 120.0, 'Chl': 150.0, 'temp': 18.5
#     }, {
#         'point_id': 'Site_B', 'latitude': 52.5300, 'longitude': 13.4150,
#         'pH': 8.1, 'O2': 6.5, 'Cl': 45.0, 'NO3': 12.0, 'NH4': 420.0, 'PO4': 180.0, 'Chl': 210.0, 'temp': 21.0
#     }])
#     st.dataframe(example, hide_index=True, use_container_width=True)
    
#     st.download_button("⬇️ Download Example CSV", example.to_csv(index=False).encode(), "example.csv", "text/csv")
    
#     uploaded = st.file_uploader("Choose CSV", type=["csv"])
#     if uploaded:
#         try:
#             csv_df = pd.read_csv(uploaded)
#             if all(c in csv_df.columns for c in INPUT_COLS):
#                 if st.button("🔍 Predict (CSV)", type="primary", use_container_width=True):
#                     st.session_state.results = predict_risk(csv_df)
#                     st.success("✅ Prediction complete!")
#             else:
#                 st.error(f"❌ Missing columns. Expected: {INPUT_COLS}")
#         except Exception as e:
#             st.error(f"❌ Error: {e}")

# # ================= ОБЩИЙ ВЫВОД & КАРТА =================
# if 'results' in st.session_state and st.session_state.results is not None:
#     res = st.session_state.results.copy()
    
#     if show_only_risk:
#         res = res[res['risk_status'] == 'BLOOM']
    
#     if res.empty:
#         st.info("🟢 No risky points with current filter.")
#     else:
#         # Карта
#         st.markdown("### 🗺️ Risk Map")
#         st_folium(render_map(res), width="100%", height=500)
        
#         # ✅ ИСПРАВЛЕНИЕ #2: Правильная таблица с цветами
#         st.markdown("### 📊 Results")
        
#         # Сохраняем исходные данные ДО форматирования
#         display_df = res[['point_id', 'latitude', 'longitude', 'risk_probability', 'risk_status']].copy()
        
#         # Форматируем для отображения
#         display_df['risk_probability'] = display_df['risk_probability'].apply(lambda x: f"{x:.1%}")
        
#         # Создаём HTML таблицу
#         html_table = '<div class="dataframe-container"><table><thead><tr>'
#         for col in display_df.columns:
#             html_table += f'<th style="background-color: #f0f0f0; font-weight: 600;">{col}</th>'
#         html_table += '</tr></thead><tbody>'
        
#         # ✅ ИСПРАВЛЕНИЕ #2: Правильная проверка статуса
#         for idx, row in display_df.iterrows():
#             # Проверяем исходный статус (до форматирования)
#             original_status = res.iloc[idx]['risk_status']
#             bg_color = '#ffe0e0' if original_status == 'BLOOM' else '#e0ffe0'
            
#             # Форматируем статус в бейдж
#             if original_status == 'BLOOM':
#                 status_html = f'<span class="status-badge status-bloom">🔴 {row["risk_status"]}</span>'
#             else:
#                 status_html = f'<span class="status-badge status-safe">🟢 {row["risk_status"]}</span>'
            
#             html_table += f'<tr style="background-color: {bg_color};">'
#             html_table += f'<td>{row["point_id"]}</td>'
#             html_table += f'<td>{row["latitude"]}</td>'
#             html_table += f'<td>{row["longitude"]}</td>'
#             html_table += f'<td>{row["risk_probability"]}</td>'
#             html_table += f'<td>{status_html}</td>'
#             html_table += '</tr>'
        
#         html_table += '</tbody></table></div>'
        
#         st.markdown(html_table, unsafe_allow_html=True)
        
#         # Скачивание
#         csv_cols = ['point_id', 'latitude', 'longitude', 'pH', 'O2', 'Cl', 'NO3', 'NH4', 'PO4', 'Chl', 'temp', 'risk_probability', 'risk_status']
#         csv_data = res[csv_cols].copy()
#         csv_data['risk_probability'] = csv_data['risk_probability'].apply(lambda x: f'{x:.1%}')
#         csv_out = csv_data.to_csv(index=False).encode()
        
#         st.download_button("⬇️ Download Results (CSV)", csv_out, "results.csv", "text/csv")
# else:
#     st.info("👈 Enter data in tabs above and click **Predict**")





# app.py — УПРОЩЁННАЯ СТАБИЛЬНАЯ ВЕРСИЯ
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import os
import folium
from streamlit_folium import st_folium
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(layout="wide", page_title="Wetland Bloom Predictor", page_icon="🌊")

# 🎨 Стилизация
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #0068c9; margin-bottom: 1rem;}
    .status-badge {padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.9rem; display: inline-block;}
    .status-bloom {background-color: #ffe0e0; color: #c00; border: 1px solid #fcc;}
    .status-safe {background-color: #e0ffe0; color: #080; border: 1px solid #cfc;}
    .dataframe-container table {border-collapse: collapse; width: 100%;}
    .dataframe-container th, .dataframe-container td {padding: 8px; text-align: left; border: 1px solid #ddd;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🌊 Wetland Algal Bloom Risk Predictor</div>', unsafe_allow_html=True)
st.caption("AI-powered early warning system for harmful algal blooms (HABs).")

# 🔐 Загрузка моделей
@st.cache_resource
def load_artifacts():
    required = ['models/ensemble_model.pkl', 'models/scaler.pkl', 'models/config.json']
    if not all(os.path.exists(f) for f in required):
        st.error("🚨 Models not found! Run `python train_model.py` first.")
        st.stop()
    try:
        model = joblib.load('models/ensemble_model.pkl')
        scaler = joblib.load('models/scaler.pkl')
        with open('models/config.json', 'r') as f:
            config = json.load(f)
        return model, scaler, config
    except Exception as e:
        st.error(f"❌ Error loading models: {e}")
        st.stop()

model, scaler, config = load_artifacts()
THRESHOLD = config['threshold']
FEATURES = config['selected_features']
INPUT_COLS = config['input_columns']

# 🔍 Сайдбар
st.sidebar.title("🔍 Filters")
show_only_risk = st.sidebar.checkbox("🔴 Show only BLOOM points", value=False)
st.sidebar.info(f"**Threshold:** {THRESHOLD:.3f}")

def predict_risk(df_raw):
    df = df_raw.copy()
    df['N_P_ratio'] = df['NO3'] / (df['PO4'] + 0.01)
    df['nutrient_load'] = df['NO3'] + df['NH4'] + df['PO4']
    if df[FEATURES].isnull().any().any():
        df[FEATURES] = df[FEATURES].fillna(df[FEATURES].median())
    X_scaled = scaler.transform(df[FEATURES])
    probs = model.predict_proba(X_scaled)[:, 1]
    preds = (probs >= THRESHOLD).astype(int)
    df['risk_probability'] = probs
    df['risk_status'] = ['BLOOM' if p else 'NO_BLOOM' for p in preds]
    df['risk_color'] = ['#ff4b4b' if p else '#00cc66' for p in preds]
    return df

# 🗺️ Карта
def render_map(df):
    if df.empty or df['latitude'].isnull().all():
        return folium.Map(location=[52.52, 13.40], zoom_start=5)
    center = [df['latitude'].mean(), df['longitude'].mean()]
    m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")
    for _, row in df.iterrows():
        popup = f"""
        <b>ID:</b> {row['point_id']}<br>
        <b>Coords:</b> {row['latitude']:.4f}, {row['longitude']:.4f}<br>
        <b>Risk:</b> {row['risk_probability']:.1%}<br>
        <b>Status:</b> <span style="color:{row['risk_color']}">{row['risk_status']}</span>
        """
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=10, color=row['risk_color'], fill=True,
            fill_color=row['risk_color'], fill_opacity=0.8,
            popup=folium.Popup(popup, max_width=250),
            tooltip=f"{row['point_id']}"
        ).add_to(m)
    return m

# 📑 Табы
tab1, tab2 = st.tabs(["📝 Manual Entry", "📂 CSV Upload"])

# ================= TAB 1: Manual Entry (УПРОЩЁННЫЙ) =================
with tab1:
    st.subheader("Enter measurement data point-by-point")
    st.info("💡 Use the **+** button below the table to add rows, or click the **trash icon** in a row to delete it.")
    
    # ✅ Инициализация: сразу одна строка по умолчанию
    if 'manual_df' not in st.session_state or len(st.session_state.manual_df) == 0:
        st.session_state.manual_df = pd.DataFrame([{
            'point_id': 'Point_1', 'latitude': 52.52, 'longitude': 13.41,
            'pH': 7.5, 'O2': 8.0, 'Cl': 50.0, 'NO3': 5.0, 'NH4': 300.0, 'PO4': 100.0, 'Chl': 100.0, 'temp': 18.0
        }])

    # ✅ Простой data_editor с встроенными кнопками +/-
    edited_df = st.data_editor(
        st.session_state.manual_df,
        column_config={
            "point_id": st.column_config.TextColumn("ID", width="small"),
            "latitude": st.column_config.NumberColumn("Lat", min_value=-90, max_value=90, format="%.4f", width="small"),
            "longitude": st.column_config.NumberColumn("Lon", min_value=-180, max_value=180, format="%.4f", width="small"),
            "pH": st.column_config.NumberColumn("pH", min_value=0, max_value=14, step=0.1),
            "O2": st.column_config.NumberColumn("O₂", min_value=0),
            "Cl": st.column_config.NumberColumn("Cl", min_value=0),
            "NO3": st.column_config.NumberColumn("NO₃", min_value=0),
            "NH4": st.column_config.NumberColumn("NH₄", min_value=0),
            "PO4": st.column_config.NumberColumn("PO₄", min_value=0),
            "Chl": st.column_config.NumberColumn("Chl", min_value=0),
            "temp": st.column_config.NumberColumn("Temp", min_value=-10, max_value=50, step=0.1)
        },
        hide_index=True,
        use_container_width=True,
        key="manual_editor",
        num_rows="dynamic"  # ✅ Встроенные кнопки + и −
    )
    
    # Сохраняем изменения
    st.session_state.manual_df = edited_df

    # Кнопка предсказания
    if st.button("🔍 Run Prediction", type="primary", use_container_width=True):
        if len(st.session_state.manual_df) > 0:
            st.session_state.results = predict_risk(st.session_state.manual_df)
            st.success("✅ Prediction complete!")

# ================= TAB 2: CSV Upload (без изменений) =================
with tab2:
    st.subheader("Upload a CSV file with measurement data")
    
    st.markdown("📋 **Expected CSV Format:**")
    example = pd.DataFrame([{
        'point_id': 'Site_A', 'latitude': 52.5200, 'longitude': 13.4050,
        'pH': 7.5, 'O2': 8.2, 'Cl': 50.0, 'NO3': 5.5, 'NH4': 350.0, 'PO4': 120.0, 'Chl': 150.0, 'temp': 18.5
    }, {
        'point_id': 'Site_B', 'latitude': 52.5300, 'longitude': 13.4150,
        'pH': 8.1, 'O2': 6.5, 'Cl': 45.0, 'NO3': 12.0, 'NH4': 420.0, 'PO4': 180.0, 'Chl': 210.0, 'temp': 21.0
    }])
    st.dataframe(example, hide_index=True, use_container_width=True)
    st.download_button("⬇️ Download Example CSV", example.to_csv(index=False).encode(), "example.csv", "text/csv")
    
    uploaded = st.file_uploader("Choose CSV", type=["csv"])
    if uploaded:
        try:
            csv_df = pd.read_csv(uploaded)
            if all(c in csv_df.columns for c in INPUT_COLS):
                if st.button("🔍 Run Prediction (CSV)", type="primary", use_container_width=True):
                    st.session_state.results = predict_risk(csv_df)
                    st.success("✅ Prediction complete!")
            else:
                st.error(f"❌ Missing columns. Expected: {INPUT_COLS}")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ================= ОБЩИЙ ВЫВОД & КАРТА =================
if 'results' in st.session_state and st.session_state.results is not None:
    res = st.session_state.results.copy()
    
    if show_only_risk:
        res = res[res['risk_status'] == 'BLOOM']
    
    if res.empty:
        st.info("🟢 No risky points with current filter.")
    else:
        # Карта
        st.markdown("### 🗺️ Risk Map")
        st_folium(render_map(res), width="100%", height=500)
        
        # Таблица результатов
        st.markdown("### 📊 Results")
        display_df = res[['point_id', 'latitude', 'longitude', 'risk_probability', 'risk_status']].copy()
        display_df['risk_probability'] = display_df['risk_probability'].apply(lambda x: f"{x:.1%}")
        
        # HTML таблица с цветами
        html_table = '<div class="dataframe-container"><table><thead><tr>'
        for col in display_df.columns:
            html_table += f'<th style="background-color: #f0f0f0; font-weight: 600;">{col}</th>'
        html_table += '</tr></thead><tbody>'
        
        for idx, row in display_df.iterrows():
            original_status = res.iloc[idx]['risk_status']
            bg_color = '#ffe0e0' if original_status == 'BLOOM' else '#e0ffe0'
            status_html = f'<span class="status-badge status-bloom">🔴 {row["risk_status"]}</span>' if original_status == 'BLOOM' else f'<span class="status-badge status-safe">🟢 {row["risk_status"]}</span>'
            
            html_table += f'<tr style="background-color: {bg_color};">'
            html_table += f'<td>{row["point_id"]}</td><td>{row["latitude"]}</td><td>{row["longitude"]}</td><td>{row["risk_probability"]}</td><td>{status_html}</td>'
            html_table += '</tr>'
        
        html_table += '</tbody></table></div>'
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Экспорт
        csv_cols = ['point_id', 'latitude', 'longitude', 'pH', 'O2', 'Cl', 'NO3', 'NH4', 'PO4', 'Chl', 'temp', 'risk_probability', 'risk_status']
        csv_data = res[csv_cols].copy()
        csv_data['risk_probability'] = csv_data['risk_probability'].apply(lambda x: f'{x:.1%}')
        st.download_button("⬇️ Download Results (CSV)", csv_data.to_csv(index=False).encode(), "results.csv", "text/csv")
else:
    st.info("👈 Enter data in the Manual Entry tab and click **Run Prediction**")