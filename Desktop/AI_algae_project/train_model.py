# train_model.py — для sklearn==1.3.2
import pandas as pd
import numpy as np
import os
import joblib
import json
import warnings
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_recall_curve

warnings.filterwarnings('ignore')

print("="*70)
print("🚀 TRAINING & SAVING PIPELINE (sklearn==1.3.2)")
print("="*70)
print(f"📦 sklearn: {pd.__version__}, joblib: {joblib.__version__}")

# 1. Загрузка данных
if not os.path.exists('data/analysis.data'):
    print("❌ data/analysis.data not found!")
    exit(1)

df = pd.read_csv('data/analysis.data', header=None, sep=',')
columns = [
    'season', 'river_size', 'flow_velocity',
    'pH', 'O2', 'Cl', 'NO3', 'NH4', 'PO4', 'Chl', 'temp',
    'algae_a', 'algae_b', 'algae_c', 'algae_d', 
    'algae_e', 'algae_f', 'algae_g'
]
df.columns = columns

# 2. Очистка
features_raw = ['pH', 'O2', 'Cl', 'NO3', 'NH4', 'PO4', 'Chl', 'temp']
algae_cols = [f'algae_{x}' for x in 'abcdefg']
df[features_raw] = df[features_raw].apply(pd.to_numeric, errors='coerce')
df[algae_cols] = df[algae_cols].apply(pd.to_numeric, errors='coerce')
df[features_raw] = df[features_raw].fillna(df[features_raw].median())
df[algae_cols] = df[algae_cols].fillna(0)

# 3. Таргет
df['total_algae'] = df[algae_cols].sum(axis=1)
df['bloom_binary'] = df['total_algae'].apply(lambda x: 1 if x > 50 else 0)

# 4. Feature Engineering
df['N_P_ratio'] = df['NO3'] / (df['PO4'] + 0.01)
df['nutrient_load'] = df['NO3'] + df['NH4'] + df['PO4']

selected_features = ['NO3', 'NH4', 'PO4', 'temp', 'O2', 'N_P_ratio', 'nutrient_load']
X = df[selected_features].copy()
y = df['bloom_binary'].copy()

# 5. Разделение и масштабирование
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 6. Ensemble Model
estimators = [
    ('gb', GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, min_samples_leaf=5, random_state=42)),
    ('rf', RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=4, class_weight='balanced', random_state=42, n_jobs=-1)),
    ('lr', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42, solver='lbfgs'))
]
voting_model = VotingClassifier(estimators=estimators, voting='soft')
voting_model.fit(X_train_scaled, y_train)

# 7. Threshold Tuning
y_prob = voting_model.predict_proba(X_test_scaled)[:, 1]
precision, recall, thresholds = precision_recall_curve(y_test, y_prob)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
best_threshold = thresholds[np.argmax(f1_scores)] if len(thresholds) > 0 else 0.217

print(f"✅ Optimal Threshold: {best_threshold:.3f}")
print(f"✅ Model trained successfully on sklearn 1.3.2")

# 8. 💾 СОХРАНЕНИЕ (protocol=4 для совместимости)
os.makedirs('models', exist_ok=True)

# Удаляем старые файлы
for f in ['ensemble_model.pkl', 'scaler.pkl', 'config.json']:
    path = os.path.join('models', f)
    if os.path.exists(path):
        os.remove(path)

# Сохраняем с protocol=4 (универсальный для Python 3.7-3.11)
joblib.dump(voting_model, 'models/ensemble_model.pkl', protocol=4)
joblib.dump(scaler, 'models/scaler.pkl', protocol=4)

config = {
    'threshold': float(best_threshold),
    'selected_features': selected_features,
    'input_columns': ['point_id', 'latitude', 'longitude', 'pH', 'O2', 'Cl', 'NO3', 'NH4', 'PO4', 'Chl', 'temp'],
    'sklearn_version': '1.3.2'
}
with open('models/config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("💾 Saved to models/:")
print("   • ensemble_model.pkl")
print("   • scaler.pkl")
print("   • config.json")
print("🏁 Запусти: streamlit run app.py")