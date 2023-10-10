from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linepay import LinePayApi
from api.chatgpt import ChatGPT
from api.flex_message_template import get_flex_message_content
import json
import os
import uuid
LINE_PAY_CHANNEL_ID = os.getenv("LINE_PAY_CHANNEL_ID")
LINE_PAY_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_pay_api = LinePayApi(LINE_PAY_CHANNEL_ID, LINE_PAY_CHANNEL_SECRET, is_sandbox=True)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"
LINE_PAY_REQEST_BASE_URL = "https://{}".format('gpt-linebot-python-flask-on-vercel-puce-two.vercel.app') 
app = Flask(__name__)
chatgpt = ChatGPT()
CACHE = {} #付款用

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def pay(line_id,user_name):
    product_name = 'AI敏捷專家Line諮詢(1小時)'
    price = 99
    order_id = str(uuid.uuid4())
    amount = 1
    currency = "TWD"
    CACHE["order_id"] = order_id
    CACHE["amount"] = amount
    CACHE["currency"] = currency
    #-------------設定flex message----------------------------------   
    flex_content = get_flex_message_content(user_name, order_id) # 設定flexmessage模板
    #---------------------------------------------------------------
    request_options = {
        "amount": amount,
        "currency": currency,
        "orderId": order_id,
        "packages": [
            {
                "id": "package-999",
                "amount": amount,
                "name": "Sample package",
                "products": [
                    {
                        "id": "product-001",
                        "name": "Sample product",
                        "imageUrl": "https://www.pm-abc.com.tw/img/index/banner_pc_1.jpg",
                                    "quantity": 1,
                                    "price": price
                    }
                ]
            }
        ],
        "redirectUrls": {
            "confirmUrl": LINE_PAY_REQEST_BASE_URL + "/confirm",
            "cancelUrl": LINE_PAY_REQEST_BASE_URL + "/cancel"
        }
    }

    
    line_bot_api.push_message(line_id, FlexSendMessage(
                        alt_text='hello',
                        contents=flex_content
                    ))
    
@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.message.type != "text":
        return
    
    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return
    if event.message.text == "pay":
        print(str(event)) 
        #tmp_obj = json.loads(str(event.source))
        #line_id = str(tmp_obj['userId'])
        line_id = json.loads(str(event.source))['userId']
        user_name = line_bot_api.get_profile(line_id).display_name # 取得line名稱
        #profile
        pay(line_id,user_name)       
        return
        
    if event.message.text == "閉嘴":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return

    if working_status:
        chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))


if __name__ == "__main__":
    app.run()
