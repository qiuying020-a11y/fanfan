import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


def movie_similar(movie_id, movie_info, topn=10):
    df = movie_info.copy()
    df['movie_type'] = df['movie_type'].fillna('')
    df['type_vec'] = df['movie_type'].apply(lambda s: [t.strip() for t in str(s).split(',') if t.strip()])
    # build binary features for types
    types = sorted({t for row in df['type_vec'] for t in row})
    for t in types:
        df[f'type_{t}'] = df['type_vec'].apply(lambda lst: 1 if t in lst else 0)
    feat_cols = [c for c in df.columns if c.startswith('type_')]
    if not feat_cols:
        return []
    try:
        df[feat_cols] = df[feat_cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
        mat = df[feat_cols].values
        sim = cosine_similarity(mat)
    except Exception:
        return []
    idx = df.index[df['movie_id'] == movie_id].tolist()
    if not idx:
        return []
    i = idx[0]
    scores = list(enumerate(sim[i]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    res = []
    for j, s in scores[1:topn+1]:
        row = df.iloc[j]
        res.append({
            'movie_id': int(row['movie_id']),
            'movie_name': row.get('movie_name', ''),
            'movie_type': row.get('movie_type', ''),
            'similarity': float(s)
        })
    return res


def user_personal(user_id, user_score, movie_info, topn=10):
    ratings = user_score.copy()
    if ratings.empty:
        return []
    score_col = 'score' if 'score' in ratings.columns else ('user_score' if 'user_score' in ratings.columns else None)
    if score_col is None:
        return []
    try:
        top_movies = ratings['movie_id'].value_counts().head(1000).index
        ratings_small = ratings[ratings['movie_id'].isin(top_movies)]
        pivot = ratings_small.pivot_table(index='user_id', columns='movie_id', values=score_col).fillna(0)
    except Exception as e:
        print(f"[recommend:user_personal] pivot build error: {e}")
        return []

    movie_details = movie_info.set_index('movie_id')[['movie_name', 'movie_type', 'score_avg']] if 'score_avg' in movie_info.columns else movie_info.set_index('movie_id')[['movie_name', 'movie_type']]
    movie_box = None
    if 'movie_box' in globals():
        movie_box = globals()['movie_box']

    if user_id not in pivot.index:
        sort_field = 'hot_score' if 'hot_score' in movie_info.columns else ('score_avg' if 'score_avg' in movie_info.columns else 'movie_id')
        popular = movie_info.sort_values(by=sort_field, ascending=False).head(topn)
        res = []
        for _, row in popular.iterrows():
            res.append({
                'movie_id': int(row['movie_id']),
                'movie_name': row.get('movie_name', ''),
                'movie_type': row.get('movie_type', ''),
                'box_office': float(row['box_office']) if 'box_office' in row and pd.notna(row['box_office']) else None,
                'score_avg': float(row['score_avg']) if 'score_avg' in row and pd.notna(row['score_avg']) else None,
                'recommend_score': float(row.get(sort_field, 0))
            })
        return res

    user_vec = pivot.loc[user_id].values.reshape(1, -1)
    sims = cosine_similarity(user_vec, pivot.values)[0]
    sim_series = pd.Series(sims, index=pivot.index).drop(user_id)
    top_users = sim_series.sort_values(ascending=False).head(10).index
    try:
        recs = ratings[ratings['user_id'].isin(top_users)].groupby('movie_id')[score_col].mean()
    except Exception:
        return []
    seen = set(ratings[ratings['user_id'] == user_id]['movie_id'].tolist())
    recs = recs[~recs.index.isin(seen)].sort_values(ascending=False).head(topn)
    res = []
    for mid, sc in recs.items():
        if mid in movie_details.index:
            row = movie_details.loc[mid]
            res.append({
                'movie_id': int(mid),
                'movie_name': row.get('movie_name', ''),
                'movie_type': row.get('movie_type', ''),
                'score_avg': float(row['score_avg']) if 'score_avg' in row and pd.notna(row['score_avg']) else None,
                'recommend_score': float(sc)
            })
        else:
            res.append({
                'movie_id': int(mid),
                'movie_name': '',
                'movie_type': '',
                'score_avg': None,
                'recommend_score': float(sc)
            })
    if not res:
        sort_field = 'hot_score' if 'hot_score' in movie_info.columns else ('score_avg' if 'score_avg' in movie_info.columns else 'movie_id')
        popular = movie_info[~movie_info['movie_id'].isin(list(seen))].sort_values(by=sort_field, ascending=False).head(topn)
        for _, row in popular.iterrows():
            res.append({
                'movie_id': int(row['movie_id']),
                'movie_name': row.get('movie_name', ''),
                'movie_type': row.get('movie_type', ''),
                'score_avg': float(row['score_avg']) if 'score_avg' in row and pd.notna(row['score_avg']) else None,
                'recommend_score': float(row.get(sort_field, 0))
            })
    return res
