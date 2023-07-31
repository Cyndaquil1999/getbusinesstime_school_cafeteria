from requests import get
from bs4 import BeautifulSoup
import re
import streamlit as st
import datetime

# エスケープ文字と特定のパターンを含む配列を出力しないようにする関数
def should_output(row):
    escape_pattern = re.compile(r'^[\s\xa0]+$')
    specific_pattern = re.compile(r'^[\r\n\t－]+$')
    return not (all(escape_pattern.match(item) for item in row) or specific_pattern.match(row[0]))

# 特殊文字を置換する関数
def replace_special_characters(s):
    return s.replace('\r', '').replace('\n', '').replace('\t', '').replace('\xa0', '').replace('\u3000', '').strip()

# キャンパス情報
user_input = st.radio('キャンパスを選択してください', ['松本キャンパス', '教育学部キャンパス', '工学部キャンパス', '農学部キャンパス', '繊維学部キャンパス'])

campas = ['松本キャンパス', '教育学部キャンパス', '工学部キャンパス', '農学部キャンパス', '繊維学部キャンパス']

# user_inputがcampas内にあるかチェック
if user_input in campas:
    campas = [campus for campus in campas if campus != user_input]

# 学食の夏休み営業時間についてgetしてくる
URL = 'https://www.univcoop.jp/shinshu/news_4/news_detail_220795.html'
res = get(URL)
data = BeautifulSoup(res.text, 'html.parser')

# テーブルデータの取得
tbody_element = data.find('tbody')
table_data = []
if tbody_element:
    for row in tbody_element.find_all('tr'):
        row_data = [cell.get_text() for cell in row.find_all('td')]
        table_data.append(row_data)

# 営業時間等の取得
flg = False
business_hours = []
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
current_time = now.strftime('%H:%M')
is_holiday = now.weekday() >= 5  # 土曜日(5)または日曜日(6)なら休日

for i in table_data:
    if user_input in i[0]:
        flg = True

    if flg and i[0] == '\xa0':
        row_data = [replace_special_characters(item) for item in i[1:] if item.strip() != '']
        if should_output(row_data):
            business_hours.append(row_data)

    for j in campas:
        if flg and j in i[0]:
            flg = False

# 今日の日付と時刻を取得
current_date_time = now.strftime('%Y年%m月%d日 %H:%M:%S')

# Streamlitに結果を表示
st.write(f"現在日時: {current_date_time}")

if business_hours:
    st.write(f"{user_input}の営業時間:")
    st.table(business_hours)
else:
    st.write(f"{user_input}は通常通り営業しています。")
