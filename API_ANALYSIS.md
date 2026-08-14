# StockHunter API 数据分析与后端工作原理推断

> 基于 `StockHunter Malaysia 3.7.1` 实测抓包 + 反编译源码的**逆向分析**。
> 目的：搞清 API 返回什么数据、服务端怎么算的、用什么数据库、数据从哪来。
> 配合 `README.md` 的接口文档与 `reverse_engineering/` 的逆向报告。

---

## 1. 实测数据快照（2026-08-14）

| 接口 (域名) | 返回状态 | 说明 |
|---|---|---|
| `klsestock.com/json_filter_v1.php` (Screener) | ✅ **真实数据** | 106 字段/股，返回 4 只 |
| `freeinfo.my/.../getcurresult_v1.php` | ⚠️ 空 `result_value:[]` | 所有日期均空 |
| `freeinfo.my/.../getklse_index_v1.php` | ⚠️ 空 | `result_value:null` |
| `freeinfo.my/.../getklse_hotstk_v1.php` | ⚠️ 空 `[]` | |
| `freeinfo.my/.../getklsediv_bycode_v1.php` | ⚠️ 空 | 蓝筹均空 |
| `freeinfo.my/.../getklsenews_bycode_v2.php` | ⚠️ 空 `No data found` | |
| `stockhunter.my/.../get_chart_adam.php` | ✅ **内联 HTML** | 含完整 K线数组 |

**核心结论**：当前**只有 `klsestock.com` 的 Screener 与 `stockhunter.my` 的图表接口在服役**；`freeinfo.my` 那组（行情/新闻/股息/指数）服务端返回空 —— 推测 `freeinfo.my` 数据源已停用或改版，App 实际可能也已切到 `klsestock.com`。**Screener 是唯一稳定可用的数据接口。**

---

## 2. Screener 返回数据字段分类（106 字段）

实测一只股票 (`AHB / 7315`) 的字段，按业务语义分类：

### 2.1 标识与行情 (Identity & Quote)
| 字段 | 示例 | 含义 |
|---|---|---|
| `stockcode` / `stk_code` | `7315` | 股票代码 (Bursa) |
| `stockname` | `AHB` | 股票名 |
| `price` / `pri_now` | `0.050` | 现价 |
| `pri_open` | `0.045` | 开盘 |
| `pri_prv_close` / `priceyest` | `0.045` | 昨收 |
| `pri_chg` / `pri_chg_pcn` | `+0.005` / `+11.11%` | 涨跌 / 涨跌% |
| `volumn` / `vol_now` | `40660700` | 成交量 |
| `turnover_amt` / `turnover_amt_avg` | `2033040` / `124041` | 成交额 / 均成交额 |
| `total_share` | `918300000` | 总股数 |
| `market_cap` | `45915000` | 市值 |
| `sikl_main_sector` | `CONSUMER PRODUCTS & SERVICES` | 主板块 |
| `scid` | `22` | 板块 ID |
| `is_w` | `0` | 是否权证 |
| `is_top_cap` | `0` | 是否大盘股 |

### 2.2 基本面 / 财务 (Fundamentals)
| 字段 | 示例 | 含义 |
|---|---|---|
| `pe` | `-8.82` | PE (负=亏损) |
| `roe` | `-14.42` | ROE % |
| `profit_margin` | `-23.38` | 利润率 % |
| `ev` | `44370335` | Enterprise Value |
| `EV_EBIT` | `-8.65` | EV/EBIT |
| `earning_yield` | `-11.56` | 盈利收益率 % |
| `dy` / `dy_status` | `0` | 股息率 / 状态 |
| `debt_cash` | `0` | 债现比 |
| `current_ratio` | `113.05` | 流动比率 |
| `pri_of_book` | `1.27` | 市净率 (P/B) |
| `net_cash` | `1` | 净现金 (0/1 标志) |
| `profit_continue_growth` / `ytoy` / `qtoq` | `0` | 连续增长 / 同比 / 环比 |
| `report_type` | `1` | 报告类型 |
| `qm` | `Mar` | 财报季度 (Quarter Month) |
| `pn17` / `is_30` | `0` | PN17 重组 / 第30条例 ( distress 标记) |

### 2.3 技术指标 (Technical)
| 字段 | 示例 | 含义 |
|---|---|---|
| `pri_ma10/20/50/60/200` | `0.0400...` | 价格 MA 各周期 |
| `ema10/20/25/50/60` | `0.0412...` | EMA 各周期 |
| `ema_golden_cross` / `sma_golden_cross` | `1` | 金叉标志 |
| `macd_line` / `macd_signal` / `macd` / `macd_above` / `macd_sid` / `macd_daycount` | `0.00353`... | MACD 全要素 |
| `rsi` | `79.87` | RSI |
| `obv` / `obv20` / `obv_sid` | `8249900`... | OBV 能量潮 |
| `pri_bb` / `pri_bb_up` / `pri_bb_down` / `pri_bb_centrifugal` / `pri_bb_daycount` | `15`... | 布林带 |
| `market_s` / `market_sid` | `3.Bear to Bull` | 市场阶段 (牛熊) |
| `mom_status` / `mom_strength` / `is_mom_plus_today` | `1` / `74.07` | Momentum 动量 |
| `volume_up` | `1` | 量增标志 |
| `pri_tp` / `pri_potential` | `-0.061` / `-410%` | 目标价 / 潜在空间 |

### 2.4 形态识别 / 信号 (Patterns & Signals)
| 字段 | 示例 | 含义 |
|---|---|---|
| `uptrend` / `topprofit` / `toprev` / `breakout` / `daycount` | `5`/`0`/`0`/`2`/`1` | 趋势/盈利/突破信号 |
| `HL` | `1` | 高低标志 |
| `candle_desc` | `Marubozu` | K线形态文字描述 |
| `candle_*` (19个) | `marubozu:100` 其余 `0` | 19种K线形态置信度 (0~100) |

> **19种形态字段**：`hammer harami kicking piercing tristar dojistar haramicross morningstar 3outside engulfing abandonbaby dragonflydoji marubozu upgapsidebyside invertedhammer takuri morningdojistar tasukigap 3linestrike 3whitesoldiers`

### 2.5 数据特征推断
- 字段**同时给字符串和数值**（`price:"0.050"` 字符串 + `priceyest:0.045` 数值）→ 服务端 PHP 混合类型输出，前端直接渲染
- 财务字段（PE/ROE/EV）带负号 → 后端**直接算**不兜底，亏损股显示负
- `candle_*` 是 0~100 的置信度而非 0/1 → 形态识别是**打分模型**不是硬匹配
- `macd_daycount:15` / `pri_bb_daycount:2` → 指标带"持续天数"状态字段 → 后端维护**状态机**（信号持续 N 日）

---

## 3. 后端工作原理推断

### 3.1 请求流（实测确认）
```
App ──AES-256-CBC(key=Kls3@p#GI3ch!qEh)──> hash 参数 ──HTTP GET──> PHP 服务端
                                                              │
                                                  解密 hash → 读筛选条件
                                                              │
                                                  查数据库 / 计算指标
                                                              │
                                                  返回 JSON (screener) 或 拼装 HTML (chart)
```
- **加密目的**：防抓包重放 + 防盗用 API（但 key 硬编码于 APK，形同公开）
- **version + serial**：`&ver=3.7.1&sn=<Build.SERIAL>` 拼在明文里 → 疑似做**版本/设备灰度**或简单鉴权（实测 `sn=own` 放行）

### 3.2 图表接口：服务端预渲染
`chart_adam.php` 返回**完整 HTML**，内含 `var sync_date=[...]`, `var pri_open=[...]`, `var pri_close_adam_a=[...]` 等内联数组（Google Charts 渲染）。
→ 证明：K线 + ADAM 指标是**服务端算好、拼进 HTML 模板**返回，不是前端 AJAX 二次拉取。
→ 架构：**PHP 服务端计算 → 模板引擎输出 HTML**（类似老式 server-side rendering）。

### 3.3 Screener：参数化查询 + 预计算指标
Screener 返回 106 字段且含**实时计算的指标**（MACD/RSI/布林/金叉/形态置信度）→ 后端不可能每次实时算全市场 1000 只股票的指标。
→ 推断：**每日收盘后批处理**，预计算所有股票的技术指标 + 财务比率，存进「预计算宽表」；Screener 只是对这张宽表做 `WHERE` 条件过滤。

### 3.4 数据来源推断
| 数据类型 | 来源推断 |
|---|---|
| 实时/历史 OHLCV | Bursa Malaysia 官方数据供应商 (如 Macquarie/自营 feed) 或 `klse.i3investor.com` 等聚合源 |
| 财务 (PE/ROE/EV/dividend) | 季报爬取 (Bursa MBRS / 公司公告) 或财经数据商 |
| 板块分类 | Bursa 官方 sector 映射 |
| 新闻/社媒 | `klse.i3investor.com` / `theedgemarkets` 等 RSS 爬取 |

---

## 4. 数据库推测

### 4.1 证据指向关系型数据库 (MySQL)
- PHP 服务端（`.php` 后缀 endpoint）+ `result_value` JSON 包装 → 典型 **PHP + MySQL** LAMP 栈
- 字段命名风格（`stk_code`, `pri_now`, `sikl_main_sector`）→ 下划线蛇形命名，符合 MySQL 习惯
- `is_success` / `result_value` / `err_msg` 统一响应壳 → 服务端有**统一 API 层**（PHP 框架或自写 wrapper）
- Screener 支持多维度 `WHERE` 过滤（价格区间/PE/板块/形态）→ 关系型 SQL 的 `SELECT ... WHERE ...` 范式

### 4.2 推测的表结构
```
stocks (主表)
  stk_code PK, stockname, sikl_main_sector, scid, is_w, total_share, ...
daily_quote (日行情)
  stk_code FK, trade_date, pri_open, pri_high, pri_low, pri_now, volumn, turnover_amt, ...
financials (财务, 季度)
  stk_code FK, qm(季度), pe, roe, profit_margin, ev, dy, debt_cash, current_ratio, pri_of_book, ...
tech_indicators (预计算技术指标, 日)
  stk_code FK, trade_date, macd_line, macd_signal, rsi, obv, pri_ma*, ema*, pri_bb*, ...
candle_patterns (形态识别, 日)
  stk_code FK, trade_date, candle_marubozu, candle_hammer, ..., candle_desc
market_state (市场阶段)
  stk_code FK, trade_date, market_sid, mom_status, mom_strength, ...
news / social (新闻社媒)
  post_id, stk_code, title, summary, source, date
```
> ⚠️ 此为**基于字段与响应壳的架构推断**，非真实 dump。StockHunter 服务端未公开 schema。

### 4.3 缓存层
- 多数 `freeinfo.my` 接口按 `req_date` 查且当前空 → 疑似**每日快照表** (`WHERE trade_date=?`)，非实时计算
- Screener 用 `klsestock.com`（独立库）→ 可能 `klsestock.com` 与 `freeinfo.my` 是**两套独立后端**，前者活跃后者退役

---

## 5. 关键工程结论

1. **活跃数据源 = `klsestock.com`**（Screener + 图表），`freeinfo.my` 已空（退役/停用）
2. **Screener = 预计算宽表 + SQL 过滤**（每天批处理算指标）
3. **图表 = 服务端预渲染 HTML**（内联数据数组，Google Charts 画）
4. **后端栈 = PHP + MySQL**（LAMP 范式，统一 JSON 响应壳）
5. **加密 = AES-256-CBC 防君子**，key 公开，仅增加抓取门槛
6. **指标丰富度极高**（MACD/RSI/布林/OBV/金叉/动量/19种K线形态/牛熊阶段）→ 后端有完整量化计算管线
7. **形态识别是打分制**（0~100 置信度），非硬规则

---

## 6. 对网页复现的启示

- **唯一稳定数据入口 = Screener**（`klsestock.com/json_filter_v1.php`）→ 网页版应以 Screener 为核心数据源
- `freeinfo.my` 那组接口（行情/新闻/股息）当前空，**网页版暂时用 Yahoo Finance 补实时行情**（README 已做）
- 若要完整还原 App，需**自建指标计算管线**（拉 Yahoo OHLCV → 算 MACD/RSI/布林/形态 → 存 MySQL → 提供 Screener API），即"用开源栈复刻 StockHunter 后端"
- 图表可复用 Google Charts / ECharts，前端内联数据（同服务端预渲染思路，但改前端渲染）

---

*分析日期：2026-08-14 · 数据来自真实 API 抓包 · 架构部分为逆向推断（标注 ⚠️ 处为推测）*
