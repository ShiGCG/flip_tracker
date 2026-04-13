# 子弹倒卖助手（GUI）

已按“子弹名称 + 等级绑定、买入卖出分离、分层代码结构”重构。

## 分层结构

- `main.py`：启动入口
- `app\models.py`：数据模型
- `app\storage.py`：数据读写
- `app\services.py`：业务逻辑（聚合、回本价、库存校验）
- `app\ui\main_window.py`：主窗口编排与交互
- `app\ui\theme.py`：样式与主题
- `app\ui\widgets.py`：通用 UI 组件（如 Tooltip）
- `app\ui\dialogs.py`：设置/记录管理弹窗
- `app\ui\__init__.py`：UI 包导出（`run_app`）

## 功能（当前版本）

- 子弹名称与等级绑定（名称确定后，等级自动显示）
- 名称输入支持已有名称推荐（下拉+可输入）
- 买入卡片录入：名称、买入单价、买入数量
- 卖出卡片录入：名称、卖出单价、卖出数量（全局一处）
- 提供设置页面管理子弹类型（新增/修改/删除）
- 子弹类型支持标签：日抛 / 周抛 / 长期 / 赛季
- 交易卡片：每种子弹一张，重点显示
  - 卡片排序：先按标签优先级（日抛 > 周抛 > 长期 > 赛季），再按最近买入时间（新的在前）
  - 平均买入价（K/M 缩写显示，悬浮可看完整数字）
  - 回本价（按每种子弹的回本系数计算并向上取整；K/M 缩写显示，悬浮可看完整数字）
  - 库存
  - 平均卖出（K/M 缩写显示，悬浮可看完整数字）
  - 每种子弹收益（K/M 缩写显示，悬浮可看完整数字）
  - 当前库存花费（K/M 缩写显示，悬浮可看完整数字）
- 页面顶部显示总收益（K/M 缩写显示，悬浮可看完整数字）
- 页面顶部显示总库存花费（K/M 缩写显示，悬浮可看完整数字）
- 页面顶部显示总子弹数量（当前库存总和）
- 首页卡片标题与“子弹类型管理”列表按等级着色：
  - Lv.1 白色、Lv.2 绿色、Lv.3 蓝色、Lv.4 紫色、Lv.5 黄色
- 子弹类型管理可设置每种子弹的“回本系数”（默认 0.8700，四位小数）
- 菜单栏新增“记录”页面，可查看并编辑买入/卖出记录（用于修正误输入）
- 菜单栏新增“收益概览”页面，展示每种子弹收益与总收益
- 卡片内直接卖出（卖出单价 + 卖出数量）
- 全局卖出下拉仅显示当前有库存的子弹，避免误选无库存项目
- 卖出数量超过库存时，自动按当前库存卖出
- 库存为 0 的项目：**软件启动时隐藏**；若本次运行内刚卖到 0，会暂时保留到下次启动
- 自动记录交易日志：`data\trade_log.jsonl`
- 自动生成利润汇总：`data\profit_summary.json`（每种子弹利润 + 总利润）
- 主数据文件：`data\ledger.json`

## 创建 conda 环境

```bash
conda env create -f environment.yml
conda activate game-flip-tracker
```

如果创建环境失败，先执行：

```bash
conda config --set channel_priority flexible
conda clean -i -y
```

再重试上面的 `conda env create`。

## 运行

```bash
python main.py
```

## 静态网页版（无需 Python 运行）

已提供 `web_static\` 多页面版本：

- `index.html`：主页（买入/卖出 + 持仓卡片）
- `types.html`：子弹类型管理
- `records.html`：买卖记录管理
- `profit.html`：收益统计
- `shared.js`：共享逻辑（数据读写、计算、导入导出）
- `styles.css`：统一样式

使用方式：

1. 直接双击 `web_static\index.html`（或用浏览器打开）
2. 数据保存在浏览器 `localStorage`
3. 页面右上角可“导出数据 / 导入数据”做备份迁移

### GitHub Pages 说明

GitHub Pages 是纯静态托管，前端 **不能直接写仓库里的 JSON 文件**。  
所以网页上线后仍采用浏览器本地存储（`localStorage`）+ 导入导出 JSON 的方式持久化。

如果你需要“跨设备自动同步同一个 JSON 文件”，需要接一个后端或第三方数据库（例如 Firebase / Supabase / 自建 API）。

## 数据文件

- `data\ledger.json`：主数据
- `data\trade_log.jsonl`：买卖操作日志（逐行 JSON）
- `data\profit_summary.json`：利润汇总（每种子弹 + 总利润）

## 导入文件格式

`data\ammo_types_import.json` 示例：

```json
{
  "ammo_types": [
    { "name": "7.62 PS", "level": 3, "image": "default" },
    { "name": "5.56 M855A1", "level": 5, "image": "default" }
  ]
}
```

