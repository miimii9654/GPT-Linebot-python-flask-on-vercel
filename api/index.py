from flask import Flask, request, abort 
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from api.chatgpt import ChatGPT
from api.flex_message_template import get_flex_message_content
from api.ecpay_payment_sdk import ECPayPaymentSdk
import json
import os
from datetime import datetime,timedelta
import psycopg2

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

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
useable_minutes = 15 #每次付款可使用幾分鐘

# domain root
@app.route('/')
def home():
    html = '<style> table,td {  border: 1px solid #333;} thead,tfoot {  background-color: #333;  color: #fff;}</style>'
    html = html+'<h2>aism_accounts</h2>'
    html = html+"<table style='border: 1px solid #333;'><thead style='border: 1px solid #333;'><tr><th>no</th><th>line_id</th><th>user_name</th><th>created_on</th></tr></thead><tbody style='border: 1px solid #333;'>"    
    conn = psycopg2.connect(conn_string) 
    cur = conn.cursor()
    cur.execute("select line_id,user_name,TO_CHAR(created_on, 'YYYY/MM/DD HH24:MI:SS') from aism_accounts order by created_on desc")
    i = 1
    for r in cur :
        line_id=r[0]
        user_name=r[1]
        created_on=r[2] 
        html = html+"<tr><td>"+str(i)+"</td><td>"+line_id+"</td><td>"+user_name+"</td><td>"+created_on+"</td></tr>"
        i=i+1
    html = html+"</tbody></table>"
    
    html = html+'<h2>aism_pay</h2>'
    html = html+"<table style='border: 1px solid #333;'><thead style='border: 1px solid #333;'><tr><th>no</th><th>line_id</th><th>order_id</th><th>rtnmsg</th><th>created_on</th></tr></thead><tbody style='border: 1px solid #333;'>"    
    cur.execute("select line_id,order_id,COALESCE(rtnmsg,''),TO_CHAR(created_on, 'YYYY/MM/DD HH24:MI:SS') from aism_pay order by created_on desc")
    i = 1
    for r in cur :
        line_id=r[0]
        order_id=r[1]
        rtnmsg=r[2]
        created_on=r[3] 
        html = html+"<tr><td>"+str(i)+"</td><td>"+line_id+"</td><td>"+order_id+"</td><td>"+rtnmsg+"</td><td>"+created_on+"</td></tr>"
        i=i+1
    html = html+"</tbody></table>"
    
    return 'Hello, World!<br>'+html

# return_url: 綠界 Server 端回傳 (POST) 付款成功
@app.route('/return_url', methods=['POST'])
def return_url():    
    RtnMsg = request.form['RtnMsg']
    order_id = request.form['MerchantTradeNo']
    print('3.return_url  order_id =>',order_id,',RtnMsg:',RtnMsg)
    
    # 更新交易結果
    conn = psycopg2.connect(conn_string) 
    cur = conn.cursor()
    cur.execute("update aism_pay set rtnmsg=%s , created_on= (NOW() + interval '8 hour') where order_id=%s",(RtnMsg, order_id))    
    cur.execute("commit")    
    cur.close()
    conn.close()    
    if RtnMsg == 'Succeeded' or RtnMsg == 'paid' :
        start_time = (datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.now() +timedelta(hours=8) + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
        html = '<h1>訂單編號:'+order_id+'</h1><h1>恭喜您付款成功，您可開始跟AI敏捷專家對話，使用的時間區間為一小時</h1><h2>開始時間:'+start_time+'</h2><h2>結束時間:'+end_time+'</h2>'
    else :
        html = '<h1>訂單編號:'+order_id+'</h1><h1>很抱歉您的付款沒有成功</h1><h2>錯誤訊息:'+RtnMsg+'</h2>step:return_url'
    return html

# order_result_url: 綠界 Server 端回傳 (POST) 付款失敗
@app.route('/order_result_url', methods=['POST'])
def order_result_url():
    RtnMsg = request.form['RtnMsg'] 
    print(RtnMsg)
    order_id = request.form['MerchantTradeNo']
    print('4.order_result_url   order_id =>',order_id)     
    # 更新交易結果
    conn = psycopg2.connect(conn_string) 
    cur = conn.cursor()
    cur.execute("update aism_pay set rtnmsg=%s , created_on= (NOW() + interval '8 hour') where order_id=%s",(RtnMsg, order_id))  
    cur.execute("commit")    
    cur.close()
    conn.close()
    if RtnMsg == 'Succeeded' or RtnMsg == 'paid' :
        start_time = (datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.now() +timedelta(hours=8) + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
        html = '<h1>訂單編號:'+order_id+'</h1><h1>恭喜您付款成功，您可開始跟AI敏捷專家對話，使用的時間區間為一小時</h1><h2>開始時間:'+start_time+'</h2><h2>結束時間:'+end_time+'</h2>'
    else :
        html = '<h1>訂單編號:'+order_id+'</h1><h1>很抱歉您的付款沒有成功</h1><h2>錯誤訊息:'+RtnMsg+'</h2>step:order_result_url'
    return html
    
@app.route("/ecpay", methods=['GET']) 
def ecpay():
    host_name = request.host_url
    line_id = request.args.get("line_id")
    order_id = request.args.get("order_id")
    print("2.ecpay  order_id:",order_id,",host_name:",host_name)
    #user_name = request.args.get("user_name")
    #print('MerchantTradeNo:',MerchantTradeNo )
    order_params = {
        'MerchantTradeNo': order_id, 
        'StoreID': '',
        'MerchantTradeDate': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        'PaymentType': 'aio',
        'TotalAmount': 5,
        'TradeDesc': '訂單測試',
        'ItemName': 'AI敏捷專家Line諮詢(1小時)',
        'ReturnURL': host_name+'return_url', #'https://gpt-linebot-python-flask-on-vercel-puce-two.vercel.app/', 
        'ChoosePayment': 'ALL',
        'ClientBackURL': 'https://www.ecpay.com.tw/client_back_url.php', 
        'ItemURL': 'https://www.ecpay.com.tw/item_url.php',
        'Remark': '交易備註',
        'ChooseSubPayment': '',
        'OrderResultURL': host_name+'order_result_url', #'https://udn.com/news/index', 
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
        
        # 建立交易order_id
        print('建立交易order_id:',order_id,',   line_id:', line_id)
        conn = psycopg2.connect(conn_string) 
        cur = conn.cursor()
        cur.execute("insert into aism_pay(line_id, order_id, created_on) values (%s, %s, (NOW() + interval '8 hour'))  ",(line_id, order_id))
        cur.execute("commit")    
        cur.close()
        conn.close()
        
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

def check_useable(line_id):
    conn = psycopg2.connect(conn_string) 
    cur = conn.cursor()

    # 取得user最近付款紀錄的時間
    created_on = ''    
    cur.execute("select TO_CHAR(created_on, 'YYYY/MM/DD HH24:MI:SS') from aism_pay where rtnmsg in ('Succeeded','paid') and line_id='"+line_id+"' order by created_on desc LIMIT 1")
    for r in cur :
        created_on=r[0]
    cur.close()
    conn.close() 
    
    current_time = datetime.now() + timedelta(hours=8)
    print('check_useable  current_time:',current_time.strftime("%Y/%m/%d %H:%M:%S"),',created_on:',created_on) 
    if created_on != '':        
        diff_minutes = (current_time - datetime.strptime(created_on, '%Y/%m/%d %H:%M:%S')).total_seconds() / 60
        if diff_minutes > useable_minutes :            
            useable = 2 # over useable_minutes
            print('diff_minutes:',diff_minutes,',超過useable_minutes:',useable_minutes,',useable:',useable,'==>超過使用時間，不可使用')
        else :    
            useable = 1 # in useable_minutes
            print('diff_minutes:',diff_minutes,',沒有超過useable_minutes:',useable_minutes,',useable:',useable,'==>還在使用時間內，可使用')
    else :
        useable = 3 # not pay
        print('useable:',useable,'==>沒付過款，不可使用')
    
    return useable

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.message.type != "text":
        return
    
    line_id = json.loads(str(event.source))['userId']
    user_name = line_bot_api.get_profile(line_id).display_name # 取得line名稱 
    
    # 紀錄user帳號
    conn = psycopg2.connect(conn_string) 
    cur = conn.cursor()
    cur.execute("insert into aism_accounts(line_id, user_name, created_on) values (%s, %s, (NOW() + interval '8 hour')) on conflict (line_id) do nothing",(line_id,user_name))
    cur.execute("commit")    
    cur.close()
    conn.close()
    
    print("0.handle_message    line_id:",line_id,",user_name:",user_name) 
    if event.message.type == "text":  # 只要user輸入就判斷能否使用，若否則跳出付費視窗  
        useable = check_useable(line_id)
        print('useable ==> ',useable) 
        if useable != 1 : # 不可使用，跳出付費視窗
            host_name = request.host_url
            order_id = datetime.now().strftime("NO%Y%m%d%H%M%S")     
            flex_content = get_flex_message_content(host_name, user_name, line_id, order_id) # 設定flexmessage模板
            line_bot_api.push_message(line_id, FlexSendMessage(
                alt_text='hello',
                contents=flex_content
            ))
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
