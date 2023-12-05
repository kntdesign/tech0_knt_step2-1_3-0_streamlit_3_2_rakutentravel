#最初にipynbでpip install streamlitを行うこと

import streamlit as st
import pandas as pd
import requests
import plotly.express as px

#------------------------------------
#サイドバー部分
#------------------------------------

st.set_page_config(layout="wide")
#セレクトボックスのリストを作成
pagelist = ["page1","page2"]

#------------
#ユーザーに都道府県と対応する市区町村を選択させるモジュール
#------------

# CSVファイルを読み込む
file_path = 'rakuten_api_chikucode_ichiran.csv'
df = pd.read_csv(file_path)

# ユニークな都道府県リストを取得
prefectures = df['middleClassName'].unique()

# Streamlitドロップダウンで都道府県を選択
selected_prefecture = st.sidebar.selectbox('都道府県を選択してください。', prefectures)

# 選択された都道府県に対応する市区町村をフィルタリング
cities = df[df['middleClassName'] == selected_prefecture]['smallClassName'].unique()

# Streamlitドロップダウンで市区町村を選択
selected_city = st.sidebar.selectbox('市区町村を選択してください。', cities)

# 選択された市区町村に対応するエリアをフィルタリング（detailClassNameが存在する場合のみ）
areas = df[(df['smallClassName'] == selected_city) & df['detailClassName'].notna()]['detailClassName'].unique()

if len(areas) > 0:
    # Streamlitドロップダウンでエリアを選択
    selected_area = st.sidebar.selectbox('エリアを選択してください。', areas)
else:
    selected_area = None


#------------
#ユーザーが選択した都道府県と市区町村を楽天APIのリクエスト用のコードに変換するためのモジュール
#------------

code_selected_prefecture =  df[df['middleClassName'] == selected_prefecture]['middleClassCode'].unique()
code_selected_city =  df[df['smallClassName'] == selected_city]['smallClassCode'].unique()
code_selected_area =  df[df['detailClassName'] == selected_area]['detailClassCode'].unique()


#------------
#ユーザーが選択した都道府県・市区町村・エリアに基づき、いったん楽天施設検索APIで結果を戻すためのモジュール
#------------

#楽天施設検索APIでリクエストを行うためのモジュール

REQUEST_URL = 'https://app.rakuten.co.jp/services/api/Travel/SimpleHotelSearch/20170426'
APP_ID = '1043594254102804262'

params = {
    "format":"JSON",
    "largeClassCode":"japan",
    "middleClassCode":code_selected_prefecture,
    "smallClassCode":code_selected_city,
    "detailClassCode":code_selected_area,
    "applicationId":APP_ID
}

res = requests.get(REQUEST_URL, params)
result = res.json()

#空のpandasデータフレームを用意
df_hotels = pd.DataFrame()

#resultからpandasデータフレームに1つずつデータを格納していく処理を行う
for i in range(0,len(result['hotels'])):
    hotel_info = result['hotels'][i]['hotel'][0]['hotelBasicInfo'] #格納する配列をhotel_infoに代入する
    temp_df_hotels = pd.DataFrame(hotel_info,index=[i]) #hotel_infoに代入されたホテルのデータをデータフレームに変換します。
    df_hotels = pd.concat([df_hotels,temp_df_hotels]) #dfに結合して１つにまとめます。


#------------------------------------
#サイドバー部分（ロジック上、表示モジュールの下に表示）
#------------------------------------


#------------
#ユーザーに最低価格と最高価格を指定させるモジュール
#------------
min_hotelMinCharge = int(df_hotels['hotelMinCharge'].min())
max_hotelMinCharge = int(df_hotels['hotelMinCharge'].max())

req_min_Charge, req_max_Charge = st.sidebar.slider(
      "ホテルの価格帯を選択してください。",
      min_value = min_hotelMinCharge,
      max_value = max_hotelMinCharge,
      value = (min_hotelMinCharge, max_hotelMinCharge)
)

#------------
#ユーザーにレビュー点数の下限値を指定させるモジュール
#------------

min_reviewAverage = df_hotels['reviewAverage'].min()
max_reviewAverage = df_hotels['reviewAverage'].max()

req_min_reviewAverage = st.sidebar.slider(
      "レビュー点数の下限値を選択してください",
      min_value = min_reviewAverage,
      max_value = max_reviewAverage,
      value = (min_reviewAverage)
)


#------------
#ユーザーにレビュー数の下限値を指定させるモジュール
#------------

min_reviewCount = df_hotels['reviewCount'].min()
max_reviewCount = df_hotels['reviewCount'].max()

req_min_reviewCount = st.sidebar.slider(
      "レビュー数の下限値を選択してください",
      min_value = min_reviewCount,
      max_value = max_reviewCount,
      value = (min_reviewCount)
)

# データ型の変換（df_hotelsデータフレーム内のデータを文字列から整数形へ変換する）
df_hotels['hotelMinCharge'] = pd.to_numeric(df_hotels['hotelMinCharge'], errors='coerce')
df_hotels['reviewAverage'] = pd.to_numeric(df_hotels['reviewAverage'], errors='coerce')
df_hotels['reviewCount'] = pd.to_numeric(df_hotels['reviewCount'], errors='coerce')



#------------------------------------
#メインの表示部分
#------------------------------------


st.title('楽天トラベル検索ボード') # タイトル

st.write('サイドメニューにて指定された条件に合致する宿を探します。')
st.write('表頭をクリックすることで、ソートすることができます。なお、レビュー平均とレビュー件数はデフォルトでソートされています。')

# st.write('選択された都道府県: ', selected_prefecture)
# st.write('選択された市区町村: ', selected_city)
# if len(areas) > 0:
#     st.write('選択されたエリア: ', selected_area)

#------------
#検索結果に基づいて表の表示を行うモジュール / 評価が高くかつ評価件数が多いようにソートを行わせるモジュール
#------------

req_df_hotels = df_hotels.query('hotelMinCharge <= @req_max_Charge and hotelMinCharge >= @req_min_Charge')

#住所の列を結合する｜https://note.nkmk.me/python-pandas-str-combine/
req_df_hotels['addressUnite'] = req_df_hotels['address1'].str.cat(req_df_hotels['address2'])

#必要なものだけ列を抽出する
select_columns=['hotelName','reviewAverage','reviewCount','hotelMinCharge','postalCode','addressUnite','telephoneNo','access','parkingInformation']
matrix_df_hotels = req_df_hotels[select_columns]

#列の名前を表示用に変更する
matrix_df_hotels.columns = ['施設名','レビュー平均','レビュー件数','最低金額','郵便番号','住所','電話番号','アクセス','駐車場']
sorted_matrix_df_hotels = matrix_df_hotels.sort_values(by=['レビュー平均','レビュー件数'], ascending=[False, False])
st.dataframe(sorted_matrix_df_hotels)


#------------
#価格でのヒストグラムを表示させるモジュール
#------------

# ヒストグラムの作成
fig_histogram = px.histogram(req_df_hotels, x='hotelMinCharge', nbins=20, title='ホテルの最低料金分布')

# ヒストグラムのレイアウト設定
fig_histogram.update_layout(
    xaxis_title='最低料金',
    yaxis_title='ホテルの数',
    bargap=0.2,  # バー間の間隔
    xaxis=dict(
        tickformat=',',  # コンマ区切りのフォーマット
        tickprefix='',  # 数値の前に付けるプレフィックス（この場合は何も付けない）
        ticksuffix='円'  # 数値の後ろに付けるサフィックス
    )
)

# ヒストグラムの表示
st.plotly_chart(fig_histogram)


#------------
#Map上で表示させるモジュール
#------------

# 地図表示用にデータが正しいかどうかを確認する
# st.dataframe(req_df_hotels)
# st.write(req_df_hotels.dtypes)
# st.write(req_df_hotels.isnull().any()) #緯度経度に欠損値は存在しない模様


# fig_map = px.scatter_mapbox(req_df_hotels,
#                         lat='latitude',
#                         lon='longitude',
#                         hover_name='hotelName',
#                         zoom=10)

# fig_map.update_layout(mapbox_style="open-street-map",margin={"r":0,"t":0,"l":0,"b":0})
# st.plotly_chart(fig_map)

