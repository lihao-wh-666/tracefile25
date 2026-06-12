# Platform Jumper - Docker 部署文档

## 目录

1. [项目概述](#项目概述)
2. [环境要求](#环境要求)
3. [快速开始](#快速开始)
4. [环境变量说明](#环境变量说明)
5. [多环境部署](#多环境部署)
6. [Dockerfile 架构说明](#dockerfile-架构说明)
7. [服务健康检查](#服务健康检查)
8. [VNC 远程访问](#vnc-远程访问)
9. [资源限制与优化](#资源限制与优化)
10. [网络与数据卷管理](#网络与数据卷管理)
11. [常见问题排查](#常见问题排查)
12. [升级与维护](#升级与维护)

---

## 项目概述

Platform Jumper 是一款基于 Pygame 开发的 2D 平台跳跃游戏。本项目提供完整的 Docker 容器化部署方案，支持开发、测试、生产三种环境，通过 VNC 协议远程访问游戏画面。

**核心特性：**
- 多阶段 Docker 构建，最小化镜像体积
- 开发/测试/生产多环境配置隔离
- VNC 远程画面访问支持
- 容器健康检查自动重启
- 资源限制与安全加固
- 数据卷持久化与日志管理

---

## 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Docker Engine | 20.10.0 | 24.0+ |
| Docker Compose | 2.0.0 | 2.20+ |
| 操作系统 | Linux / macOS / Windows 10+ | - |
| 内存 | 512MB | 1GB+ |
| CPU | 1 核 | 2 核+ |
| 磁盘空间 | 500MB | 2GB+ |

**安装 Docker：**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 验证安装
docker --version
docker compose version
```

---

## 快速开始

### 方式一：Docker Compose 一键部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd lh-25

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，根据需要修改配置

# 3. 构建镜像
docker compose --profile dev build

# 4. 启动服务
docker compose --profile dev up -d

# 5. 查看状态
docker compose --profile dev ps
docker compose --profile dev logs -f
```

### 方式二：纯 Docker 命令部署

```bash
# 构建生产镜像
docker build -t platform-jumper:latest --target production .

# 运行容器（带 VNC 支持）
docker run -d \
  --name platform-jumper \
  -p 5900:5900 \
  -e APP_ENV=production \
  -e ENABLE_VNC=true \
  -e VNC_PASSWORD=mysecret \
  -e SCREEN_WIDTH=960 \
  -e SCREEN_HEIGHT=640 \
  -e FPS=60 \
  --memory=512m \
  --cpus=1.0 \
  --restart=unless-stopped \
  platform-jumper:latest

# 查看运行状态
docker ps -a | grep platform-jumper
docker logs -f platform-jumper
```

### 停止与清理

```bash
# Docker Compose 停止
docker compose --profile dev down
docker compose --profile dev down -v  # 同时删除数据卷

# 纯 Docker 停止
docker stop platform-jumper
docker rm platform-jumper

# 清理镜像
docker rmi platform-jumper:latest platform-jumper:dev platform-jumper:test

# 深度清理（谨慎使用）
docker system prune -a --volumes
```

---

## 环境变量说明

### 应用核心配置

| 变量名 | 默认值 | 说明 | 可选值 |
|--------|--------|------|--------|
| `APP_ENV` | `development` | 运行环境标识 | `development` / `testing` / `production` |
| `SCREEN_WIDTH` | `960` | 游戏窗口宽度（像素） | 正整数 |
| `SCREEN_HEIGHT` | `640` | 游戏窗口高度（像素） | 正整数 |
| `FPS` | `60` | 游戏帧率 | 正整数，建议 30-120 |
| `HEADLESS` | `true` | 无头模式（无物理显示设备时必须为 true） | `true` / `false` |

### VNC 远程访问配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_VNC` | `false` | 是否启用 VNC 服务器，生产环境建议启用 |
| `ENABLE_WM` | `false` | 是否启用窗口管理器（Fluxbox） |
| `VNC_PORT` | `5900` | 容器内 VNC 监听端口 |
| `VNC_PASSWORD` | 空 | VNC 访问密码，生产环境必须设置 |
| `DISPLAY_NUM` | `99` | Xvfb 虚拟显示器编号 |

### 资源限制配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEV_MEM_LIMIT` | `512m` | 开发环境内存限制 |
| `DEV_CPU_LIMIT` | `1.0` | 开发环境 CPU 核心数限制 |
| `TEST_MEM_LIMIT` | `256m` | 测试环境内存限制 |
| `TEST_CPU_LIMIT` | `0.5` | 测试环境 CPU 核心数限制 |
| `PROD_MEM_LIMIT` | `512m` | 生产环境内存限制 |
| `PROD_CPU_LIMIT` | `1.0` | 生产环境 CPU 核心数限制 |
| `PROD_DATA_PATH` | `./data` | 生产数据卷本地绑定路径 |
| `PROD_LOG_PATH` | `./logs` | 生产日志卷本地绑定路径 |

### 网络配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `NETWORK_SUBNET` | `172.28.0.0/16` | Docker 自定义网桥子网 |
| `VNC_HOST_PORT` | `5900` | 宿主机 VNC 映射端口 |
| `PYTHON_VERSION` | `3.12-slim` | 基础 Python 镜像版本 |

### 健康检查配置（代码内）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HEALTHCHECK` | `false` | 运行模式切换为健康检查模拟 |
| `HEALTHCHECK_MAX_FRAMES` | `300` | 健康检查模拟的最大帧数（约5秒@60FPS） |

---

## 多环境部署

### 开发环境 (Development)

**特点：**
- 代码热重载支持（通过 bind mount 挂载源码）
- 启用窗口管理器方便调试
- 日志级别更高

```bash
# 配置 .env
APP_ENV=development
ENABLE_VNC=true
ENABLE_WM=true

# 启动
docker compose --profile dev up -d --build

# 实时查看日志
docker compose --profile dev logs -f game-dev
```

### 测试环境 (Testing)

**特点：**
- 自动运行健康检查模拟（300帧后退出）
- 资源限制更严格
- 适合 CI/CD 流水线集成

```bash
# 单次运行测试
docker compose --profile test run --rm game-test

# 检查退出码（0 表示通过）
echo $?

# CI/CD 示例（GitLab CI）
# .gitlab-ci.yml
# docker_test:
#   script:
#     - docker compose --profile test build
#     - docker compose --profile test run --rm game-test
```

### 生产环境 (Production)

**特点：**
- Python 字节码优化（PYTHONOPTIMIZE=2）
- 密码保护的 VNC 访问
- 数据持久化卷挂载
- 严格的健康检查与重启策略
- 资源配额控制

```bash
# 准备数据目录
mkdir -p /srv/platform-jumper/{data,logs}
chown -R 1000:1000 /srv/platform-jumper/

# 配置 .env
APP_ENV=production
ENABLE_VNC=true
ENABLE_WM=false
VNC_PASSWORD=<your-strong-password>
PROD_DATA_PATH=/srv/platform-jumper/data
PROD_LOG_PATH=/srv/platform-jumper/logs

# 启动
docker compose --profile prod up -d --build

# 滚动更新（零停机近似）
docker compose --profile prod up -d --build --no-deps game-prod

# 扩容（如需多实例）
docker compose --profile prod up -d --scale game-prod=2
```

---

## Dockerfile 架构说明

本项目采用**三阶段多阶段构建**策略，有效减小最终镜像体积并提升构建速度。

### 构建阶段 (Stage 1: builder)

```
python:3.12-slim
  ├── 安装编译工具链（gcc, SDL2-dev 等）
  ├── 构建所有 Python 依赖为 wheel 包
  └── 输出: /wheels 目录（预编译 wheel）
```

**目的：** 将编译环境与运行环境分离，避免最终镜像中包含编译器和开发头文件。

### 运行时基础 (Stage 2: runtime-base)

```
python:3.12-slim
  ├── 仅安装运行时动态链接库
  ├── 从 builder 阶段拷贝 wheel 并安装
  ├── 创建非 root 用户（appuser）
  └── 设置工作目录权限
```

**目的：** 提供所有环境共享的最小运行时层，利用 Docker 层缓存。

### 环境特化阶段

| 阶段 | 基础层 | 附加组件 | 镜像大小估算 |
|------|--------|----------|--------------|
| `development` | runtime-base | Xvfb, x11vnc, fluxbox, xterm, netcat | ~350MB |
| `testing` | runtime-base | 无（最精简） | ~250MB |
| `production` | runtime-base | Xvfb, x11vnc, fluxbox, /data 卷 | ~320MB |

### 缓存优化策略

Dockerfile 中的指令顺序经过精心设计，以最大化层缓存命中：

```
1. 基础镜像（几乎不变）     → 缓存稳定
2. apt-get 系统依赖         → 变化少，缓存久
3. 拷贝 requirements.txt    → 依赖不变时命中
4. pip install 依赖         → 依赖不变时命中
5. 创建用户/权限            → 项目配置变化时命中
6. 拷贝应用代码             → 代码变更时重建
```

---

## 服务健康检查

### 工作原理

健康检查通过设置 `HEALTHCHECK=true` 环境变量启动应用的**模拟运行模式**：
- 自动模拟玩家向右移动 + 周期性跳跃的输入
- 运行 `HEALTHCHECK_MAX_FRAMES` 帧（默认 300 帧，约 5 秒）
- 如无异常崩溃，正常退出码 0 表示健康
- 任何异常退出码非 0，标记为不健康

### Docker Compose 配置

```yaml
healthcheck:
  test: ["CMD-SHELL", "HEALTHCHECK=true python platform_jumper.py || exit 1"]
  interval: 30s        # 每 30 秒检查一次
  timeout: 15s         # 单次检查超时 15 秒
  retries: 3           # 连续 3 次失败标记不健康
  start_period: 15s    # 启动前 15 秒忽略检查结果
```

### 检查与排障

```bash
# 查看容器健康状态
docker inspect --format='{{.State.Health.Status}}' platform-jumper-dev

# 查看最近健康检查日志
docker inspect --format='{{range .State.Health.Log}}{{.End}} - Exit: {{.ExitCode}} | {{.Output}}{{"\n"}}{{end}}' platform-jumper-dev

# 手动执行健康检查
docker exec platform-jumper-dev bash -c "HEALTHCHECK=true python platform_jumper.py"
echo "Exit code: $?"

# 健康状态列表
#   starting   - 容器启动中，等待 start_period
#   healthy    - 服务正常
#   unhealthy  - 连续失败超过重试次数
```

---

## VNC 远程访问

### 连接步骤

1. **确认服务启动且健康：**
```bash
docker compose --profile dev ps
# 输出中 game-dev 状态应为 Up (healthy)
```

2. **获取连接信息：**
```bash
# 宿主机 IP
hostname -I | awk '{print $1}'    # Linux
ipconfig getifaddr en0            # macOS
# Windows: ipconfig
```

3. **使用 VNC 客户端连接：**
   - **RealVNC Viewer**（推荐，跨平台）
   - **TigerVNC**
   - **UltraVNC**（Windows）
   - **macOS 自带：** Finder → 前往 → 连接服务器 → `vnc://<host>:5900`

4. **连接地址格式：**
```
<宿主机IP>:<VNC_HOST_PORT>
示例: 192.168.1.100:5900
```

### VNC 安全建议

**生产环境必须：**
- 设置强密码 `VNC_PASSWORD`（至少 12 位，混合字符）
- 不要将 VNC 端口直接暴露到公网
- 通过 VPN 或 SSH 隧道访问

```bash
# SSH 隧道示例（本地端口转发）
ssh -L 5900:localhost:5900 -N user@remote-server
# 然后本地 VNC 客户端连接 localhost:5900
```

**通过 HTTPS 反向代理（推荐）：**
使用 Web 端 VNC（noVNC）+ Nginx 反向代理，配合 TLS 加密。

### 常见 VNC 问题

| 现象 | 可能原因 | 解决方案 |
|------|----------|----------|
| 连接被拒绝 | VNC 服务未启动 | 检查 `ENABLE_VNC=true`，查看日志 |
| 黑屏 | Xvfb 未启动 | 检查容器日志中 Xvfb 启动信息 |
| 密码错误 | 未设置或设置错误 | 修改 `.env` 并重启容器 |
| 画面卡顿 | 带宽不足或 FPS 过高 | 降低 `FPS=30`，压缩网络传输 |

---

## 资源限制与优化

### 内存优化

游戏典型内存占用：80-150MB（不含系统开销）

| 环境 | 推荐限制 | 极端最低 |
|------|----------|----------|
| 开发 | 512MB | 256MB |
| 测试 | 256MB | 128MB |
| 生产 | 512MB | 256MB |

```bash
# 监控容器资源使用
docker stats platform-jumper-dev

# 手动调整（临时）
docker update --memory=384m --cpus=0.8 platform-jumper-dev
```

### CPU 优化

```bash
# 查看 Pygame 渲染线程数（内部不可配置）
# CPU 限制建议：
# - 1核：流畅 60 FPS，满足日常使用
# - 0.5核：约 20-30 FPS，可接受（测试环境）
```

### 构建缓存加速

```bash
# 启用 BuildKit（大幅提升多阶段构建速度）
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# 构建时复用层缓存
docker compose --profile prod build --cache-from platform-jumper:latest
```

### 镜像体积优化

| 镜像 | 预估大小 | 说明 |
|------|----------|------|
| 未优化单阶段构建 | ~900MB | 包含 gcc、make、dev 头文件等 |
| testing 阶段 | ~250MB | 最精简 |
| production 阶段 | ~320MB | 带 Xvfb + VNC |

**进一步优化思路：**
- 使用 `python:3.12-alpine` 基础镜像（需解决 SDL2 编译）
- 剔除不需要的字体、地区数据
- 构建完成后 `strip` 二进制文件

---

## 网络与数据卷管理

### 自定义网络架构

```
┌─────────────────────────────────────────────────┐
│  Docker Host                                     │
│                                                  │
│  br-game (172.28.0.0/16)                         │
│  ├─ game-dev     (172.28.0.2)  :5900 → Host      │
│  ├─ game-test    (172.28.0.3)                    │
│  └─ game-prod    (172.28.0.4)  :5900 → Host      │
│                                                  │
│  iptables 规则：允许 VNC 端口映射                │
└─────────────────────────────────────────────────┘
```

**查看网络配置：**
```bash
docker network inspect platform-jumper-net
docker network ls | grep game
```

### 数据卷说明

| 卷名称 | 类型 | 挂载路径 | 用途 |
|--------|------|----------|------|
| `dev-logs` | local (匿名) | `/var/log` | 开发环境日志 |
| `prod-data` | bind mount | `/data` | 生产环境游戏存档/数据 |
| `prod-logs` | bind mount | `/var/log` | 生产环境日志持久化 |

**生产数据卷初始化：**
```bash
# 创建宿主机目录（使用 bind mount）
sudo mkdir -p /srv/platform-jumper/{data,logs}

# 匹配容器内 appuser UID/GID（Dockerfile 中 useradd -r，通常 UID=999 或 1000）
UID_IN_CONTAINER=$(docker run --rm platform-jumper:latest id -u appuser)
GID_IN_CONTAINER=$(docker run --rm platform-jumper:latest id -g appuser)
sudo chown -R ${UID_IN_CONTAINER}:${GID_IN_CONTAINER} /srv/platform-jumper/

# 备份数据卷
docker run --rm \
  -v platform-jumper-prod-data:/source \
  -v $(pwd):/backup \
  alpine tar czf /backup/prod-data-backup-$(date +%Y%m%d).tar.gz -C /source .

# 恢复数据卷
docker run --rm \
  -v platform-jumper-prod-data:/target \
  -v $(pwd):/backup \
  alpine tar xzf /backup/prod-data-backup-YYYYMMDD.tar.gz -C /target
```

---

## 常见问题排查

### 问题 1：容器启动后立即退出

**症状：**
```bash
docker compose --profile dev ps
# STATUS: Exited (1) 5 seconds ago
```

**排查步骤：**
```bash
# 1. 查看启动日志
docker compose --profile dev logs game-dev

# 2. 常见日志条目
# 错误1: "Unable to open a terminal" 
#   → 检查 HEADLESS 是否为 true

# 错误2: "No available video device"
#   → 确认 SDL_VIDEODRIVER=dummy 是否设置（HEADLESS=true 时会自动设置）
#   → 验证: docker exec game-dev bash -c "echo $SDL_VIDEODRIVER"

# 错误3: "Permission denied"
#   → 检查 /data 和 /var/log 目录权限
ls -la /srv/platform-jumper/

# 3. 交互式调试（覆盖入口点）
docker run --rm -it --entrypoint bash platform-jumper:dev
```

### 问题 2：健康检查反复失败

**症状：**
```bash
docker inspect --format='{{.State.Health.Status}}' game-dev
# unhealthy
```

**排查步骤：**
```bash
# 1. 查看健康检查详细日志
docker inspect --format='{{range .State.Health.Log}}{{"\n"}}[{{.End}}] Exit:{{.ExitCode}} {{.Output}}{{end}}' game-dev

# 2. 手动运行健康检查
docker exec -it game-dev bash
HEALTHCHECK=true python platform_jumper.py
echo "Exit: $?"

# 3. 如果是资源不足导致，提升资源限制
# 修改 .env: DEV_MEM_LIMIT=768m, DEV_CPU_LIMIT=1.5
docker compose --profile dev up -d --build
```

### 问题 3：VNC 连接后无画面

**排查：**
```bash
# 1. 确认 Xvfb 运行
docker exec game-dev bash -c "ps aux | grep Xvfb | grep -v grep"
# 应输出 Xvfb :99 -screen 0 ...

# 2. 确认 VNC 进程
docker exec game-dev bash -c "ps aux | grep x11vnc | grep -v grep"

# 3. 检查 VNC 日志
docker exec game-dev bash -c "cat /tmp/vnc.log"
docker exec game-dev bash -c "cat /tmp/xvfb.log"

# 4. 测试虚拟显示器是否存在
docker exec game-dev bash -c "DISPLAY=:99 xdpyinfo | head"
```

### 问题 4：构建时 pip install 失败 / 超时

**解决：**
```bash
# 1. 使用国内 PyPI 镜像
# 在 Dockerfile 中修改（或在 build 时临时注入）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 2. 配置 Docker 构建代理
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
docker compose --profile dev build --build-arg HTTP_PROXY=$HTTP_PROXY

# 3. 预先下载 wheel 包
pip download -r requirements.txt -d ./wheels
```

### 问题 5：端口冲突（VNC 5900 被占用）

**解决：**
```bash
# 查看占用进程
lsof -i :5900    # Linux/macOS
netstat -ano | findstr :5900   # Windows

# 修改 .env 中的 VNC_HOST_PORT
VNC_HOST_PORT=15900

# 重启服务
docker compose --profile dev up -d
```

### 问题 6：Windows 下 bind mount 代码修改不生效

**解决：**
1. Docker Desktop → Settings → Resources → File Sharing → 添加项目目录
2. 使用 WSL2 后端（推荐）
3. 检查 `docker compose` 版本 ≥ 2.0

---

## 升级与维护

### 版本升级流程

```bash
# 1. 备份当前生产数据
BACKUP_FILE="prod-backup-$(date +%Y%m%d-%H%M).tar.gz"
docker run --rm \
  -v platform-jumper-prod-data:/source \
  -v $(pwd):/backup \
  alpine tar czf /backup/${BACKUP_FILE} -C /source .
echo "Backup created: ${BACKUP_FILE}"

# 2. 拉取/构建新版本
docker compose --profile prod build --no-cache game-prod

# 3. 滚动更新（新容器启动健康后替换旧容器）
docker compose --profile prod up -d --no-deps game-prod

# 4. 验证新版本
docker compose --profile prod ps
docker inspect --format='{{.State.Health.Status}}' platform-jumper-prod
# 等待状态变为 healthy

# 5. 如出现问题，快速回滚
# 修改 Dockerfile tag 或 image 指向旧版本
# docker compose --profile prod up -d --build
```

### 定期维护任务

| 任务 | 频率 | 命令/方法 |
|------|------|-----------|
| 数据备份 | 每日（自动）或每周 | 数据卷 tar 备份（见上文） |
| 日志清理 | 每周 | `docker compose --profile prod logs --tail 0` |
| 安全更新 | 每月 | `docker compose build --pull` 重建拉取最新安全补丁 |
| 资源监控 | 持续 | `docker stats` / Prometheus + Grafana |
| 镜像清理 | 每月 | `docker image prune -a --filter "until=720h"` |

### 日志管理

```bash
# 实时查看特定服务日志
docker compose --profile prod logs -f --tail=100 game-prod

# 按时间过滤日志（Docker ≥20.10）
docker compose --profile prod logs --since 2025-01-01T00:00:00 --until 2025-01-02T00:00:00

# 日志已通过 json-file 驱动限制大小（10MB × 3 文件）
# 如需要集中式日志收集，建议部署 ELK 或 Loki
```

### 生产环境 Checklist

- [ ] 设置强 `VNC_PASSWORD`（≥12 位）
- [ ] VNC 端口不直接暴露公网（VPN/SSH 隧道/反向代理）
- [ ] `PROD_DATA_PATH` 和 `PROD_LOG_PATH` 指向可靠磁盘
- [ ] 已配置 `restart: unless-stopped`
- [ ] 健康检查返回 `healthy`
- [ ] 资源限制已设置并测试
- [ ] 定期备份脚本已部署
- [ ] `.env` 文件权限：`chmod 600 .env`
- [ ] 宿主机操作系统安全补丁已更新

---

## 附录：完整命令速查

```bash
# ===== 构建 =====
docker compose --profile dev build          # 开发镜像
docker compose --profile test build         # 测试镜像
docker compose --profile prod build         # 生产镜像

# ===== 启动 =====
docker compose --profile dev up -d          # 后台启动开发
docker compose --profile test run --rm game-test  # 单次测试
docker compose --profile prod up -d --build # 构建并启动生产

# ===== 状态 =====
docker compose --profile dev ps             # 查看服务状态
docker compose --profile dev logs -f        # 实时日志
docker stats                                # 资源使用监控

# ===== 运维 =====
docker compose --profile prod down          # 停止并移除
docker compose --profile prod down -v       # 同时清理数据卷
docker exec -it game-prod bash              # 进入容器交互

# ===== 健康 =====
HEALTHCHECK=true python platform_jumper.py  # 手动健康测试
docker inspect --format='{{.State.Health.Status}}' <容器名>
```

---

**文档版本：** 1.0.0
**最后更新：** 2026-06-13
