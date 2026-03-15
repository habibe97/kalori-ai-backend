from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from foods_db import foods_db

load_dotenv()

app = Flask(__name__)

API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"

headers = {
    "Authorization": f"Bearer {os.getenv('HUGGINGFACE_TOKEN')}"
}

portion_multiplier = {
    "small": 0.8,
    "medium": 1,
    "large": 1.4
}

food_mapping = {
    "beans": "kurufasulye",
    "bean": "kurufasulye",
    "lentil": "mercimek corbasi",
    "dumpling": "manti",
    "dumplings": "manti",
    "gyro": "doner",
    "shawarma": "doner",
    "pastry": "borek",
    "cake": "baklava",
    "rice": "pilav",
    "meatball": "kofte",
    "chicken": "tavuk",
    "grilled chicken": "tavuk izgara"
}


@app.route("/")
def home():
    return "Kalori AI Backend Çalışıyor"


@app.route("/analyze", methods=["POST"])
def analyze():

    if "image" not in request.files:
        return jsonify({"error": "image gönderilmedi"})

    image = request.files["image"].read()
    portion = request.form.get("portion", "medium")

    try:

        response = requests.post(
            API_URL,
            headers=headers,
            data=image,
            timeout=30
        )

        if response.status_code != 200:
            print("HF ERROR:", response.text)
            return jsonify({
                "food": "AI çalışmadı",
                "portion": portion,
                "calorie": 200
            })

        try:
            result = response.json()
        except:
            print("JSON PARSE ERROR:", response.text)
            return jsonify({
                "food": "AI cevap hatası",
                "portion": portion,
                "calorie": 200
            })

        caption = ""

        if isinstance(result, list) and "generated_text" in result[0]:
            caption = result[0]["generated_text"].lower()

        caption = caption.replace("_", " ").replace("-", " ")

        print("AI caption:", caption)

        food_key = "unknown"

        # foods_db kontrol
        for food in foods_db.keys():
            if food in caption:
                food_key = food
                break

        # mapping kontrol
        if food_key == "unknown":
            for key in food_mapping:
                if key in caption:
                    food_key = food_mapping[key]
                    break

        if food_key == "unknown":
            return jsonify({
                "food": "Bilinmeyen Yemek",
                "portion": portion,
                "calorie": 200
            })

        base_calorie = foods_db.get(food_key, 200)
        multiplier = portion_multiplier.get(portion, 1)

        calorie = int(base_calorie * multiplier)

        return jsonify({
            "food": food_key.title(),
            "portion": portion,
            "calorie": calorie
        })

    except Exception as e:
        print("SERVER ERROR:", e)

        return jsonify({
            "food": "Sunucu hatası",
            "portion": portion,
            "calorie": 200
        })


@app.route("/coach", methods=["POST"])
def coach():

    data = request.json
    total = data.get("total", 0)
    goal = data.get("goal", 2000)

    remaining = goal - total

    if remaining > 1000:
        advice = "Bugün kalori alımın düşük görünüyor."
    elif remaining > 500:
        advice = "Günlük hedefe yaklaşıyorsun."
    elif remaining > 0:
        advice = "Hedefe çok yakınsın."
    else:
        advice = "Kalori hedefini geçtin."

    return jsonify({
        "advice": advice,
        "remaining": remaining
    })


@app.route("/weekly", methods=["POST"])
def weekly():

    data = request.json
    weekly = data.get("weekly", [])
    goal = data.get("goal", 2000)

    if len(weekly) == 0:
        return jsonify({"analysis": "Henüz veri yok"})

    avg = sum(weekly) / len(weekly)

    if avg < goal * 0.7:
        advice = "Kalori düşük"
    elif avg > goal * 1.2:
        advice = "Kalori fazla"
    else:
        advice = "Dengeli"

    return jsonify({
        "analysis": advice,
        "average": avg
    })


@app.route("/mealplan", methods=["POST"])
def meal_plan():

    goal = request.json.get("goal", 2000)

    return jsonify({
        "breakfast": ["Yulaf", "Omlet", "Yoğurt"],
        "lunch": ["Tavuk pilav", "Ton balıklı salata"],
        "dinner": ["Sebze yemeği", "Izgara tavuk"],
        "goal": goal
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
