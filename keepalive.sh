#!/bin/bash
# 品牌市场部工作台 - 隧道保活脚本
# 定时检查服务器和隧道是否存活，断了自动重连
# 由 launchd 每 60 秒调用一次

PROJECT_DIR="/Users/Admin/WorkBuddy/2026-07-29-11-09-09"
NODE_BIN="/Users/Admin/.workbuddy/binaries/node/versions/22.22.2/bin/node"
NODE_PATH_DIR="/Users/Admin/.workbuddy/binaries/node/workspace/node_modules"
PORT=3000
LOG="/tmp/workbench-keepalive.log"

# ===== 固定子域名配置 =====
# 注册 serveo.net 后，把这里的 SUBDOMAIN 改成你的子域名
# 注册链接: https://console.serveo.net/ssh/keys?add=SHA256%3ASllBtGlW4mKITdreuHVndbNOKrFyeg3LGsqnQBY%2BHq4
# 留空则使用随机URL（每次重启会变）
SUBDOMAIN=""

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

# 构建 SSH 参数
if [ -n "$SUBDOMAIN" ]; then
  SSH_R_ARG="${SUBDOMAIN}:80:127.0.0.1:${PORT}"
  TUNNEL_CHECK_URL="https://${SUBDOMAIN}.serveo.net"
else
  SSH_R_ARG="80:127.0.0.1:${PORT}"
  TUNNEL_CHECK_URL=""
fi

# 1. 检查服务器是否存活
if ! curl -s --max-time 3 http://127.0.0.1:$PORT/api/health | grep -q '"success":true'; then
  log "服务器未响应，重启中..."
  lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null
  sleep 1
  cd "$PROJECT_DIR"
  NODE_PATH="$NODE_PATH_DIR" nohup "$NODE_BIN" server.js > /tmp/workbench-server.log 2>&1 &
  sleep 2
  if curl -s --max-time 3 http://127.0.0.1:$PORT/api/health | grep -q '"success":true'; then
    log "服务器重启成功"
  else
    log "服务器重启失败！"
    exit 1
  fi
fi

# 2. 检查隧道是否存活
TUNNEL_ALIVE=0

if [ -n "$TUNNEL_CHECK_URL" ]; then
  # 固定子域名模式：直接检查固定URL
  HTTP_CODE=$(curl -skL --max-time 8 --noproxy '*' -o /dev/null -w "%{http_code}" "${TUNNEL_CHECK_URL}/api/health" 2>/dev/null)
  if [ "$HTTP_CODE" = "200" ]; then
    TUNNEL_ALIVE=1
  else
    log "固定子域名返回 HTTP $HTTP_CODE，需要重连"
  fi
else
  # 随机URL模式：从日志中提取URL
  if pgrep -f "ssh.*serveo.net" > /dev/null 2>&1; then
    TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.serveousercontent\.com' /tmp/workbench-tunnel.log 2>/dev/null | tail -1)
    if [ -n "$TUNNEL_URL" ]; then
      HTTP_CODE=$(curl -skL --max-time 8 --noproxy '*' -o /dev/null -w "%{http_code}" "${TUNNEL_URL}/api/health" 2>/dev/null)
      if [ "$HTTP_CODE" = "200" ]; then
        TUNNEL_ALIVE=1
        echo "$TUNNEL_URL" > /tmp/workbench-current-url.txt
      else
        log "隧道URL返回 HTTP $HTTP_CODE，需要重连"
      fi
    else
      log "隧道日志中未找到URL，需要重连"
    fi
  else
    log "SSH隧道进程不存在，需要重连"
  fi
fi

# 3. 如果隧道断了，重连
if [ "$TUNNEL_ALIVE" -eq 0 ]; then
  log "正在重启隧道..."
  pkill -f "ssh.*serveo.net" 2>/dev/null
  sleep 1
  > /tmp/workbench-tunnel.log
  nohup ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -R "$SSH_R_ARG" serveo.net > /tmp/workbench-tunnel.log 2>&1 &
  sleep 8

  if [ -n "$TUNNEL_CHECK_URL" ]; then
    # 固定子域名模式
    HTTP_CODE=$(curl -skL --max-time 10 --noproxy '*' -o /dev/null -w "%{http_code}" "${TUNNEL_CHECK_URL}/api/health" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
      log "隧道重连成功: $TUNNEL_CHECK_URL"
      echo "$TUNNEL_CHECK_URL" > /tmp/workbench-current-url.txt
    else
      log "隧道重连后验证失败 (HTTP $HTTP_CODE)，下次重试"
    fi
  else
    # 随机URL模式
    NEW_URL=$(grep -o 'https://[a-z0-9-]*\.serveousercontent\.com' /tmp/workbench-tunnel.log 2>/dev/null | tail -1)
    if [ -n "$NEW_URL" ]; then
      log "隧道重连成功: $NEW_URL"
      echo "$NEW_URL" > /tmp/workbench-current-url.txt
    else
      log "隧道重连失败，下次重试"
    fi
  fi
fi
