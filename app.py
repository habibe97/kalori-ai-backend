from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from foods_db import foods_db

load_dotenv()

app = Flask(__name__)

API_URL = "https://router.huggingface.co/hf-inference/models/Salesforce/blip-image-captioning-base"

headers = {
    "Authorization": "Bearer " + os.getenv("HUGGINGFACE_TOKEN"),
    "Content-Type": "application/octet-stream"
}

portion_multiplier = {
    "small": 0.8,
    "medium": 1,
    "large": 1.4
}

# AI benzer yemek eşleştirme
food_mapping = {

    "beans": "kurufasulye",
    "bean stew": "kurufasulye",
    "white beans": "kurufasulye",

    "lentil": "mercimek corbasi",
    "lentil soup": "mercimek corbasi",

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
    return '''
    <h1>AI Kalori Test</h1>
    <form action="/analyze" method="post" enctype="multipart/form-data">
        <input type="file" name="image">
        <select name="portion">
            <option value="small">Küçük</option>
            <option value="medium">Orta</option>
            <option value="large">Büyük</option>
        </select>
        <button type="submit">Analiz Et</button>
    </form>
    '''


@app.route("/analyze", methods=["POST"])
def analyze():

    image = request.files["image"].read()
    portion = request.form.get("portion", "medium")

    response = requests.post(API_URL, headers=headers, data=image)

    if response.status_code != 200:
        return jsonify({
            "error": "AI API hata verdi",
            "detay": response.text
        })

    result = response.json()

    caption = ""

    if isinstance(result, list) and "generated_text" in result[0]:
        caption = result[0]["generated_text"].lower()

    caption = caption.replace("_", " ").replace("-", " ")

    print("AI caption:", caption)

    food_key = "unknown"

    # önce direkt foods_db içinde var mı bak
    for food in foods_db.keys():
        if food in caption:
            food_key = food
            break

    # yoksa mapping kullan
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


@app.route("/coach", methods=["POST"])
def coach():
    data = request.json
    history = data.get("history", [])
    total = data.get("total", 0)
    goal = data.get("goal", 2000)

    remaining = goal - total

    if remaining > 1000:
        advice = "Bugün kalori alımın düşük görünüyor. Protein ve sebze içeren bir öğün ekleyebilirsin."
    elif remaining > 500:
        advice = "Günlük hedefe yaklaşıyorsun. Dengeli bir akşam yemeği iyi olabilir."
    elif remaining > 0:
        advice = "Hedefe çok yakınsın. Hafif bir şey tercih edebilirsin."
    else:
        advice = "Günlük kalori hedefini geçtin. Yarın daha dengeli bir gün planlayabilirsin."

    return jsonify({
        "advice": advice,
        "remaining": remaining
    })


@app.route("/weekly", methods=["POST"])
def weekly_analysis():

    data = request.json
    weekly = data.get("weekly", [])
    goal = data.get("goal", 2000)

    if len(weekly) == 0:
        return jsonify({"analysis": "Henüz haftalık veri yok."})

    average = sum(weekly) / len(weekly)

    if average < goal * 0.7:
        advice = "Bu hafta kalori alımın düşük görünüyor."
    elif average > goal * 1.2:
        advice = "Bu hafta kalori hedefinin üstüne çıkmışsın."
    else:
        advice = "Bu hafta dengeli beslenmişsin."

    return jsonify({
        "analysis": advice,
        "average": average
    })


@app.route("/mealplan", methods=["POST"])
def meal_plan():

    data = request.json
    goal = data.get("goal", 2000)

    breakfast_cal = int(goal * 0.25)
    lunch_cal = int(goal * 0.35)
    dinner_cal = int(goal * 0.40)

    breakfast_options = [
        "Yulaf + süt + muz",
        "Omlet + tam buğday ekmeği",
        "Yoğurt + granola + meyve"
    ]

    lunch_options = [
        "Tavuk + pilav + salata",
        "Ton balıklı salata",
        "Izgara köfte + sebze"
    ]

    dinner_options = [
        "Sebze yemeği + yoğurt",
        "Izgara tavuk + salata",
        "Mercimek çorbası + salata"
    ]

    return jsonify({
        "breakfast": breakfast_options,
        "lunch": lunch_options,
        "dinner": dinner_options,
        "breakfast_cal": breakfast_cal,
        "lunch_cal": lunch_cal,
        "dinner_cal": dinner_cal,
        "goal": goal
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
