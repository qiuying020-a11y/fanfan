import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

from .data_loader import load_all


app = FastAPI(title='电影数据分析 API')

# Load data once at import time and again at startup.
# This ensures DATA is available during tests and when the server starts.
DATA = {}
try:
    DATA = load_all()
except Exception as e:
    print(f"[main] initial load_all failed: {e}")


@app.on_event('startup')
def startup_event():
    global DATA
    if not DATA:
        DATA = load_all()


def json_ok(data):
    return JSONResponse({'code': 0, 'message': 'ok', 'data': data})


@app.get('/api/data/summary')
def data_summary():
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    ub = DATA['user_behavior']
    return json_ok({
        'movie_count': int(mi.shape[0]),
        'box_count': int(mb.shape[0]),
        'behavior_count': int(ub.shape[0]),
    })


@app.get('/api/stat/year_count')
def year_count():
    mi = DATA['movie_info']
    if 'release_year' not in mi.columns:
        raise HTTPException(400, 'release_year 列缺失')
    s = mi.groupby('release_year').size().reset_index(name='count').sort_values('release_year')
    return json_ok(s.to_dict(orient='records'))


@app.get('/api/stat/type_box')
def type_box():
    mi = DATA['movie_info'].copy()
    mb = DATA['movie_box']
    merged = pd.merge(mi, mb, on='movie_id')
    # explode types
    merged['movie_type'] = merged['movie_type'].fillna('未知')
    merged['movie_type'] = merged['movie_type'].astype(str)
    merged = merged.assign(type=merged['movie_type'].str.split(','))
    merged = merged.explode('type')
    res = merged.groupby('type').agg(avg_box=('box_office', 'mean'), total_box=('box_office', 'sum'), cnt=('movie_id','count')).reset_index()
    res = res.sort_values('avg_box', ascending=False)
    res['avg_box'] = res['avg_box'].round(2)
    res['total_box'] = res['total_box'].round(2)
    return json_ok(res.to_dict(orient='records'))


@app.get('/api/rank/hot_top')
def hot_top(n: int = 10):
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    merged = pd.merge(mi, mb, on='movie_id')
    top = merged.sort_values('box_office', ascending=False).head(n)
    return json_ok(top[['movie_id', 'movie_name', 'box_office', 'hot_score']].to_dict(orient='records'))


@app.get('/api/data/full_clean')
def data_full_clean():
    # very small cleaning report
    report = {}
    for k, df in DATA.items():
        report[k] = {
            'rows': int(df.shape[0]),
            'cols': int(df.shape[1]),
            'missing_per_column': df.isnull().sum().to_dict()
        }
    return json_ok(report)


@app.get('/api/stat/area_dist')
def area_dist():
    mi = DATA['movie_info']
    s = mi.groupby('movie_area').size().reset_index(name='count').sort_values('count', ascending=False)
    return json_ok(s.to_dict(orient='records'))


@app.get('/api/stat/duration_score')
def duration_score():
    mi = DATA['movie_info']
    bins = [0, 80, 100, 120, 140, 9999]
    labels = ['<=80','81-100','101-120','121-140','>140']
    mi['dur_bin'] = pd.cut(mi['duration'], bins=bins, labels=labels)
    res = mi.groupby('dur_bin').agg(avg_score=('score_avg','mean'), cnt=('movie_id','count')).reset_index()
    return json_ok(res.fillna(0).to_dict(orient='records'))


@app.get('/api/stat/hot_dist')
def hot_dist():
    mb = DATA['movie_box']
    q = mb['hot_score'].quantile([0.33,0.66]).tolist()
    def tag(h):
        if h<=q[0]:
            return '低热度'
        if h<=q[1]:
            return '中热度'
        return '高热度'
    mb['level'] = mb['hot_score'].apply(tag)
    s = mb.groupby('level').size().reset_index(name='count')
    return json_ok(s.to_dict(orient='records'))


@app.get('/api/stat/behavior_ratio')
def behavior_ratio():
    ub = DATA['user_behavior']
    s = ub.groupby('behavior_type').size().reset_index(name='count')
    s['ratio'] = (s['count'] / s['count'].sum()).round(4)
    return json_ok(s.to_dict(orient='records'))


@app.get('/api/stat/score_box')
def score_box():
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    merged = pd.merge(mi, mb, on='movie_id')
    bins = [0,4,6,8,10]
    labels = ['0-4','4-6','6-8','8-10']
    merged['score_bin'] = pd.cut(merged['score_avg'], bins=bins, labels=labels)
    res = merged.groupby('score_bin').agg(avg_box=('box_office','mean'), cnt=('movie_id','count')).reset_index()
    return json_ok(res.fillna(0).to_dict(orient='records'))


@app.get('/api/stat/type_watch')
def type_watch():
    mi = DATA['movie_info'].copy()
    mb = DATA['movie_box']
    merged = pd.merge(mi, mb, on='movie_id')
    merged['movie_type'] = merged['movie_type'].fillna('未知')
    merged = merged.assign(type=merged['movie_type'].str.split(',')).explode('type')
    res = merged.groupby('type').agg(total_watch=('watch_people','sum')).reset_index().sort_values('total_watch', ascending=False)
    return json_ok(res.to_dict(orient='records'))


# User analysis endpoints
@app.get('/api/user/age_prefer')
def age_prefer():
    ui = DATA['user_info']
    us = DATA['user_score']
    mi = DATA['movie_info']
    merged = pd.merge(us, ui, on='user_id')
    merged = pd.merge(merged, mi[['movie_id','movie_type']], on='movie_id')
    merged['age_group'] = pd.cut(merged['user_age'], bins=[0,18,30,45,60,999], labels=['<=18','19-30','31-45','46-60','>60'])
    result = []
    for age_group, grp in merged.groupby('age_group'):
        types = grp['movie_type'].fillna('未知').astype(str).str.get_dummies(sep=',').sum().sort_values(ascending=False)
        top_types = types.head(3).reset_index().rename(columns={'index':'movie_type', 0:'count'}).to_dict(orient='records')
        result.append({'age_group': str(age_group), 'top_types': top_types})
    return json_ok(result)


@app.get('/api/user/gender_prefer')
def gender_prefer():
    ui = DATA['user_info']
    us = DATA['user_score']
    mi = DATA['movie_info']
    merged = pd.merge(us, ui, on='user_id')
    merged = pd.merge(merged, mi[['movie_id','movie_type']], on='movie_id')
    result = []
    for gender, grp in merged.groupby('user_gender'):
        types = grp['movie_type'].fillna('未知').astype(str).str.get_dummies(sep=',').sum().sort_values(ascending=False)
        top_types = types.head(5).reset_index().rename(columns={'index':'movie_type', 0:'count'}).to_dict(orient='records')
        result.append({'gender': str(gender), 'top_types': top_types})
    return json_ok(result)


@app.get('/api/user/vip_behavior')
def vip_behavior():
    ui = DATA['user_info']
    ub = DATA['user_behavior']
    merged = pd.merge(ub, ui[['user_id','user_level']], on='user_id')
    s = merged.groupby(['user_level','behavior_type']).size().reset_index(name='count')
    return json_ok(s.to_dict(orient='records'))


# Rank endpoints
@app.get('/api/rank/hot_cold_dist')
def hot_cold_dist():
    mb = DATA['movie_box']
    q = mb['hot_score'].quantile([0.33,0.66]).tolist()
    def tag(h):
        if h<=q[0]:
            return '冷门'
        if h<=q[1]:
            return '普通'
        return '热门'
    mb['tier'] = mb['hot_score'].apply(tag)
    s = mb.groupby('tier').size().reset_index(name='count')
    return json_ok(s.to_dict(orient='records'))


@app.get('/api/rank/box_score_mismatch')
def box_score_mismatch():
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    merged = pd.merge(mi, mb, on='movie_id')
    high_box_low_score = merged[(merged['box_office']>merged['box_office'].quantile(0.75)) & (merged['score_avg']<merged['score_avg'].quantile(0.25))]
    low_box_high_score = merged[(merged['box_office']<merged['box_office'].quantile(0.25)) & (merged['score_avg']>merged['score_avg'].quantile(0.75))]
    return json_ok({'high_box_low_score': high_box_low_score[['movie_id','movie_name','box_office','score_avg']].to_dict(orient='records'), 'low_box_high_score': low_box_high_score[['movie_id','movie_name','box_office','score_avg']].to_dict(orient='records')})


@app.get('/api/rank/hot_decay')
def hot_decay():
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    merged = pd.merge(mi[['movie_id','release_year']], mb[['movie_id','hot_score']], on='movie_id')
    res = merged.groupby('release_year').agg(avg_hot=('hot_score','mean')).reset_index().sort_values('release_year')
    return json_ok(res.to_dict(orient='records'))


# Factor analysis endpoint
@app.get('/api/factor/box_analysis')
def box_analysis():
    from .ml_models import feature_importances
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    merged = pd.merge(mi, mb, on='movie_id')
    merged = merged.dropna(subset=['duration', 'score_avg', 'release_year', 'box_office'])
    feats = ['duration', 'score_avg', 'release_year', 'hot_score']
    correlations = {}
    for feat in feats:
        if feat in merged.columns:
            corr = merged[feat].corr(merged['box_office'])
            correlations[feat] = float(corr) if pd.notna(corr) else 0.0
    importances = feature_importances(mi, mb)
    importance_dict = {name: imp for name, imp in importances}
    res = {
        'correlations': correlations,
        'feature_importances': importance_dict
    }
    return json_ok(res)


# Model endpoints
@app.post('/api/model/all_compare')
def model_all_compare():
    from .ml_models import train_and_compare
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    res = train_and_compare(mi, mb)
    return json_ok(res)


@app.get('/api/model/feature_import')
def model_feature_import():
    from .ml_models import feature_importances
    mi = DATA['movie_info']
    mb = DATA['movie_box']
    res = feature_importances(mi, mb)
    return json_ok(res)


@app.post('/api/model/predict')
def model_predict(params: dict):
    from .ml_models import predict
    res = predict(params)
    return json_ok(res)


# Recommend endpoints
@app.get('/api/recommend/movie_similar')
def api_movie_similar(movie_id: int, topn: int = 10):
    from .recommend import movie_similar
    mi = DATA['movie_info']
    res = movie_similar(movie_id, mi, topn=topn)
    return json_ok(res)


@app.get('/api/recommend/user_personal')
def api_user_personal(user_id: int, topn: int = 10):
    from .recommend import user_personal
    us = DATA['user_score']
    mi = DATA['movie_info']
    res = user_personal(user_id, us, mi, topn=topn)
    return json_ok(res)


# Serve frontend static files from ../frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
if os.path.isdir(frontend_path):
    app.mount('/', StaticFiles(directory=frontend_path, html=True), name='frontend')
