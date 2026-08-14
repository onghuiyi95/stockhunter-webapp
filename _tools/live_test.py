import urllib.request, urllib.parse, ssl, json, base64, datetime
from pathlib import Path
from Crypto.Cipher import AES
KEY=b"Kls3@p#GI3ch!qEh"; IV=bytes(16)
def pkcs7(b): p=16-len(b)%16; return b+bytes([p])*p
def ae(s): c=AES.new(KEY,AES.MODE_CBC,IV); return base64.b64encode(c.encrypt(pkcs7(s.encode()))).decode()
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
H={"User-Agent":"Mozilla/5.0"}
TD=(datetime.date.today()+datetime.timedelta(days=1)).strftime("%Y-%m-%d")
def get_json(url, p=None, post=False):
    if post:
        body=urllib.parse.urlencode({"hash":ae(p),"os":"and"}).encode()
        req=urllib.request.Request(url, data=body, headers={**H,"Content-Type":"application/x-www-form-urlencoded"}, method="POST")
    else:
        q=("?hash="+urllib.parse.quote(ae(p),safe='')+"&os=and") if p else ""
        req=urllib.request.Request(url+q, headers=H)
    try: return urllib.request.urlopen(req, timeout=15, context=ctx).read().decode()
    except Exception as e: return "ERR:"+str(e)[:60]
def summarize(raw, n=2):
    if raw.startswith("ERR"): return raw
    try: d=json.loads(raw)
    except: return f"非JSON[{len(raw)}]: {raw[:80]}"
    if isinstance(d,list):
        if not d: return f"裸数组 [] 空 [{len(raw)}字节]"
        return f"裸数组 n={len(d)} [{len(raw)}字节] 样本: {json.dumps(d[:n], ensure_ascii=False)[:400]}"
    rv=d.get('result_value')
    if rv is None: return f"{{is_success:{d.get('is_success')}, result_value:null, err_msg:{d.get('err_msg','')}}} [{len(raw)}字节]"
    if isinstance(rv,list):
        if not rv: return f"空数组 [] [{len(raw)}字节]"
        return f"{{is_success:{d.get('is_success')}}} 数组 n={len(rv)} [{len(raw)}字节] 样本: {json.dumps(rv[:n], ensure_ascii=False)[:400]}"
    return f"字符串/对象 [{len(raw)}字节]: {str(rv)[:200]}"
F="http://www.freeinfo.my/api/klse/"; K="http://www.klsestock.com/"
R={}
R['01_news']=get_json(F+"getklsenews_bycode_v2.php","StkCode=&PostId=&Cat=&Lang=1&keywId=&req_date="+TD)
R['02_social']=get_json(F+"getklse_social_v1.php","StkCode=&PostId=&Cat=&Lang=1&req_date="+TD)
R['03_hotstock']=get_json(F+"getklse_hotstk_v1.php","day=1&Lang=1&req_date="+TD)
R['04_index_ASIA']=get_json(F+"getklse_index_v1.php","idx_type=index&region=ASIA&location=&req_date="+TD)
R['05_index_NSAM']=get_json(F+"getklse_index_v1.php","idx_type=index&region=NSAM&location=&req_date="+TD)
R['06_index_future']=get_json(F+"getklse_index_v1.php","idx_type=future&region=&location=&req_date="+TD)
R['07_screener']=get_json(K+"json_filter_v1.php","id=20&bo=&yh=&tp=&gw=&nc=&iw=&tr=&hl=&er=&type=&trend=&day=&sector=&pri_mi=&pri_mx=&pe=&pm=&ev=&dc=&cr=&ey=&roe=&dy=&pob=&evalue_ab=&m_cap_min=&m_cap_max=&t_share_min=&t_share_max=&ma1=&ma_c1=&ma2=&ma_c2=&ma3=&macd=&macd_day=&rsi_c=&rsi_v=&obv=&bb=&bb_day=&turn_ov_min=&turn_ov_max=&hammer=&harami=&haramicross=&engulfing=&piercing=&dojistar=&dragonflydoji=&marubozu=&invertedhammer=&takuri=&morningstar=&morningdojistar=&tristar=&kicking=&tasukigap=&abandonbaby=&threelinestrike=&threeoutside=&threewhitesoldiers=&ver=3.7.1&sn=own")
R['08_curresult']=get_json(F+"getcurresult_v1.php","req_date="+TD)
R['09_dividend_POST']=get_json(F+"getklsediv_bycode_v1.php","StkCode=6012&req_date="+TD, post=True)
R['10_qresult_POST']=get_json(F+"getklseprospect_bycode_v1.php","stk_code=6012&q_year=2026&PostId=&KeywId=&req_date="+TD, post=True)
cids={"11_Overview_v1":"json_cache_v1.php?id=1","12_Watchlist_v1":"json_cache_v1.php?id=2","13_Trend_v1":"json_cache_v1.php?id=6&trend=2","14_Tech_v1":"json_cache_v1.php?id=8","15_HotWeek_v1":"json_cache_v1.php?id=9","16_HotMonth_v1":"json_cache_v1.php?id=10","17_GrowthConQ_v1":"json_cache_v1.php?id=11","18_GrowthYoY_v1":"json_cache_v1.php?id=12","19_GrowthQoQ_v1":"json_cache_v1.php?id=13","20_Report_v1":"json_cache_v1.php?id=16","21_TopProfit_v1":"json_cache_v1.php?id=17","22_NetCash_v1":"json_cache_v1.php?id=18","23_DivYield_v1":"json_cache_v1.php?id=19","24_Toploss_v1":"json_cache_v1.php?id=22","25_Shariah_v1":"json_cache_v1.php?id=23","26_HotList_v2":"json_cache_v2.php?id=3","27_TopGainer_v2":"json_cache_v2.php?id=26","28_TopLoser_v2":"json_cache_v2.php?id=27","29_TopGainPct_v2":"json_cache_v2.php?id=28","30_TopLosePct_v2":"json_cache_v2.php?id=29","31_MomVolUp_v2":"json_cache_v2.php?id=30","32_MomGapUp_v2":"json_cache_v2.php?id=31","33_MomTurnOver_v2":"json_cache_v2.php?id=32","34_SectorList_v2":"json_cache_v2.php?id=33","35_SectorDetail_v2":"json_cache_v2.php?id=34","36_DivPolicy_v2":"json_cache_v2.php?id=35","37_LatestQ_v2":"json_cache_v2.php?id=37","38_Warrant38_v2":"json_cache_v2.php?id=38&code=6012&ver=3.7.1&sn=own","39_WarrantDisc_v2":"json_cache_v2.php?id=39","40_WarrantVol_v2":"json_cache_v2.php?id=40","41_WarrantTurn_v2":"json_cache_v2.php?id=41","42_TopRev_v2":"json_cache_v2.php?id=43"}
for k,api in cids.items():
    base=K+api.split("?")[0]
    qstr=api.split("?")[1] if "?" in api else "id="
    R[k]=get_json(base, qstr)
R['43_AI_ADAM']=get_json("http://klsechart.my/ai/ai_adam.php?code=6012")
R['44_tv_v6_chart']=get_json("http://www.stockhunter.my/tv_v6/chart.php?symbol=6012")
for k,url in [("45_klsegroup","http://klsegroup.com/get_json.php?id=1"),("46_sh_adam","http://www.stockhunter.my/api/klse/get_chart_adam.php?StkCode=6012&req_date="+TD),("47_sh_mom","http://www.stockhunter.my/api/klse/get_chart_mom_subsector.php?req_date="+TD),("48_happypanic","http://www.freeinfo.my/api/klse/get_chart_happypanic.php?req_date="+TD)]:
    R[k]=get_json(url)
out=[f"# StockHunter 全接口直连实测 (req_date={TD})\n"]
for k,raw in R.items(): out.append(f"\n## {k}\n{summarize(raw)}\n")
Path(r"C:\Users\Administrator\stockhunter-webapp\API_LIVE_TEST.md").write_text("\n".join(out), encoding='utf-8')
print(f"完成 {len(R)} 个接口 -> API_LIVE_TEST.md")
for k,raw in R.items(): print(f"\n## {k}\n{summarize(raw)}")
