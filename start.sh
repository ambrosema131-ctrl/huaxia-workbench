#!/bin/bash
# 品牌市场部工作台 - 一键启动脚本
# 使用方法: bash start.sh
#
# 服务器和隧道已由 launchd 自动管理（开机自启、断线自动重连）
# 本脚本用于手动启动或查看状态

echo "============================================"
echo "  品牌市场部工作台"
echo "============================================"

PROJECT_DIR="/Users/Admin/WorkBuddy/2026-07-29-11-09-09"
NODE_BIN="/Users/Admin/.workbuddy/binaries/node/versions/22.22.2/bin/node"
NODE_PATH_DIR="/Users/Admin/.workbuddy/binaries/node/workspace/node_modules"
PORT=3000

# 1. 检查服务器
echo "[1/3] 检查服务器..."
if curl -s --max-time 3 http://127.0.0.1:$PORT/api/health | grep -q '"success":true'; then
  COUNT=$(curl -s http://127.0.0.1:$PORT/api/health | grep -o '"demandsCount":[0-9]*' | grep -o '[0-9]*')
  echo "  ✓ 服务器运行中 (数据: $COUNT 条)"
else
  echo "  服务器未运行，启动中..."
  lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null
  cd "$PROJECT_DIR"
  NODE_PATH="$NODE_PATH_DIR" nohup "$NODE_BIN" server.js > /tmp/workbench-server.log 2>&1 &
  sleep 2
  if curl -s http://127.0.0.1:$PORT/api/health | grep -q '"success":true'; then
    echo "  ✓ 服务器启动成功"
  else
    echo "  ✗ 服务器启动失败！查看: /tmp/workbench-server.log"
    exit 1
  fi
fi

# 2. 检查隧道
echo "[2/3] 检查公网隧道..."
TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.serveousercontent\.com' /tmp/workbench-tunnel.log 2>/dev/null | tail -1)
if [ -z "$TUNNEL_URL" ]; then
  echo "  隧道未运行，启动中..."
  pkill -f "ssh.*serveo.net" 2>/dev/null
  sleep 1
  nohup ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -R 80:127.0.0.1:$PORT serveo.net > /tmp/workbench-tunnel.log 2>&1 &
  sleep 8
  TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.serveousercontent\.com' /tmp/workbench-tunnel.log 2>/dev/null | tail -1)
fi

if [ -n "$TUNNEL_URL" ]; then
  HTTP_CODE=$(curl -skL --max-time 10 --noproxy '*' -o /dev/null -w "%{http_code}" "${TUNNEL_URL}/api/health" 2>/dev/null)
  if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ 隧道正常 (HTTP 200)"
  else
    echo "  ⚠ 隧道连接异常 (HTTP $HTTP_CODE)，可能正在重连"
  fi
  echo "  ✓ 公网地址: $TUNNEL_URL"
else
  echo "  ⚠ 隧道启动中，稍后查看 /tmp/workbench-tunnel.log"
fi

# 3. 确保 launchd 守护已加载
echo "[3/3] 检查开机自启..."
launchctl list | grep "com.huaxia.workbench" 2>/dev/null | while read line; do
  echo "  ✓ $line"
done

COUNT=$(curl -s http://127.0.0.1:$PORT/api/health | grep -o '"demandsCount":[0-9]*' | grep -o '[0-9]*')
echo ""
echo "============================================"
echo "  本地访问: http://localhost:$PORT"
if [ -n "$TUNNEL_URL" ]; then
  echo "  公网访问: $TUNNEL_URL"
fi
echo "  数据量:   $COUNT 条设计需求"
echo ""
echo "  停止服务: bash stop.sh"
echo ""
echo "  ⚠ 当前URL是随机的，注册固定子域名后不变"
echo "  注册链接: https://console.serveo.net/ssh/keys?add=SHA256%3ASllBtGlW4mKITdreuHVndbNOKrFyeg3LGsqnQBY%2BHq4"
echo "============================================"
