from flask import Flask, request, abort,session
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linepay import LinePayApi
from api.chatgpt import ChatGPT
from api.flex_message_template import get_flex_message_content
from api.ecpay_payment_sdk import ECPayPaymentSdk
import json
import os
import uuid

import importlib.util
from datetime import datetime,timedelta
import psycopg2

LINE_PAY_CHANNEL_ID = os.getenv("LINE_PAY_CHANNEL_ID")
LINE_PAY_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_pay_api = LinePayApi(LINE_PAY_CHANNEL_ID, LINE_PAY_CHANNEL_SECRET, is_sandbox=True)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"
LINE_PAY_REQEST_BASE_URL = "https://{}".format('gpt-linebot-python-flask-on-vercel-puce-two.vercel.app') 
app = Flask(__name__)
app.secret_key = 'super secret string'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)

# db setting
host = "ep-solitary-glade-75192711.us-east-1.postgres.vercel-storage.com"
dbname = "verceldb"
user = "default"
password = "9l5YHtOCTyRJ"
sslmode = "require"
port = "5432"
conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)

chatgpt = ChatGPT()
CACHE = {} #付款用

# domain root
@app.route('/')
def home():
    conn = psycopg2.connect(conn_string) 
    cur = conn.cursor()
    cur.execute("select count(1) from aism_accounts")
    cur.execute("select now()")
    for r in cur :
        c=str(r[0])
    cur.close()
    conn.close()    
    return 'Hello, World! aism_accounts count: '+c

# return_url: 綠界 Server 端回傳 (POST) 
@app.route('/return_url', methods=['POST'])
def return_url():
    #print("3.receive_result  order_id:",CACHE["order_id"],',line_id:',session['line_id'],',user_name:',session['user_name'])
    result = request.form['RtnMsg']
    print(result)
    order_id = request.form['MerchantTradeNo']
    print('3.return_url  order_id =>',order_id)
    """
    result = request.form['RtnMsg']
    tid = request.form['CustomField1']
    trade_detail = sql.Transaction.query.filter_by(tid=tid).first()
    trade_detail.status = '交易成功 sever post'
    db.session.add(trade_detail)
    db.session.commit()
    """
    return '3.return_url  order_id =>'+order_id+',RtnMsg:'+RtnMsg

# order_result_url: 綠界 Server 端回傳 (POST) 失敗
@app.route('/order_result_url', methods=['POST'])
def order_result_url():
    RtnMsg = request.form['RtnMsg']
    #print("4.order_result_url  order_id:",CACHE["order_id"],',line_id:',CACHE['line_id'],',user_name:',CACHE['user_name'])
    print(RtnMsg)
    order_id = request.form['MerchantTradeNo']
    print('4.order_result_url   order_id =>',order_id)
    """
    result = request.form['RtnMsg']
    tid = request.form['CustomField1']
    trade_detail = sql.Transaction.query.filter_by(tid=tid).first()
    trade_detail.status = '交易成功 sever post'
    db.session.add(trade_detail)
    db.session.commit()
    """
    return '4.order_result_url   order_id =>'+order_id+',RtnMsg:'+RtnMsg
    
@app.route("/ecpay", methods=['GET']) 
def ecpay():
    """
    spec = importlib.util.spec_from_file_location(
        "ecpay_payment_sdk",
        "sdk/ecpay_payment_sdk.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    """
    host_name = request.host_url
    #MerchantTradeNo = request.args.get("MerchantTradeNo")
    print("2.ecpay  order_id:",CACHE["order_id"],",host_name:",host_name)
    #user_name = request.args.get("user_name")
    #print('MerchantTradeNo:',MerchantTradeNo )
    order_params = {
        #'line_id': line_id,
        #'user_name': user_name,
        'MerchantTradeNo': CACHE["order_id"], #session['order_id'], #datetime.now().strftime("NO%Y%m%d%H%M%S"),
        'StoreID': '',
        'MerchantTradeDate': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        'PaymentType': 'aio',
        'TotalAmount': 5,
        'TradeDesc': '訂單測試',
        'ItemName': 'AI敏捷專家Line諮詢(1小時)',
        'ReturnURL': host_name+'return_url', #'https://gpt-linebot-python-flask-on-vercel-puce-two.vercel.app/',  #'https://www.ecpay.com.tw/return_url.php',
        'ChoosePayment': 'ALL',
        'ClientBackURL': 'https://www.ecpay.com.tw/client_back_url.php', # 'https://tw.yahoo.com/',
        'ItemURL': 'https://www.ecpay.com.tw/item_url.php',
        'Remark': '交易備註',
        'ChooseSubPayment': '',
        'OrderResultURL': host_name+'order_result_url', #'https://udn.com/news/index', #'https://www.ecpay.com.tw/order_result_url.php',
        'NeedExtraPaidInfo': 'Y',
        'DeviceSource': '',
        'IgnorePayment': '',
        'PlatformID': '',
        'InvoiceMark': 'N',
        'CustomField1': '',
        'CustomField2': '',
        'CustomField3': '',
        'CustomField4': '',
        'EncryptType': 1,
    }
    
    extend_params_1 = {
        'ExpireDate': 7,
        'PaymentInfoURL': 'https://www.ecpay.com.tw/payment_info_url.php',
        'ClientRedirectURL': '',
    }
    
    extend_params_2 = {
        'StoreExpireDate': 15,
        'Desc_1': '',
        'Desc_2': '',
        'Desc_3': '',
        'Desc_4': '',
        'PaymentInfoURL': 'https://www.ecpay.com.tw/payment_info_url.php',
        'ClientRedirectURL': '',
    }
    
    extend_params_3 = {
        'BindingCard': 0,
        'MerchantMemberID': '',
    }
    
    extend_params_4 = {
        'Redeem': 'N',
        'UnionPay': 0,
    }
    
    inv_params = {
        # 'RelateNumber': 'Tea0001', # 特店自訂編號
        # 'CustomerID': 'TEA_0000001', # 客戶編號
        # 'CustomerIdentifier': '53348111', # 統一編號
        # 'CustomerName': '客戶名稱',
        # 'CustomerAddr': '客戶地址',
        # 'CustomerPhone': '0912345678', # 客戶手機號碼
        # 'CustomerEmail': 'abc@ecpay.com.tw',
        # 'ClearanceMark': '2', # 通關方式
        # 'TaxType': '1', # 課稅類別
        # 'CarruerType': '', # 載具類別
        # 'CarruerNum': '', # 載具編號
        # 'Donation': '1', # 捐贈註記
        # 'LoveCode': '168001', # 捐贈碼
        # 'Print': '1',
        # 'InvoiceItemName': '測試商品1|測試商品2',
        # 'InvoiceItemCount': '2|3',
        # 'InvoiceItemWord': '個|包',
        # 'InvoiceItemPrice': '35|10',
        # 'InvoiceItemTaxType': '1|1',
        # 'InvoiceRemark': '測試商品1的說明|測試商品2的說明',
        # 'DelayDay': '0', # 延遲天數
        # 'InvType': '07', # 字軌類別
    }
    
    # 建立實體
    ecpay_payment_sdk = ECPayPaymentSdk(
        #測試用
        #MerchantID='2000132',
        #HashKey='5294y06JbISpM5x9',
        #HashIV='v77hoKGq4kWxNNIS'
        #長宏
        MerchantID='3238602',
        HashKey='PgIIxM6WewzcNXQ0',
        HashIV='yYakdCvLQDF9nlIw'
    )
    
    # 合併延伸參數
    order_params.update(extend_params_1)
    order_params.update(extend_params_2)
    order_params.update(extend_params_3)
    order_params.update(extend_params_4)
    
    # 合併發票參數
    order_params.update(inv_params)
    
    try:
        # 產生綠界訂單所需參數
        final_order_params = ecpay_payment_sdk.create_order(order_params)
    
        # 產生 html 的 form 格式
        #action_url = 'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'  # 測試環境
        action_url = 'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5' # 正式環境
        html = ecpay_payment_sdk.gen_html_post_form(action_url, final_order_params)
        html = '<html><body>'+html+'</body></html>'
        #print(html)
        return html
    except Exception as error:
        print('An exception happened: ' + str(error))

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
    order_id = datetime.now().strftime("NO%Y%m%d%H%M%S") #str(uuid.uuid4())
    amount = 1
    currency = "TWD"
    CACHE["order_id"] = order_id
    session['order_id'] = order_id
    print("1.pay  order_id:",session['order_id'],',line_id:',line_id,',user_name:',user_name)
    CACHE["amount"] = amount
    CACHE["currency"] = currency
    
    #-------------設定flex message----------------------------------   
    flex_content = get_flex_message_content(line_id, user_name, order_id) # 設定flexmessage模板
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
    line_id = json.loads(str(event.source))['userId']
    user_name = line_bot_api.get_profile(line_id).display_name # 取得line名稱    
    session['line_id'] = line_id
    session['user_name'] = user_name
    conn = psycopg2.connect(conn_string) 
    cur = conn.cursor()
    #cur.execute("insert  aism_accounts")
    #insert into aism_accounts(line_id, user_name, created_on) values (%s, %s, 'Awesome') on conflict (title, body) do nothing;
    
    for r in cur :
        c=str(r[0])
    cur.close()
    conn.close()
    print("0.handle_message    line_id:",session['line_id'],",user_name:",session['user_name'])
    if event.message.text == "pay":
        #print(str(event)) 
        #tmp_obj = json.loads(str(event.source))
        #line_id = str(tmp_obj['userId'])
        #line_id = json.loads(str(event.source))['userId']
        #user_name = line_bot_api.get_profile(line_id).display_name # 取得line名稱
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
