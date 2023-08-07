import sys, os
sys.path.append(os.pardir)
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import time
import schedule
from datetime import datetime
from tc_lib.common import *
from tensorflow import keras
from tensorflow.python.keras.models import load_model

def predict_data(model):
    model = model
    dimension = 48

    x_input = get_cur_data(dimension)
    x_input = x_input.reshape(1, dimension, dimension, 3)

    y_input = model.predict(x_input)

    return y_input

start_time = time.time()

access_key = ""
secret_key = ""

unit = 0.0
uuid = ""

isAsk = False

#load model
if search_model() == False:
    os.system('train_model.py')

model = load_model('my_model.h5', compile=False)

print("Start time : ", datetime.now())
print(get_mybalance(access_key, secret_key))
print("-"*30)

final_decision = False
case = 0 #0: 오를 경우, 가격 상향 조정 / 1 : 내릴 경우, 가격 하향 조정
sell_price = 0.0

#ver.1
while True:
    ans = predict_data(model)

    if isAsk: #이미 매수한 상황
        if (ans[0] == 0): #하락 예상
            uuid = sell_coin(access_key, secret_key, unit)

            print("<<Try to sell coin>>")
            print("Current time : ", datetime.now())
            isAsk = False
        else: #매수한 코인이 더 오를 것으로 예상
            print("coin will be up...")
            adjust_price(access_key, secret_key, uuid, unit, 1)

    else: #아직 매수하지 않은 상황
        if (ans[0] == 1): #다음 3분봉에서 가격이 오를 것이라고 예상
            final_decision = True

            cur_tick_time = datetime.now()
            if cur_tick_time.minute % 3 != 0: #다음 봉에서 오를 거 같은데 아직 새로운 10분봉이 나오기 전이라면, 나올 때까지 기다렸다가 시가를 시장가로 매수
                INTERVAL_MIN = 3
                tmp_time = cur_tick_time.replace(minute=cur_tick_time.minute - cur_tick_time.minute % INTERVAL_MIN + 3, second=0)                    
                del_time = tmp_time - cur_tick_time
                
                sec = del_time.seconds
                for t in tqdm(range(0, sec)):
                    time.sleep(1)
                    candle, cur_price = get_candle_cur()
                    open_price = candle.iat[0, 0]
                    if (ans[0] == 0) and (open_price > cur_price*1.01): #안 오를 거 같다는 판단 + 시가보다 현재가*1.01 보다 낮을 때(1% 손해)
                        final_decision = False
                        break
                
                if final_decision is True:
                    print(cur_tick_time)
                    print("<<buy coin>>")
                    unit, uuid, sell_price = buy_coin(access_key, secret_key)
                else:
                    print("Not buy...")

            else: #todo : 3분봉의 초반에도 제한을 둬야 할지 생각 -> 시가로 사야함.
                unit, uuid = buy_coin(access_key, secret_key)

            print("<<Try to buy coin>>")
            print("Current time : ", datetime.now())
            isAsk = True
    
    print(get_mybalance(access_key, secret_key))
    print("-"*30)

    time.sleep(60*3) #3분 단위로 검사

    stop_time = time.time() - start_time
    if stop_time >= 60*60: #60분 동안 투자
        sell_coin(access_key, secret_key, unit)
        break

print("End time : ", datetime.now())
print("End program")