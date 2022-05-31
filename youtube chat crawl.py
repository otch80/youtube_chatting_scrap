from collections import Counter
from enum import Flag
import subprocess
import sys
import json
import re
import os
import platform
import datetime

try:
    import pytchat
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytchat"])
    import pytchat

try:
    from konlpy.tag import Okt
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "konlpy"])
    from konlpy.tag import Okt
try:
    import matplotlib.pyplot as plt
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt
try:
    import pandas as pd
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"]) 
    import pandas as pd


if platform.system() == 'Darwin': #맥
    plt.rc('font', family='AppleGothic') 
elif platform.system() == 'Windows': #윈도우
        plt.rc('font', family='Malgun Gothic') 
elif platform.system() == 'Linux': # 구글 코랩
        plt.rc('font', family='Malgun Gothic') 
plt.rcParams['axes.unicode_minus'] = False #한글 폰트 사용시 마이너스 폰트 깨짐 해결

###################### URL ######################
video_id = input('Youtube URL을 입력해주세요 : ')
#################################################
    
    
today = datetime.datetime.now().strftime("%Y_%m_%d")
filename = f'{today}_채팅데이터.csv'

df = None
flag = True

if os.path.isfile(filename):
    print(filename,"파일이 이미 존재 합니다")
    answer = input("새로 생성하시겠습니까? [Y|N] : ")
    
    answer = answer.upper()
    
    if (answer == "Y"):
        flag = True
        
    elif (answer == "N"):
        df = pd.read_csv(filename, parse_dates=['timestamp'],infer_datetime_format=True)
        print(filename,"파일 로드 완료")
        flag = False
    else:        
        print("Y|N 값 중에서 입력하십시요")
        sys.exit(0)

if (flag):
    '''
        1. 라이브 방송 실시간 채팅 로그 수집
    ''' 

    chat = pytchat.create(video_id)
    total = []
    cnt = 0

    while chat.is_alive():

        temp = chat.get().json()
        temp_dict = json.loads(temp)

        for i in temp_dict:
            timestamp = i['datetime']
            username = i['author']['name']
            message = i['message']
            total.append([timestamp, username, message])
        cnt += 1
        print(f"{timestamp} - 수집한 채팅수 : {len(total)}개")

    # 채팅 로그 저장
    df = pd.DataFrame(total,columns = ['timestamp','username','message'])
    df['timestamp'] = pd.to_datetime(df.timestamp)
    df.dropna(axis=0,inplace=True)
    df.to_csv(filename,index=False,encoding='utf-8-sig')

'''
    2. 한글 추출
'''
try:
    df['message'] = df.message.astype('str')
except:
    pass
print(">>> 한글 추출 시작")
hangul = re.compile('[가-힣]+').findall("".join(df.message.to_list()))
print(">>> 한글 추출 완료")


top_k = int(input('>>> 추출할 상위 빈도수 개수 (20개 권장, 숫자만 입력) : '))
print(f">>> 빈도수 상위 {top_k}개 키워드 추출 시작")

print(">>> 단어 추출 시작")
nlpy = Okt()
nouns = nlpy.nouns(' '.join(hangul))
print(">>> 단어 추출 완료")
print(">>> 빈도수 체크 시작")
cnt = Counter(nouns)
print(">>> 빈도수 체크 완료")
target = pd.DataFrame(cnt.most_common(top_k),columns=['keyword','freq']).sort_values(by='freq',ascending=False)
freq_df = pd.DataFrame.from_dict(cnt.items())
freq_df.columns=['keyword','freq']
freq_df = freq_df.sort_values(by='freq',ascending=False).to_csv(f"{filename.split('_채팅데이터.csv')[0]}_단어별 빈도수.csv",index=False, encoding='utf-8-sig')
print(">>> 빈도수 파일 저장 완료")

print(">>> 빈도수 그래프 생성 시작")
plt.figure(figsize=(8,12))
plt.barh(range(target.shape[0]),target['freq'])
plt.yticks(range(len(target)),target.keyword,fontsize=13)
plt.xlabel("빈도수")
plt.ylabel("단어")
plt.tight_layout()
plt.savefig(f"단어별 빈도수 top {top_k}.png",dpi=300)
print(">>> 빈도수 그래프 생성 완료")

# n분 단위 채팅수
n = int(input('>>> 채팅수 측정 단위 (1분 권장, 숫자만 입력)) : '))

plt.figure(figsize=(20,8))

print(f">>> {n}분 단위 채팅수 측정 시작")
df.set_index('timestamp').message.resample(f'{n}T').count().plot.bar(title="시간대별 채팅수")
print(f">>> {n}분 단위 채팅수 측정 완료")

plt.tight_layout()
plt.savefig(f"{n}분 단위 채팅수.png",dpi=300)
print(f">>> {n}분 단위 채팅수 그래프 생성 완료")
print(">>> 종료")
