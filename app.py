from flask import Flask, request, abort
import requests
import random
import os
import re
from urllib.parse import quote
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import jieba
import jieba.analyse
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

app = Flask(__name__)
handler = WebhookHandler("57cbca60172f1a880c7af1eca75d8889")  # Channel secret


class MyToken:
    def __init__(self, token, id):
        self.token = token
        self.id = id


# 閒閒權杖: 
# 個人群組測試權杖: 
# 個人群組測試權杖Group_ID: 
# LINE Notify Token
MyTokenTest = MyToken(
    "LINE Notify Token", "Group_ID"
)
MyTokenAnderson = MyToken(
    "LINE Notify Token", "Group_ID"
)

# 图片目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(current_dir, "ImgRepo")
BASE_URL = "https://raw.githubusercontent.com/mrsanderz/ImgRepo/main/"


def get_image_urls():
    """Fetch the list of image URLs from local directory, along with original filenames."""
    valid_extensions = (".jpg", ".png", ".jpeg", ".PNG", ".JPG", ".JPEG", "GIF", "gif")  # 允许的图像文件扩展名
    try:
        files = os.listdir(IMAGE_DIR)
        image_urls = [
            (f, BASE_URL + quote(f)) for f in files if f.endswith(valid_extensions)
        ]
        # print("Fetched image filenames and URLs:", image_urls)  # 调试输出
        return image_urls
    except Exception as e:
        print("Failed to fetch image URLs:", str(e))  # 错误处理
        return []


def send_line_notify(message, line_notify_token, image_url=None):
    headers = {
        "Authorization": f"Bearer {line_notify_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {"message": message}
    if image_url:
        payload["imageThumbnail"] = image_url
        payload["imageFullsize"] = image_url
    response = requests.post(
        "https://notify-api.line.me/api/notify", headers=headers, data=payload
    )
    print("Status Code:", response.status_code)  # 打印状态码以检查是否成功
    print("Response:", response.text)  # 打印响应文本以诊断问题
    return response.status_code


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


# List of pre-defined image URLs
"""
image_urls = [
    "https://megapx-assets.dcard.tw/images/ab174a89-69e1-44e7-a15b-ecd60add474e/full.jpeg",
    "https://megapx-assets.dcard.tw/images/3722ecd7-297e-4979-a733-dc4eaedbd326/full.jpeg",
    "https://megapx-assets.dcard.tw/images/776c3489-c910-40f4-b5a3-cb1d7bb664ff/1280.jpeg",
    "https://megapx-assets.dcard.tw/images/2d2f27fd-7d26-4e2d-8cbb-549b28a1b801/1280.jpeg",
    "https://megapx-assets.dcard.tw/images/d5274e0f-65ec-40b4-a380-7a8dd26997e2/full.jpeg",  # 美型驚訝
    "https://megapx-assets.dcard.tw/images/4af5cbc9-a6f9-4abb-a3d5-21da9081a0ee/1280.webp",  # 哆啦梳頭髮
    "https://megapx-assets.dcard.tw/images/c7e60d86-7d96-42e7-b26b-098c0c99f512/1280.webp",
]
"""

# 初始化向量化工具
# https://blog.csdn.net/blmoistawinde/article/details/80816179
# vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
vectorizer = TfidfVectorizer()  # token_pattern="\\b\\w+\\b")
file_path = "custom_dict.txt"
jieba.load_userdict(file_path)


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    if len(re.findall(r"[\u4e00-\u9fff]", event.message.text)) >= 2:
        image_data = get_image_urls()

        # 使用jieba进行中文分词，并转换为列表
        words = list(jieba.cut(event.message.text, HMM=True))
        # 清理词汇中的空白字符
        words = [word.strip() for word in words if word.strip()]
        print("text", event.message.text)
        print("words", words)

        for x, w in jieba.analyse.extract_tags(event.message.text, withWeight=True):
            print('%s %s' % (x, w))
        tags_with_weights = jieba.analyse.extract_tags(event.message.text, topK=1, withWeight=True, allowPOS=())
        if tags_with_weights:
            max_keyword, max_score = tags_with_weights[0]
            print('Keyword: %s Score: %s' % (max_keyword, max_score))

        # Find the first image that includes the user's text in its original filename
        for filename, url in image_data:
            if event.message.text in filename:  # 使用原始文件名进行比较
                print("Group ID:", event.source.group_id)
                print("Match found:", url)  # Debugging: Print the matching URL
                print("User input:", event.message.text)  # Debugging: Print user input
                if event.source.group_id == MyTokenTest.id:
                    sendToken = MyTokenTest.token
                elif event.source.group_id == MyTokenAnderson.id:
                    sendToken = MyTokenAnderson.token
                print("Token", sendToken)
                send_line_notify(":", sendToken, url)
                break
            else:  # 結巴
                if max_keyword in filename:  # 使用原始文件名进行比较
                    if event.source.group_id == MyTokenTest.id:
                        sendToken = MyTokenTest.token
                    elif event.source.group_id == MyTokenAnderson.id:
                        sendToken = MyTokenAnderson.token
                    print("Token", sendToken)
                    send_line_notify(max_keyword + ":", sendToken, url)
                    break


if __name__ == "__main__":
    app.run()
