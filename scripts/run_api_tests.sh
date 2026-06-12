#!/usr/bin/env bash
set -euo pipefail
BASE=http://127.0.0.1:8000
echo "API 测试开始：$BASE"

call(){
  local method=${1:-GET}
  local url=$2
  local data=${3:-}
  echo "==> $method $url"
  if [ "$method" = "GET" ]; then
    curl -sS -m 10 -w "\nHTTP_CODE:%{http_code}\n---\n" "$BASE$url" || echo "(请求失败)";
  else
    curl -sS -m 20 -X $method -H "Content-Type: application/json" -d "$data" -w "\nHTTP_CODE:%{http_code}\n---\n" "$BASE$url" || echo "(请求失败)";
  fi
}

echo "基础接口"
call GET /api/data/summary
call GET /api/data/full_clean

echo "统计接口"
call GET /api/stat/year_count
call GET /api/stat/type_box
call GET /api/stat/area_dist
call GET /api/stat/duration_score
call GET /api/stat/hot_dist
call GET /api/stat/behavior_ratio
call GET /api/stat/score_box
call GET /api/stat/type_watch

echo "用户接口"
call GET "/api/user/age_prefer"
call GET "/api/user/gender_prefer"
call GET "/api/user/vip_behavior"

echo "排行榜与热度"
call GET "/api/rank/hot_top?n=5"
call GET /api/rank/hot_cold_dist
call GET /api/rank/box_score_mismatch
call GET /api/rank/hot_decay

echo "模型接口（注意：可能较慢，等待 20s 超时）"
call POST /api/model/all_compare '{}'
call GET /api/model/feature_import
call POST /api/model/predict '{"duration":100,"score_avg":7.0,"release_year":2022}'

echo "推荐接口"
call GET "/api/recommend/movie_similar?movie_id=1&topn=5"
call GET "/api/recommend/user_personal?user_id=1&topn=5"

echo "测试完成"
