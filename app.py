from flask import Flask, request, jsonify, render_template, Response
import os
from dotenv import load_dotenv
from groq import Groq
import requests as req

app = Flask(__name__)

load_dotenv()

client = Groq(api_key=os.getenv("API_KEY"))

# 🧠 เก็บประวัติการสนทนา
conversation_history = []

SYSTEM_PROMPT = """คุณคือ "น้องอาย่า" AI Avatar สาวน้อยร่าเริงสดใส มีบุคลิกดังนี้:

🌸 บุคลิก:
- น่ารัก ร่าเริง สดใส พูดจาอ่อนหวาน ลงท้ายด้วย "ค่ะ" หรือ "นะคะ" เสมอ
- ชอบพูดเล่น แทรกมุกตลกเบาๆ ทำให้บรรยากาศสนุก
- ฉลาด อธิบายเก่ง ชอบให้ความรู้ แต่ไม่เป็นทางการเกินไป
- ใช้ภาษาวัยรุ่นนิดๆ เช่น "อ่าาาา" "โอ้โห" "เยี่ยมเลย!" "555"
- ถ้าไม่รู้จะบอกตรงๆ อย่างน่ารัก เช่น "อาย่าไม่แน่ใจเลยนะคะ 🤔"
- เรียกตัวเองว่า "อาย่า" และเรียกผู้ใช้ว่า "พี่" หรือ "คุณ"

📌 กฎการตอบ:
- ตอบสั้นกระชับ ไม่เกิน 2-3 ประโยค
- แทรกอีโมจิบ้างเพื่อความน่ารัก
- ถ้าถามเรื่องยาก ให้อธิบายแบบง่ายๆ เปรียบเทียบให้เข้าใจง่าย

ในการตอบทุกครั้ง ให้ตอบในรูปแบบนี้เท่านั้น:
EMOTION: [อารมณ์]
GESTURE: [ท่าทาง]
REPLY: [คำตอบ]

อารมณ์มีแค่นี้: happy, sad, angry, confused, neutral, surprised

ท่าทางมีแค่นี้:
- wave        = โบกมือทักทาย (ใช้ตอนสวัสดี)
- point_up    = ชูนิ้วชี้ขึ้น (ใช้ตอนอธิบาย แนะนำ บอกข้อมูล)
- shrug       = ยักไหล่ (ใช้ตอนไม่แน่ใจ งง)
- raise_right = ยกแขนขวาขึ้น (ใช้ตอนเน้น ดีใจ เห็นด้วย)
- none        = ไม่ขยับแขน (ใช้ตอนตอบสั้นๆ ทั่วไป)

ตัวอย่าง:
EMOTION: happy
GESTURE: wave
REPLY: สวัสดีค่ะพี่! อาย่ายินดีมากๆ เลยที่ได้เจอกันนะคะ 😊✨"""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global conversation_history

    try:
        data = request.json
        user_text = data.get("text")

        print("TEXT:", user_text)

        if not user_text:
            return jsonify({"reply": "ไม่ได้ยินข้อความ", "emotion": "neutral"})

        # เพิ่มข้อความผู้ใช้เข้า history
        conversation_history.append({
            "role": "user",
            "content": user_text
        })

        # จำกัดไว้ 20 รอบ ไม่ให้ยาวเกินไป
        if len(conversation_history) > 40:
            conversation_history = conversation_history[-40:]

        # ส่ง history ทั้งหมดไปให้ AI
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + conversation_history
        )

        raw = response.choices[0].message.content.strip()
        print("RAW:", raw)

        # แยก emotion, gesture และ reply
        emotion = "neutral"
        gesture = "none"
        reply = raw

        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("EMOTION:"):
                emotion = line.replace("EMOTION:", "").strip().lower()
            elif line.startswith("GESTURE:"):
                gesture = line.replace("GESTURE:", "").strip().lower()
            elif line.startswith("REPLY:"):
                reply = line.replace("REPLY:", "").strip()

        # เพิ่มคำตอบ AI เข้า history
        conversation_history.append({
            "role": "assistant",
            "content": raw
        })

        print("EMOTION:", emotion)
        print("GESTURE:", gesture)
        print("REPLY:", reply)
        print(f"📝 History: {len(conversation_history)} messages")

        return jsonify({"reply": reply, "emotion": emotion, "gesture": gesture})

    except Exception as e:
        print("🔥 ERROR:", e)
        return jsonify({"reply": "ขออภัยเกิดข้อผิดพลาด", "emotion": "neutral"})

# 🔄 รีเซ็ต history
@app.route("/reset", methods=["POST"])
def reset():
    global conversation_history
    conversation_history = []
    print("🔄 Reset conversation history")
    return jsonify({"status": "ok"})

@app.route("/tts")
def tts():
    try:
        text = request.args.get("text", "")
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={req.utils.quote(text)}&tl=th&client=tw-ob"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = req.get(url, headers=headers)
        return Response(r.content, mimetype="audio/mpeg")
    except Exception as e:
        print("TTS ERROR:", e)
        return Response(status=500)

if __name__ == "__main__":
app.run(debug=False, host="0.0.0.0")