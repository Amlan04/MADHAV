from flask import Flask, request
from flask_restful import Api, Resource
from flask_cors import CORS
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util
import warnings
import traceback
import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path

# ✅ Force load .env from same directory as this script
dotenv_path = Path(__file__).resolve().parent / ".env"
print(f"📄 Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path, override=True)

# ✅ Load and show partial API key
api_key = os.getenv("GEMINI_API_KEY")
print("🔐 Loaded GEMINI_API_KEY (partial):", api_key[:8] + "..." if api_key else "None")
if not api_key:
    raise EnvironmentError("❌ GEMINI_API_KEY not found in .env file!")

# ✅ Reset Gemini client and configure with correct key
from google.generativeai import generative_models
generative_models._client = None
genai.configure(api_key=api_key)

# ✅ Gemini API key test
def test_gemini_api_key():
    try:
        print("🧪 Testing Gemini API...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Testing Gemini key from Flask backend.")
        print("✅ Gemini responded:", response.text.strip())
    except Exception as e:
        print("❌ Gemini API test failed:")
        traceback.print_exc()

test_gemini_api_key()

# ✅ Ignore torch flash attention warning
warnings.filterwarnings("ignore", message=".*Torch was not compiled with flash attention.*")

# ✅ Setup Flask
app = Flask(__name__)
CORS(app)
api = Api(app)

print("🔄 Starting up...")

try:
    # Device setup
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"✅ Using device: {device}")
    if device == 'cuda':
        print("🧠 GPU:", torch.cuda.get_device_name(0))

    # Load CSV
    print("📁 Loading Bhagavad Gita verses...")
    df = pd.read_csv("processed_v1.0.csv")
    verses = df['EngMeaning'].tolist()

    # Load sentence transformer
    print("🔍 Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2', device=device)

    # Encode verses
    print("📦 Encoding verses into embeddings...")
    verse_embeddings = model.encode(verses, convert_to_tensor=True, device=device)

    print("✅ Initialization complete.")

except Exception as e:
    print("❌ Error during startup:")
    traceback.print_exc()


def create_structured_gemini_payload(convo_history):
    return {
        "contents": [
            {
                "parts": [{"text": msg["content"]}],
                "role": "user" if msg["role"] == "user" else "model"
            }
            for msg in convo_history
        ]
    }


class user_msg_Api(Resource):
    def post(self):
        data = request.get_json()
        user_msg = data.get("message", "").strip()
        history = data.get("history", [])

        print("\n📥 Received message:")
        print(user_msg)

        if not user_msg:
            print("⚠️ Empty message received.")
            return {"error": "Empty input"}, 400

        try:
            print("🔍 Finding best matching verse...")
            input_embedding = model.encode(user_msg, convert_to_tensor=True, device=device)
            cosine_scores = util.cos_sim(input_embedding, verse_embeddings)[0]
            top_idx = torch.argmax(cosine_scores).item()
            top_score = cosine_scores[top_idx].item()
            top_verse = df.iloc[top_idx]

            proccesed_msg = f"""user msg: {user_msg}\n
                            {top_verse['ID']} (Chapter {top_verse['Chapter']}, Verse {top_verse['Verse']})\n
                            {top_verse['EngMeaning']}\n
                            Similarity Score: {round(top_score, 4)}"""

            structured_history = history + [
                {"role": "user", "content": proccesed_msg}
            ]

            payload = create_structured_gemini_payload(structured_history)

            print("────────────────────────────────────────────")
            for h in structured_history:
                print(f"role: {h['role']}, content: {h['content']}")
                print(" ")
            print("────────────────────────────────────────────")

            try:
                gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                response = gemini_model.generate_content(
                    contents=payload["contents"]
                )
                reply = response.text.strip()

                print("\n📤 Final Combined Message to Deliver:")
                print("────────────────────────────────────────────")
                print(reply)
                print("────────────────────────────────────────────")

            except Exception as gen_error:
                print("❌ Gemini API Error:")
                traceback.print_exc()
                reply = "Could not generate response from Gemini."

            return {
                "status": "success",
                "matched_verse": {
                    "chapter": int(top_verse["Chapter"]),
                    "verse": int(top_verse["Verse"]),
                    "eng_meaning": top_verse["EngMeaning"],
                    "similarity": round(top_score, 4)
                },
                "gemini_response":
                    f"{top_verse['ID']} (Chapter {top_verse['Chapter']}, Verse {top_verse['Verse']})\n"
                    f"\n"
                    f"{top_verse['EngMeaning']}\n"
                    f"─────────────────────────────────\n"
                    f"{reply}\n"
                    f"─────────────────────────────────"
            }

        except Exception as e:
            print("❌ Error during processing:")
            traceback.print_exc()
            return {"error": "Internal processing error"}, 500


# API route
api.add_resource(user_msg_Api, "/user_msg_Api")

# Run server
if __name__ == "__main__":
    print("🚀 Running Flask server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
