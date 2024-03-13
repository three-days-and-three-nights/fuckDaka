# 读取user.json文件
import json
import requests
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from wxpusher import WxPusher
from datetime import datetime
from daka_decrypt import AESCipher

# 创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# 创建handler
fh = logging.FileHandler('daka.log', mode='a')
fh.setLevel(logging.INFO)
# 创建formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 添加formatter
fh.setFormatter(formatter)
# 添加handler
logger.addHandler(fh)

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; 22041211AC Build/TP1A.220624.014; wv) AppleWebKit/537.36 (KHTML, '
                  'like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160065 MMWEBSDK/20231202 '
                  'MMWEBID/5667 MicroMessenger/8.0.47.2560(0x28002F3F) WeChat/arm64 Weixin NetType/WIFI '
                  'Language/zh_CN ABI/arm64 miniProgram/wxa1683f1bada79909',
    'Referer': 'https://kq.henetc.edu.cn/catch/static/m/index-202311201637.html',
    'x-requested-with': 'com.tencent.mm'
}


def sendMsg(msg):
    app_token = "AT_Pr2fWXZaL05VOvQuVLkwZO1LfOC9hTXR"
    result = WxPusher.send_message(content=msg, uids=["UID_LDm68NFjN1gO72sXOzBGouIj4rv7"], token=app_token)
    if result["success"]:
        logger.info("send message success")
    else:
        logger.error("send message failed")


def readUser():
    try:
        with open('user.json', 'r') as f:
            user = json.load(f)
            return user
    except FileNotFoundError as e:
        logger.error(f"user.json not found-{e}")
        sendMsg(f"user.json not found-{e}")
        exit(1)


def loginUser():
    user = readUser()
    url = "https://kq.henetc.edu.cn/ucenter/core/user/hnjmloginCatchAjax"
    payload = {
        "username": user["username"],
        "password": user["password"],
        "aid": "catch",
        "pid": "yyzx",
        "token": ""
    }

    try:
        data = requests.request("POST", url, headers=headers, data=payload).json()
        if data["status"] != 0:
            # 抛出异常
            raise Exception(data["errmsg"])
        logger.info(f"login success, username:{data['data']['userinfo']['username']}, token:{data['data']['token']}")
        return data['data']['token'], user["username"]
    except Exception as e:
        logger.error(f"login failed-{e}")
        sendMsg(f"login failed-{e}")
        exit(1)


def saveCourse():
    token, username = loginUser()
    url = "https://kq.henetc.edu.cn//catch/core/syllabus/oneDayListAjax"
    data = {
        "aid": "",
        "pid": "",
        "token": token,
    }
    aes_cipher = AESCipher("/catch/core/syllabus/oneDayListAjax")
    encrypt, random = aes_cipher.encrypt(data)
    headers["random"] = random
    try:
        data = requests.request("POST", url, headers=headers, data={
            "encrypt": encrypt
        }).json()
        if data["status"] != 0:
            # 抛出异常
            raise Exception(data["errmsg"])
        with open('course.json', 'w') as f:
            json.dump(data["data"]["data"], f)
        logger.info(f"save course success, today total {data['data']['statistics']['total']} courses")
        return data["data"]["data"]
    except Exception as e:
        logger.error(f"save course failed-{e}")
        sendMsg(f"save course failed-{e}")
        exit(1)


def fakeDaka():
    # 读取课程表
    try:
        with open('course.json', 'r') as f:
            courses = json.load(f)
    except FileNotFoundError as e:
        logger.error(f"course.json not found-{e}")
        sendMsg(f"course.json not found-{e}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"course.json format error-{e}")
        sendMsg(f"course.json format error-{e}")
        exit(1)

    for course in courses:
        # 获取当前course
        # 判断当前时间是否在打卡时间内
        if course["signinbegin"] < datetime.now().strftime('%H:%M:%S') < course["signinend"]:
            logger.info(
                f"now is in daka time, current course is {course['title']}, room is {course.get('roomnum', 'dormnum')}")
            # 开始打卡
            with open('bluetooth_data.json', 'r') as f:
                bluetooth_data = json.load(f)["iBeaconstr"]
            token, username = loginUser()
            iBeaconstr = bluetooth_data.get(("classroom", "dormitory", "training_room")[course["type"] - 1])
            data = {
                "pid": "yyzx",
                "aid": "catch",
                "iBeaconstr": iBeaconstr,
                "position": "",
                "token": token,
                "idnum": username
            }
            url = "https://kq.henetc.edu.cn/catch/core/syllabus/freeSignAjax"
            aes_cipher = AESCipher("/catch/core/syllabus/freeSignAjax")
            encrypt, random = aes_cipher.encrypt(data)
            headers["random"] = random
            try:
                data = requests.request("POST", url, headers=headers, data={
                    "encrypt": encrypt
                }).json()
                if data["status"] != 0:
                    # 抛出异常
                    raise Exception("fake daka failed, please check !")
                logger.info(f"fake daka success, daka id {data['data']}")
            except Exception as e:
                logger.error(f"fake daka failed-{e}")
                sendMsg(f"fake daka failed-{e}")
            break
    # fake 打卡流程结束
    logger.info(f"fake daka finished")


scheduler = BlockingScheduler()
# 工作日每天早上7点50执行
scheduler.add_job(saveCourse, 'cron', hour=7, minute=40)
# 第一节打卡
scheduler.add_job(fakeDaka, 'cron', hour=7, minute=55)
# 第二节打卡
scheduler.add_job(fakeDaka, 'cron', hour=9, minute=55)
# 第三节打卡
scheduler.add_job(fakeDaka, 'cron', hour=14, minute=25)
# 第四节打卡
scheduler.add_job(fakeDaka, 'cron', hour=16, minute=25)
# 第五节打卡
scheduler.add_job(fakeDaka, 'cron', hour=18, minute=45)
# 归寝打卡
scheduler.add_job(fakeDaka, 'cron', hour=22, minute=10)
scheduler.start()

