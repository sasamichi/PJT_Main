# -*- coding: utf-8 -*-
import pandas as pd

df_bm = pd.read_csv('docs/精度基準マスタ.csv', dtype=str, keep_default_na=False)
df_mn = pd.read_csv('data/master/municipalities.csv', dtype=str, keep_default_na=False)
df_wz = pd.read_csv('data/master/weather_zones.csv', dtype=str, keep_default_na=False)
df_op = pd.read_csv('data/master/operators.csv', dtype=str, keep_default_na=False)
df_rt = pd.read_csv('data/master/transport_routes.csv', dtype=str, keep_default_na=False)
df_nd = pd.read_csv('data/master/nodes.csv', dtype=str, keep_default_na=False)

print('========================================================================')
print('日本 (JP) 全21ベンチマーク項目 完全自動突合監査レポート')
print('========================================================================')

pass_count = 0
total_count = 0

for _, r in df_bm[df_bm['country_code']=='JP'].iterrows():
    item = r['分野_種別']
    rule = r['判定ルール']
    target_s = r['公的基準件数']
    min_s = r['許容誤差_最小']
    max_s = r['許容誤差_最大']
    actual = None

    if item == '都道府県':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別'].isin(['都','道','府','県']))])
    elif item == '政令指定都市':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別']=='政令指定都市')])
    elif item == '政令指定都市_行政区':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別']=='行政区')])
    elif item == '中核市':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別']=='中核市')])
    elif item == '施行時特例市':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別']=='施行時特例市')])
    elif item == '一般市':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別'].isin(['一般市','市']))])
    elif item == '市':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別'].isin(['中核市','施行時特例市','一般市','市']))])
    elif item == '特別区':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別']=='特別区')])
    elif item == '町':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別']=='町')])
    elif item == '村':
        actual = len(df_mn[(df_mn['country_code']=='JP') & (df_mn['種別']=='村')])
    elif item == '気象予報区_一次細分区域':
        actual = len(df_wz[(df_wz['country_code']=='JP') & (df_wz['予報区種別']=='一次細分区域')])
    elif item == '気象庁アメダス観測所':
        actual = len(df_nd[(df_nd['country_code']=='JP') & (df_nd['種別']=='気象観測点')])
    elif item == '一般国道':
        actual = len(df_rt[(df_rt['country_code']=='JP') & (df_rt['種別']=='一般国道')])
    elif item == '主要地方道':
        actual = len(df_rt[(df_rt['country_code']=='JP') & (df_rt['種別']=='主要地方道')])
    elif item == '高速道路・都市高速':
        actual = len(df_rt[(df_rt['country_code']=='JP') & (df_rt['種別'].isin(['高速道路', '地域高規格道路・有料道路']))])
    elif item == '道の駅':
        actual = len(df_nd[(df_nd['country_code']=='JP') & (df_nd['種別']=='道の駅')])
    elif item == '旅客空港':
        actual = len(df_nd[(df_nd['country_code']=='JP') & (df_nd['種別']=='空港')])
    elif item == '主要港湾':
        actual = len(df_nd[(df_nd['country_code']=='JP') & (df_nd['種別'].isin(['主要港湾', '港湾', '港']))])
    elif item == '鉄軌道事業者':
        actual = len(df_op[(df_op['country_code']=='JP') & (~df_op['種別'].str.contains('道路|高速|航空|海運'))])
    elif item == '鉄軌道路線':
        rail_types = ['新幹線', '地下鉄', 'モノレール', '路面電車', '索道・鋼索', '新交通システム', '貨物鉄道', '鉄道']
        actual = len(df_rt[(df_rt['country_code']=='JP') & (df_rt['種別'].isin(rail_types))])
    elif item == '現行鉄道駅':
        actual = len(df_nd[(df_nd['country_code']=='JP') & (df_nd['種別'].isin(['駅', '電停', '地下鉄駅']))])

    if actual is not None:
        total_count += 1
        is_pass = False
        if rule == '完全一致':
            is_pass = (actual == int(target_s))
            range_info = f"基準: {target_s} (完全一致)"
        else:
            is_pass = (int(min_s) <= actual <= int(max_s))
            range_info = f"基準: {target_s} ({min_s}〜{max_s})"

        status_mark = "合格" if is_pass else "不合格"
        if is_pass:
            pass_count += 1
        print(f"[{status_mark}] {item:<16} | 実績: {actual:>5} 件 | {range_info}")

print('------------------------------------------------------------------------')
print(f"監査判定結果: {pass_count} / {total_count} 項目 合格 (達成率: {pass_count/total_count*100:.1f}%)")
print('========================================================================')
