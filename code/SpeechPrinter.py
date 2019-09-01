from time import sleep
import speech_recognition as sr
import clauseToEmoji
from pynq.overlays.base import BaseOverlay
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from pylab import *
from pynq.lib.video import *
import requests
import base64
import json
import os
import requests
import socket
import sys
import textwrap
import math
from serial import Serial

base = BaseOverlay("base.bit")
pAudio = base.audio

def get_token():
    server = "https://openapi.baidu.com/oauth/2.0/token?"
    grant_type = "client_credentials"
    #API Key
    client_id = "nTSYqmqOUAKbZh4DfSH19Ck4"
    #Secret Key
    client_secret = "kT5aPKv7iDOn7FKvj4DFu0utwjWZpn4i" 
    #拼url
    url ="%sgrant_type=%s&client_id=%s&client_secret=%s"%(server,grant_type,client_id,client_secret)
    #获取token
    res = requests.post(url)
    token = json.loads(res.text)["access_token"]
    return token

recordTime = 5;
threshold = 200
recordName = "/home/xilinx/recording.wav"
EmojiClause = ""
recordButton = 0
recordLed = 0
printerButton = 1
printerLed = 1
resetButton = 2
resetLed = 2
underlineButton = 3
underlineLED = 3
Delay = 0.5
underline = False
size_numpr = {1: 12, 2: 6, 3: 4, 4: 3, 5: 2}
# key:text_len, value:font_size, font_num_per_row, page_x, page_y,
dic = {1: [5, 1, 120, 75, 120, 70], 2: [5, size_numpr[5], 55, 80, 40, 70], 3: [4, size_numpr[4], 29, 95, 13, 90], 4: [3, size_numpr[3], 29, 110, 12, 105],5: [2, size_numpr[2], 60, 130, 40, 120], 6: [2, size_numpr[2], 29, 130, 13, 120]}
Mode = VideoMode(640, 480, 24)
hdmi_out = base.video.hdmi_out
hdmi_out.configure(Mode, PIXEL_BGR)
hdmi_out.start()

ffmpeg_cmd = 'ffmpeg'
api_url = 'https://vop.baidu.com/server_api'
json_template = {
    'format': 'pcm',
    'rate': '16000',
    'dev_pid': '1536',
    'speech': '',
    'cuid': 'pynq-z2',
    'len': 0,
    'channel': 1,
    'token': None
}
headers = {
    'Content-Type': 'application/json'
}



def isConnected():
    try:
        html = requests.get("http://www.baidu.com",timeout=2)
    except:
        return False
    return True


def reformat_input(filename):
    return_code = os.system('{0} -y -i {1} -acodec pcm_s16le -f s16le -ac 1 -ar 16000 16k.pcm'.format(ffmpeg_cmd, filename))
    return return_code

# 字典
def get_dic():
    for i in range(7, 13):
        dic[i] = [2, size_numpr[2], 29, 105, 15, 93]
    for i in range(13, 19):
        dic[i] = [2, size_numpr[2], 29, 70, 15, 66]
    for i in range(19, 25):
        dic[i] = [2, size_numpr[2], 29, 45, 17, 38]
    for i in range(25, 37):
        dic[i] = [1, size_numpr[1], 29, 115, 15, 95]
    for i in range(37, 49):
        dic[i] = [1, size_numpr[1], 29, 100, 15, 90]

get_dic()

def draw_underlined_text(draw, pos, text, font, size, num_per_row, row_num, **options):
    twidth, theight = draw.textsize(text, font=font)
    Line = {}
    print(twidth, theight, row_num, len(text), num_per_row)
    draw.text(pos, text, font=font, **options)
    for i in range(1, row_num):
        Line[i] = [pos[0], pos[1] + i*theight/row_num +5]
        draw.line((Line[i][0], Line[i][1], Line[i][0] + twidth, Line[i][1]), **options)
    # 最后一行可能没有占满，特殊处理
    Line[row_num] =[pos[0], pos[1] + theight + 5]
    last_width = (len(text) - (row_num-1) - (row_num-1)*num_per_row) * 31 * size
    draw.line((Line[row_num][0], Line[row_num][1], pos[0]+last_width, Line[row_num][1]), **options)
    Line.clear()

def picture(text, num_per_row, size, underline = False):
    row_num = math.ceil(len(text)/num_per_row)
    im = Image.new("RGB", (size*31*num_per_row, size*40*row_num), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    font = ImageFont.truetype("combined.ttf",  size=size*30)
    text1 = textwrap.fill(text, num_per_row)  # 每num_per_row一行，换行符算text1中的一个字符
    # 加下划线
    if(underline):
        draw_underlined_text(dr, (0, 0), text1, font, size, num_per_row, row_num, fill=0)
    else:
        # 不加下下划线
        dr.text((0, 0), text1, font=font, fill="#00000000")

    im.save("/home/xilinx/un.jpg")

def twobytes_integer(n):
    if n < 0 or n > 256 * 256:
        raise ArithmeticError('out of range')
    data = [int(n % 256), int(n / 256)]
    return bytes(data)


def compress_to_byte(data):
    sum = 0
    for i in range(8):
        sum += (data[i] << 7 - i)
    return bytes([sum])

def generate_bitimg(img, x=0, y=0):
    header = b'\x1A\x21\x01'
    x = twobytes_integer(x)
    y = twobytes_integer(y)
    width = twobytes_integer(img.shape[1])
    height = twobytes_integer(img.shape[0])
    showtype = b'\x00\x11'
    data = b''
    for line in img:
        for i in range(0, img.shape[1], 8):
            data += bytes(compress_to_byte(line[i:i + 8]))
    return header + x + y + width + height + showtype + data


def page_start(x=20, y=100, width=128 + 256, height=230, rotate=0):
    header = b'\x1A\x5B\x01'
    x = twobytes_integer(x)
    y = twobytes_integer(y)
    width = twobytes_integer(width)
    height = twobytes_integer(height)
    rotate = bytes([1 if rotate else 0])
    return header + x + y + width + height + rotate


def page_end():
    return b'\x1a\x5D\x00'


def page_print():
    return b'\x1A\x4F\x00'


def reset():
    return b'\x1B\x40'


def debug(msg):
    ser.write(msg)


def cut_page():
    return b'\x1b\x69'

# 转换图片
def display_img(x, y):
    im1 = Image.new("RGB", (53 * 8, 40 * 8), color='white')
    im2 = Image.open('/home/xilinx/un.jpg')
    im3 = Image.new("RGB", (640, 480), color='blue')
    im4 = Image.open('/home/xilinx/print.png')
    im5 = Image.open('/home/xilinx/choice.png')
    im6 = Image.open('/home/xilinx/online.png')
    im7 = Image.open('/home/xilinx/offline.png')
    im1.paste(im2, (x, y))
    im3.paste(im1, (108, 80))
    im3.paste(im4, (170, 0))
    im3.paste(im5, (145, 400))
    if isConnected():
        im3.paste(im6, (0, 200))
    else:
        im3.paste(im7, (0, 200))
    im3.save('/home/xilinx/un1.jpg')



# 接受字符串
def display(t):
    # HDMI打开
    global hdmi_out
    outframe = hdmi_out.newframe()
    # 显示图片
    if t == "":
        img = np.array(Image.open('/home/xilinx/kongbai.png'))
    else:
        display_img(dic[len(t)][2], dic[len(t)][3])
        img = np.array(Image.open('/home/xilinx/un1.jpg'))
    outframe[0:img.shape[0], 0:img.shape[1], :] = img[:, :, :3]
    hdmi_out.writeframe(outframe)

display("")

while (True):
    base.leds[recordLed].off()
    base.leds[printerLed].off()
    base.leds[resetLed].off()
    base.leds[underlineLED].off()

    if (base.buttons[recordButton].read() == 1):
        pAudio.select_microphone()
        base.leds[recordLed].on()
        pAudio.record(recordTime)
        base.leds[recordLed].off()
        pAudio.save(recordName)

        if(isConnected()):
            if json_template['token'] is None:
                json_template['token'] = get_token()
            reformat_input(recordName)
            file = '16k.pcm'
            size = os.path.getsize(file)
            with open(file, 'rb') as f:
                data = base64.b64encode(f.read()).decode('ascii')
            json_to_send = dict(json_template)
            json_to_send['speech'] = data
            json_to_send['len'] = size
            req = requests.post(api_url, json.dumps(json_to_send), headers)
            clause = json.loads(req.text)['result'][0]
        else:
            r = sr.Recognizer()
            with sr.AudioFile(recordName) as source:
                audio = r.record(source)  # read the entire audio file
            try:
                clause = r.recognize_sphinx(audio, language='zh-CN')
                clause = clause.replace(' ', '')
            except sr.UnknownValueError:
                clause = "无法识别"
            except sr.RequestError as e:
                clause = "识别错误"

        EmojiClause = EmojiClause + clauseToEmoji.clauseToEmoji(clause)
        if len(EmojiClause) > 49:
            EmojiClause = EmojiClause[0:49]
        picture(EmojiClause, dic[len(EmojiClause)][1], dic[len(EmojiClause)][0], underline)
        display(EmojiClause)
    elif (base.buttons[printerButton].read()==1):
        if(EmojiClause == ""):
            pass
        else:
            base.leds[printerLed].on()
            ser = Serial('/dev/ttyUSB0', 115200)
            img_l = Image.open('/home/xilinx/un.jpg').convert('L')
            img = np.array(img_l)
            for y in range(img.shape[0]):
                for x in range(img.shape[1]):
                    if img[y, x] <= threshold:
                        img[y, x] = 1
                    else:
                        img[y, x] = 0
            while img.shape[1] % 8 != 0:
                img = np.concatenate((img, img[:, -1:]), axis=1)
            instruction = generate_bitimg(img)
            debug(page_start(dic[len(EmojiClause)][4], dic[len(EmojiClause)][5]))
            debug(instruction)
            debug(page_end())
            debug(page_print())
            debug(cut_page())
            base.leds[printerLed].off()
        
    elif (base.buttons[resetButton].read()==1):
        #reset部分
        base.leds[resetButton].on()
        EmojiClause = ""
        base.leds[resetButton].off()
        display(EmojiClause)
    elif (base.buttons[underlineButton].read()==1):
        #reset部分
        if underline:
            underline = False
        else:
            underline = True
        base.leds[underlineLED].on()
        picture(EmojiClause, dic[len(EmojiClause)][1], dic[len(EmojiClause)][0], underline)
        display(EmojiClause)
        sleep(0.3)
        base.leds[underlineLED].off()

#按一下会反应很多秒