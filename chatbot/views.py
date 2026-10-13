from django.shortcuts import render

# Create your views here.
import os
from django.shortcuts import render
from django.http import JsonResponse
from google import genai
from dotenv import load_dotenv

# .env ফাইল লোড করা
load_dotenv()

# Gemini Client ইনিশিয়ালাইজ করা
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def chat_view(request):
    if request.method == "POST":
        user_message = request.POST.get("message", "").strip()
        
        if not user_message:
            return JsonResponse({"error": "খালি বার্তা পাঠানো যাবে না।"}, status=400)
        
        try:
            # Gemini API-তে প্রম্পট পাঠানো
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_message,
            )
            return JsonResponse({"reply": response.text})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, "chatbot/chat.html")