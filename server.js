/**
 * 品牌市场部工作台 - 后端服务器
 * 提供设计需求模块的共享数据 API
 * 数据存储在 data/demands.json 中，团队成员共享同一份数据
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// 数据文件路径
const DATA_FILE = path.join(__dirname, 'data', 'demands.json');

// 确保数据目录存在
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

// ========== 数据读写工具函数 ==========

function readDemands() {
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    const data = JSON.parse(raw);
    if (Array.isArray(data) && data.length > 0) return data;
    throw new Error('Empty data file');
  } catch (e) {
    console.log('[数据] 数据文件不可用，尝试从HTML提取初始数据...');
    return extractDefaultFromHTML();
  }
}

function extractDefaultFromHTML() {
  try {
    const htmlPath = path.join(__dirname, '品牌市场部工作台.html');
    const html = fs.readFileSync(htmlPath, 'utf8');
    const match = html.match(/const DESIGN_DEMANDS_DEFAULT=\[([\s\S]*?)\];/);
    if (match) {
      const data = eval('[' + match[1] + ']');
      console.log('[数据] 从HTML提取到', data.length, '条初始数据');
      // 保存到数据文件
      try { writeDemands(data); } catch(e) { /* 云平台可能无法写入，忽略 */ }
      return data;
    }
  } catch (e) {
    console.error('[数据] 从HTML提取失败:', e.message);
  }
  return [];
}

function writeDemands(data) {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
    console.log('[数据] 已保存', data.length, '条记录');
    return true;
  } catch (e) {
    console.error('[数据] 写入失败:', e.message);
    return false;
  }
}

function nextId(demands) {
  if (demands.length === 0) return 1;
  return Math.max(...demands.map(d => d.id || 0)) + 1;
}

// ========== 静态文件服务 ==========

// 提供工作台 HTML
app.get('/', (req, res) => {
  const htmlPath = path.join(__dirname, '品牌市场部工作台.html');
  if (fs.existsSync(htmlPath)) {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
    fs.createReadStream(htmlPath).pipe(res);
  } else {
    res.status(404).send('工作台文件未找到');
  }
});

// ========== REST API: /api/demands ==========

// 获取所有设计需求
app.get('/api/demands', (req, res) => {
  const demands = readDemands();
  console.log('[API] GET /api/demands - 返回', demands.length, '条');
  res.json({
    success: true,
    count: demands.length,
    data: demands
  });
});

// 新增设计需求
app.post('/api/demands', (req, res) => {
  const demands = readDemands();
  const newItem = {
    id: nextId(demands),
    source: req.body.source || '',
    category: req.body.category || '',
    subCategory: req.body.subCategory || '',
    requester: req.body.requester || '',
    submitDate: req.body.submitDate || new Date().toISOString().slice(0, 10),
    deadline: req.body.deadline || '',
    description: req.body.description || '',
    designer: req.body.designer || '',
    status: req.body.status || '未启动',
    previewUrl: req.body.previewUrl || '',
    sourceFile: req.body.sourceFile || '',
    remark: req.body.remark || ''
  };
  demands.push(newItem);
  if (writeDemands(demands)) {
    console.log('[API] POST - 新增需求 #' + newItem.id, newItem.description?.slice(0, 30));
    res.json({ success: true, data: newItem });
  } else {
    res.status(500).json({ success: false, error: '保存失败' });
  }
});

// 更新设计需求
app.put('/api/demands/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const demands = readDemands();
  const idx = demands.findIndex(d => d.id === id);
  if (idx === -1) {
    return res.status(404).json({ success: false, error: '需求不存在' });
  }
  // 合并更新
  demands[idx] = {
    ...demands[idx],
    ...req.body,
    id: id  // ID 不可修改
  };
  if (writeDemands(demands)) {
    console.log('[API] PUT - 更新需求 #' + id, demands[idx].description?.slice(0, 30));
    res.json({ success: true, data: demands[idx] });
  } else {
    res.status(500).json({ success: false, error: '保存失败' });
  }
});

// 删除设计需求
app.delete('/api/demands/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const demands = readDemands();
  const idx = demands.findIndex(d => d.id === id);
  if (idx === -1) {
    return res.status(404).json({ success: false, error: '需求不存在' });
  }
  const deleted = demands.splice(idx, 1)[0];
  if (writeDemands(demands)) {
    console.log('[API] DELETE - 删除需求 #' + id, deleted.description?.slice(0, 30));
    res.json({ success: true, data: deleted });
  } else {
    res.status(500).json({ success: false, error: '删除失败' });
  }
});

// 批量替换（用于导入/重置）
app.put('/api/demands', (req, res) => {
  const newData = req.body.data || req.body;
  if (!Array.isArray(newData)) {
    return res.status(400).json({ success: false, error: '需要数组格式数据' });
  }
  if (writeDemands(newData)) {
    console.log('[API] PUT /api/demands - 批量替换', newData.length, '条');
    res.json({ success: true, count: newData.length });
  } else {
    res.status(500).json({ success: false, error: '批量替换失败' });
  }
});

// ========== 企微数据同步 ==========

app.post('/api/sync-from-wecom', (req, res) => {
  // 此端点接收从前端/对话中解析的企微表格数据
  const newData = req.body.data;
  if (!Array.isArray(newData)) {
    return res.status(400).json({ success: false, error: '需要数组格式数据' });
  }
  if (writeDemands(newData)) {
    console.log('[同步] 从企微导入', newData.length, '条数据');
    res.json({ success: true, count: newData.length, message: '已从企微同步 ' + newData.length + ' 条数据' });
  } else {
    res.status(500).json({ success: false, error: '同步失败' });
  }
});

// ========== 健康检查 ==========

app.get('/api/health', (req, res) => {
  const demands = readDemands();
  res.json({
    success: true,
    status: 'running',
    demandsCount: demands.length,
    serverTime: new Date().toISOString(),
    dataFile: DATA_FILE
  });
});

// ========== 启动服务器 ==========

app.listen(PORT, '0.0.0.0', () => {
  const demands = readDemands();
  console.log('');
  console.log('========================================');
  console.log('  品牌市场部工作台 - 后端服务器');
  console.log('========================================');
  console.log('  地址: http://localhost:' + PORT);
  console.log('  数据: ' + demands.length + ' 条设计需求');
  console.log('  API:  /api/demands');
  console.log('  同步: /api/sync-from-wecom');
  console.log('  健康: /api/health');
  console.log('========================================');
  console.log('');
});
