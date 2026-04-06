# FilePool 宝塔部署（精简版）

适用场景：
- 域名：fallingnight.cn
- 只部署 FilePool
- Nginx 由宝塔管理

## 1. 准备目录

项目目录：
- /www/wwwroot/filepool

前端发布目录（默认）：
- /www/wwwroot/filepool/frontend/dist

## 2. 一键部署

在服务器执行：

```bash
cd /www/wwwroot/filepool
bash deploy/deploy_ubuntu.sh
```

脚本会完成：
1. 检查 Python（>=3.8）
2. 创建后端虚拟环境并安装依赖
3. 构建前端
4. 发布前端到默认目录

如果你要指定 Python：

```bash
cd /www/wwwroot/filepool
PYTHON_BIN=python3.11 bash deploy/deploy_ubuntu.sh
```

## 3. 启动后端

```bash
cd /www/wwwroot/filepool/backend
source .venv/bin/activate
gunicorn -w 2 -b 127.0.0.1:5001 app:app
```

建议在宝塔进程守护中配置上面命令实现开机自启。

## 4. Nginx 配置

仅保留这个配置模板：
- deploy/nginx-fallingnight-filepool-only.conf

把该文件内容复制到宝塔站点 fallingnight.cn 配置中。

重载命令（宝塔）：

```bash
nginx -t
/etc/init.d/nginx reload
```

## 5. 验证

```bash
ss -lntp | grep 5001
curl -i http://127.0.0.1:5001/api/stats
curl -i https://fallingnight.cn/api/stats
```

期望：
- 5001 有监听
- 两个 stats 都返回 200

## 6. 常见问题

1. 上传时报网络错误：通常是后端没跑，先看 5001 是否监听。
2. 502 Bad Gateway：Nginx 代理到了 127.0.0.1:5001，但后端未启动。
3. 大文件上传失败：在站点 server 内加 `client_max_body_size 1024m;` 后重载 Nginx。
