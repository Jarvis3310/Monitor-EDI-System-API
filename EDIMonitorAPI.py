import json
import pymysql
import base64
import uvicorn
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

with open("sql_config.json", "r") as f:
    config = json.load(f)
    boss_config = config["boss"]

def decrypt(source):
    source = base64.b64decode(source.encode("utf8"))
    key = SHA256.new(b"ZDu9FpVGBWGUD3FNfuzMMxPcs2snrd9HFrmvUxWp5PTm28TED73yMM6nYRMwFDdY").digest()
    IV = source[:AES.block_size]
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size:])
    padding = data[-1]
    if data[-padding:] != bytes([padding]) * padding:
        return ""
    return data[:-padding].decode("utf8")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def kh_sit_flow():
    connect = pymysql.connect(
                host=boss_config["host"], 
                user=boss_config['user']+'@'+boss_config['host'].split('.mariadb')[0],
                passwd=decrypt(boss_config["password"]), 
                db=boss_config['db'], 
                charset="utf8",
                ssl={"fake_flag_to_enable_tls":True})
    with connect.cursor() as cursor:
        sql = "SELECT EDI_NO, EDI_ID, EDI_FLOW_ID, JOB_ALL_CN, DATA_DATE, STATUS_ID, RESULT_ID, IS_AUTOMATIC, DATE_FORMAT(DT_BEGIN, '%Y-%m-%d %H:%i') as DT_BEGIN, DATE_FORMAT(DT_END, '%Y-%m-%d %H:%i') as DT_END FROM CHAIEDI.EDI_FLOW"
        cursor.execute(sql)
        data = cursor.fetchall()
    connect.close()
    return data

def kh_sit_job():
    connect = pymysql.connect(
                host=boss_config["host"], 
                user=boss_config['user']+'@'+boss_config['host'].split('.mariadb')[0],
                passwd=decrypt(boss_config["password"]), 
                db=boss_config['db'], 
                charset="utf8",
                ssl={"fake_flag_to_enable_tls":True})
    with connect.cursor() as cursor:
        sql = "SELECT EDI_NO, EDI_JOB_NO, EDI_JOB_ID, EDI_JOB_TYPE, STATUS_ID, RESULT_ID, IS_AUTOMATIC, DATE_FORMAT(DT_BEGIN, '%Y-%m-%d %H:%i') as DT_BEGIN, DATE_FORMAT(DT_END, '%Y-%m-%d %H:%i') as DT_END FROM CHAIEDI.EDI_JOB"
        cursor.execute(sql)
        data = cursor.fetchall()
    connect.close()
    return data

@app.websocket("/kh-sit-flow")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    kh_sit_flow_data = kh_sit_flow()
    for row in kh_sit_flow_data:
        await websocket.send_json(row)
    await websocket.close()

@app.websocket("/kh-sit-job")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    kh_sit_job_data = kh_sit_flow()
    for row in kh_sit_job_data:
        await websocket.send_json(row)
    await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
