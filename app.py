from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

import google.generativeai as genai

# ตั้งค่า Gemini API
genai.configure(api_key="YOUR_GEMINI_API_KEY")  # แทนที่ด้วย API Key จริง

# LINE credentials
CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'

app = Flask(__name__)

# LINE Configuration
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
line_bot_api = MessagingApi(ApiClient(configuration))  # ✅ เพิ่มตรงนี้

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ฟังก์ชัน Gemini
def ask_gemini(prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

# ตอบข้อความ
@handler.add(MessageEvent, message=TextMessageContent)  #    ใช้ TextMessageContent
def handle_message(event):
    user_text = event.message.text

    if user_text.startswith("/gemini "):
        prompt = user_text.replace("/gemini ", "")
        try:
            answer = ask_gemini(prompt)
        except Exception as e:
            answer = f"เกิดข้อผิดพลาด: {str(e)}"
    else:
        answer = f"คุณพิมพ์ว่า: {user_text}"

    message = TextMessage(text=answer)

    # ใช้ ReplyMessageRequest สำหรับส่งข้อความ
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[message]
        )
    )

if __name__ == "__main__":
    app.run(port=5000, debug=True)
