from requests import get
from bs4 import BeautifulSoup
import re
import streamlit as st
from datetime import datetime, timedelta, timezone
import pandas as pd
import jpholiday

def get_id_from_campus_name(df, campus_name):
    # キャンパス名が入力された行を抽出
    result_df = df[df['キャンパス名'] == campus_name]
    if not result_df.empty:
        return result_df.iloc[0]['id']
    else:
        return None
    
# テーブルデータから日付を取得する関数
def extract_dates(string):
    dates = []
    date_pattern = re.compile(r'(\d+/\d+)\(.+?\) ～ (\d+/\d+)\(.+?\)')

    match = date_pattern.search(string)
    if match:
        start_date, end_date = match.groups()
        dates.append('2023/'+start_date)
        dates.append('2023/'+end_date)
        
    return dates

# 短縮営業期間内の土日祝日を抽出してセットとして返す関数
def extract_holidays(holiday_info, current_year):
    holidays = set()
    date_range = holiday_info.split("・")[1].split("～")
    start_date_str, end_date_str = date_range[0].strip(), date_range[1].strip()  # 空白を削除
    start_date = datetime.strptime(f"{current_year}/{start_date_str}", "%Y/%m/%d")
    end_date = datetime.strptime(f"{current_year}/{end_date_str}", "%Y/%m/%d")

    current_date = start_date
    while current_date <= end_date:
        holidays.add(current_date)
        current_date += timedelta(days=1)

    return holidays

def get_weekend_holidays(start_date, end_date):
    holidays = set()
    current_date = start_date
    while current_date <= end_date:
        # 土日かどうかの判定
        if current_date.weekday() in [5, 6]:  # 5:土曜日, 6:日曜日
            holidays.add(current_date)
        # 祝日かどうかの判定
        if jpholiday.is_holiday(current_date):
            holidays.add(current_date)
        current_date += timedelta(days=1)
    return holidays

# タイトルを表示
st.title('2023年夏季休暇中の学内生協施設営業時間')

# csvを読み込む
cafe = pd.read_csv('./cafeteria.csv', index_col=False)
campus = pd.read_csv('./campus.csv', index_col=False)

# キャンパス情報
user_input = st.radio('キャンパスを選択してください', ['松本キャンパス', '教育学部キャンパス', '工学部キャンパス', '農学部キャンパス', '繊維学部キャンパス'])

filtered_cafe =  cafe[cafe['id'] == get_id_from_campus_name(campus, user_input)].reset_index(drop=True)

# 営業時間等の取得
business_hours = []
today = datetime.now(timezone(timedelta(hours=9))).replace(hour=0, minute=0, second=0, microsecond=0)
current_time = datetime.now()
#current_time = datetime.strptime('2023/08/01 12:00', '%Y/%m/%d %H:%M').astimezone(timezone(timedelta(hours=9)))


for i in range(len(filtered_cafe)):
    mode = 0
    row = filtered_cafe.loc[i]
    print(row['店舗'])
    #print(row['短縮営業期間'])
    time_range = extract_dates(row['短縮営業期間'])
    #print(time_range)
    
    left, right = datetime.strptime(time_range[0], '%Y/%m/%d'), datetime.strptime(time_range[1], '%Y/%m/%d')
    left = left.astimezone(timezone(timedelta(hours=9)))
    right = right.astimezone(timezone(timedelta(hours=9)))
    
    # 短縮営業期間内であるかを判定
    if left <= today and today <= right:
        #print('短縮営業期間です！')
        holidays = extract_holidays(row['左記期間内の休業'], datetime.now().year) | get_weekend_holidays(left, right)  
        #print(holidays)
        
        # 休業日であるかを判定
        if today in holidays:
            #print('今日はお休みです')
            mode = 1
        else:
            text = row['営業時間']
            time_pattern = r"\d{1,2}:\d{2}"
            times = re.findall(time_pattern, text)
            businesstime = list(map(lambda x: datetime.strptime(today.strftime('%Y/%m/%d')+ ' ' + x, '%Y/%m/%d %H:%M'), times))
            #print(businesstime)
            
            start = businesstime[0]
            end = businesstime[1]

            # 営業時間中であるかを判定
            if start <= current_time and current_time <= end:
                #print("営業しています！")
                mode = 2
            else:
                #print('営業時間外です！')
                mode = 3
        
    #st.write(row)
    if mode == 0:
        business_hours.append('通常営業中です')
        #st.write(f'{row["店舗"]}: \t通常営業中です')
    elif mode == 1:
        business_hours.append('短縮営業期間中ですが、お休みです')
        #st.write(f'{row["店舗"]}: \t短縮営業期間中ですが、お休みです')
    elif mode == 2:
        business_hours.append('営業中です')
        #st.write(f'{row["店舗"]}: \t営業中です')
    else:
        business_hours.append('営業日ですが、営業時間外です')
        #st.write(f'{row["店舗"]}: \t営業日ですが、営業時間外です')

    

# 今日の日付と時刻を取得
current_date_time = datetime.now(timezone(timedelta(hours=9))).strftime('%Y年%m月%d日 %H:%M:%S')

print(business_hours)

df = pd.DataFrame({
    '店舗': filtered_cafe['店舗'],
    '営業状況': business_hours,
    '短縮営業期間': filtered_cafe['短縮営業期間'],
    '営業期間': filtered_cafe['営業時間'],
    '左記期間内の休業': filtered_cafe['左記期間内の休業']
})


# Streamlitに結果を表示
st.write(f"現在日時: {current_date_time}")

st.table(df)
