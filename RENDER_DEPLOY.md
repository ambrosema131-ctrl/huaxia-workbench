# 品牌市场部工作台 - Render.com 部署指南

## 方式一：GitHub 部署（推荐）

1. 把本项目推送到 GitHub 仓库
2. 注册 Render 账号（https://render.com，可用 GitHub 登录）
3. 点击 New → Web Service
4. 连接 GitHub 仓库
5. Render 会自动识别 render.yaml 配置
6. 点击 Create Web Service
7. 等待部署完成（约2-3分钟）
8. 获得 URL：https://huaxia-workbench.onrender.com

## 方式二：CLI 部署

```bash
# 安装 Render CLI
npm install -g @render/cli

# 登录
render login

# 部署
render deploy
```

## 注意事项

- 免费版：15分钟不活动会休眠，访问即唤醒（约30秒）
- 数据持久性：免费版文件系统是临时的，服务器重启后数据重置为初始67条
- 如需数据持久化：后续可对接 Render PostgreSQL（免费90天）或 Supabase（永久免费）
