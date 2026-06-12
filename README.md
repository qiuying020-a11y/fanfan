# 电影数据分析与可视化平台（示例）

这是根据课程期末项目需求手册实现的前后端示例项目。后端使用 FastAPI 提供接口并托管前端静态页面，前端使用 ECharts 做可视化示例。

快速使用（本地开发）：

1. 创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. 启动服务：

```bash
./start.sh
# 或
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

访问： http://127.0.0.1:8000

容器化（Docker）：

1. 使用 Docker Compose 构建并运行：

```bash
docker compose up --build -d
```

2. 停止并移除：

```bash
docker compose down
```

说明：
- 数据文件存放在 `期末/数据源/`，docker-compose 会把该目录以只读方式挂载到容器内，确保容器使用本地数据。  
- 后端主要文件： `backend/main.py`、`backend/data_loader.py`、`backend/ml_models.py`、`backend/recommend.py`。  
- 前端页面位于 `frontend/`，由后端静态挂载提供。  

如需我为你在仓库中添加 CI、测试脚本或把项目打包为镜像并推到 registry，我可以继续操作。 
# fanfan