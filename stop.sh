#!/bin/bash
# 品牌市场部工作台 - 停止脚本
echo "停止品牌市场部工作台..."

# 卸载 launchd 守护
launchctl unload ~/Library/LaunchAgents/com.huaxia.workbench-server.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.huaxia.workbench-tunnel.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.huaxia.workbench-keepalive.plist 2>/dev/null

# 杀掉残留进程
lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null
pkill -f "ssh.*serveo" 2>/dev/null

echo "已停止"
echo ""
echo "重新启动: bash start.sh"
