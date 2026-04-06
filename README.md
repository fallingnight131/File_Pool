# FilePool

FilePool 是一个无需注册的临时文件共享池，支持本地文件上传和外链入池。

## 技术栈

- 后端：Python 3.11、Flask、SQLite、APScheduler
- 前端：Vue 3（Composition API）、Vite、手写 CSS

## 目录结构

```text
filepool/
├── backend/
├── frontend/
├── deploy/
└── README.md
```

## 本地开发启动

### 1) 启动后端

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
也可以用conda创建环境
```bash
cd backend
conda create -n filepool python=3.11 -y
conda activate filepool
pip install -r requirements.txt
python app.py
```

后端默认在 http://localhost:5001

### 2) 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认在 http://localhost:5173，且已通过 Vite 代理转发 `/api` 到后端。

## API 概览

- `POST /api/upload`：上传本地文件（字段：`files[]`）
- `POST /api/link`：上传外链
- `GET /api/files`：获取文件池列表
- `DELETE /api/files`：批量删除
- `GET /api/download/<id>`：下载本地文件或重定向外链
- `GET /api/stats`：获取容量统计

## 生产部署

请查看 [DEPLOYMENT_UBUNTU_ALIYUN.md](DEPLOYMENT_UBUNTU_ALIYUN.md)
