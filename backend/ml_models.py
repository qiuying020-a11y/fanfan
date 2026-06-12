import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os


MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)


def _prepare_features(movie_info, movie_box):
    df = pd.merge(movie_info, movie_box, on='movie_id')
    # select simple numeric features
    df = df.dropna(subset=['duration', 'score_avg', 'box_office', 'release_year'])
    X = df[['duration', 'score_avg', 'release_year']].copy()
    y = df['box_office']
    return X, y, df


def train_and_compare(movie_info, movie_box):
    X, y, df = _prepare_features(movie_info, movie_box)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        'linear': LinearRegression(),
        'tree': DecisionTreeRegressor(random_state=42),
        'rf': RandomForestRegressor(n_estimators=50, random_state=42)
    }
    results = {}
    for name, m in models.items():
        m.fit(X_train, y_train)
        pred = m.predict(X_test)
        results[name] = {
            'mae': float(mean_absolute_error(y_test, pred)),
            'mse': float(mean_squared_error(y_test, pred)),
            'sample_pred': float(pred[0]) if len(pred)>0 else None
        }
        joblib.dump(m, os.path.join(MODEL_DIR, f'{name}.joblib'))

    return results


def feature_importances(movie_info, movie_box):
    X, y, df = _prepare_features(movie_info, movie_box)
    rf = RandomForestRegressor(n_estimators=50, random_state=42)
    rf.fit(X, y)
    feats = list(X.columns)
    imps = rf.feature_importances_.tolist()
    return list(zip(feats, [float(x) for x in imps]))


def predict(params: dict):
    # params: duration, score_avg, release_year
    path = MODEL_DIR
    res = {}
    feat = [[params.get('duration', 100), params.get('score_avg', 5.0), params.get('release_year', 2020)]]
    for name in ['linear', 'tree', 'rf']:
        p = os.path.join(path, f'{name}.joblib')
        if os.path.isfile(p):
            m = joblib.load(p)
            pred = m.predict(feat)[0]
            res[name] = float(pred)
        else:
            res[name] = None
    return res
