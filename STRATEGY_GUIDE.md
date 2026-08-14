# StockHunter 策略模块 (Strategy List) 完整解密

> 来源：App 内 Strategy List 的 6 个 Google Slides 链接（goo.gl 短链 → docs.google.com/presentation）。
> 已通过 `/pub?output=txt` 抓取全部文字内容。这些策略对应 WebApp 的 Hunt 选股功能。

---

## 1. Growth（盈利增长策略）
**对应接口**：`json_cache_v1.php?id=11/12/13`（ConQ/QoQ/YoY）

选股逻辑：按公司**盈利增长**的 3 种方式筛选：
- **ConQ**（连续季度增长）：盈利逐季持续增长
- **QoQ**（环比）：季度对季度增长
- **YoY**（同比）：年对年增长

理念：好公司通过业务扩张、成本节约提升盈利 → 股价通常随之增长。

---

## 2. Sector（板块策略）
**对应接口**：`json_cache_v2.php?id=33`（板块列表）/ `id=34&sector=`（板块详情）

选股逻辑：基于 Bursa 官方板块分类选股。覆盖：
Construction（建筑）、Consumer Products（消费）、Finance（金融）、Plantation（种植）、Properties（产业）等。

例：Cons[...] 板块内选龙头/低估股。

---

## 3. Trend（趋势策略 / 星级）
**对应接口**：`json_cache_v1.php?id=6&trend=2/3/4/5`

用 **星级** 表示趋势强弱：
| 星级 | 含义 |
|---|---|
| 5 | 牛市上涨 (Bullist Up)，股价 > 20MA & 60MA |
| 4 | 上涨趋势 (Up Trend) |
| 3 | 牛休整 (Bull Rest) |
| 2 | 底部反转 (Bottom Up) |
| 1 | 下跌趋势 (Down trend) |

5 星 = 股价在 20MA 与 60MA 上方，强牛。

---

## 4. Report（季报策略）
**对应接口**：`json_cache_v1.php?id=16&type=1/2/3`（季报月份分组）

逻辑：按**财报月**分组选股（1月~12月）。财报月分 3 类：
- Jan / Apr / Jul / Oct（1/4/7/10季报）
- Feb / May / Aug / Nov（2/5/8/11季报）
- Mar / Jun / Sep / Dec（3/6/9/12季报）

理念："聪明钱"常在季报公布前提前布局好股。

---

## 5. Hot（热门策略）
**对应接口**：`getklse_hotstk_v1.php`（DAY/WEEK/MONTH）/ `json_cache_v1?id=3/9/10`

逻辑：高成交量 = 大量资金进出。可能是机会也可能是风险。
- 买卖交易形成价量波动
- 内幕交易可能预示方向

---

## 6. Top（榜首策略）
**对应接口**：`json_cache_v1.php?id=17`（Top Profit）/ `id=18`（Net Cash）/ `id=22`（Top Loss）/ `id=43`（Top Revenue）

逻辑：按榜首类型筛选：
- **TopProfit**：最新季报利润创新高
- **Top Dividend**：最高股息
- **Top Net Cash**：净现金最高（最安全）
- **Top Loss**：亏损榜（做空/避坑参考）

---

## 策略 ↔ 接口 ↔ WebApp 映射

| 策略 | json_cache id | WebApp 标签 |
|---|---|---|
| Growth | 11/12/13 | Hunt → Growth |
| Sector | 33/34 | Hunt → Sector |
| Trend | 6&trend=2-5 | Hunt → Trend |
| Report | 16&type=1-3 | Hunt → Report |
| Hot | 3/9/10 + hotstk | Hot Stock |
| Top | 17/18/22/43 | Hunt → Top |

> 注：App 的 Hunt 筛选 SA/FA/TA/CA 是**自定义条件筛**（json_filter_v1.php），而上述 6 策略是**预设榜单**（json_cache）。两者互补。

---

*抓取日期：2026-08-14 · 来源：StockHunter Google Play 描述中的 6 个 goo.gl 短链 → Google Slides*
