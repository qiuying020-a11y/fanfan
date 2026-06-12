import os
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), '..', '期末', '数据源')


def _read_csv(name):
    path = os.path.join(ROOT, name)
    return pd.read_csv(path)


def load_movie_info():
    return _read_csv('movie_info.csv')


def load_movie_box():
    return _read_csv('movie_box_data.csv')


def load_user_behavior():
    return _read_csv('user_behavior.csv')


def load_user_info():
    return _read_csv('user_info.csv')


def load_user_score():
    return _read_csv('user_score.csv')


def load_all():
    return {
        'movie_info': load_movie_info(),
        'movie_box': load_movie_box(),
        'user_behavior': load_user_behavior(),
        'user_info': load_user_info(),
        'user_score': load_user_score(),
    }
