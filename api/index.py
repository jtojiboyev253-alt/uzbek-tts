from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
import edge_tts

app = FastAPI()

# --- FRONTEND (The User Interface) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uzbek AI Voice</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--tg-theme-bg-color, #f0f2f5);
            color: var(--tg-theme-text-color, #000);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background: var(--tg-theme-secondary-bg-color, #fff);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        h2 { margin-bottom: 20px; color: var(--tg-theme-button-color, #3390ec); }
        
        textarea {
            width: 90%;
            height: 100px;
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #ddd;
            font-size: 16px;
            resize: none;
            background-color: var(--tg-theme-bg-color, #fff);
            color: var(--tg-theme-text-color, #000);
        }

        /* Dropdown for Voice Selection */
        select {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #ddd;
            font-size: 16px;
            background-color: var(--tg-theme-bg-color, #fff);
            color: var(--tg-theme-text-color, #000);
        }

        button {
            background-color: var(--tg-theme-button-color, #3390ec);
            color: var(--tg-theme-button-text-color, #fff);
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
            width: 100%;
        }
        button:active { transform: scale(0.98); opacity: 0.9; }
        #status { margin-top: 15px; font-size: 14px; color: gray; min-height: 20px;}
    </style>
</head>
<body>

    <div class="container">
        <h2>🇺🇿 O'zbek AI Voice</h2>
        
        <textarea id="textInput" placeholder="Matnni shu yerga yozing...">Salom! Bugun ob-havo qanday?</textarea>
        
        <select id="voiceSelect">
            <option value="uz-UZ-MadinaNeural">👩 Madina (Ayol)</option>
            <option value="uz-UZ-SardorNeural">👨 Sardor (Erkak)</option>
        </select>

        <button onclick="playAudio()">🔊 Ovoz berish</button>
        <p id="status"></p>
    </div>

    <script>
        // Check if running inside Telegram
        if (window.Telegram && window.Telegram.WebApp) {
            window.Telegram.WebApp.ready();
            window.Telegram.WebApp.expand();
        }

        async function playAudio() {
            const text = document.getElementById("textInput").value;
            const voice = document.getElementById("voiceSelect").value; // Get selected voice
            const status = document.getElementById("status");
            
            if (!text) {
                status.innerText = "⚠️ Iltimos, matn yozing!";
                return;
            }

            status.innerText = "⏳ Generatsiya qilinmoqda...";

            try {
                const response = await fetch("/speak", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: text, voice: voice }) // Send both text and voice
                });

                if (!response.ok) throw new Error("Server xatosi");

                const blob = await response.blob();
                const audio = new Audio(URL.createObjectURL(blob));
                audio.play();

                status.innerText = "✅ Tayyor!";
            } catch (e) {
                status.innerText = "❌ Xatolik yuz berdi.";
                console.error(e);
            }
        }
    </script>
</body>
</html>
"""

# --- BACKEND (The Logic) ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT

@app.post("/speak")
async def speak(request: Request):
    data = await request.json()
    text = data.get("text") or "Salom"
    
    # Get the voice from the user, default to Madina if missing
    voice = data.get("voice") or "uz-UZ-MadinaNeural"
    
    communicate = edge_tts.Communicate(text, voice)
    
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
            
    return Response(content=audio_data, media_type="audio/mpeg")

