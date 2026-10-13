import os
from django.shortcuts import render
from django.http import JsonResponse
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = """
তুমি একটি পার্সোনাল এবং অত্যন্ত দক্ষ AI Assistant। 
যদি ব্যবহারকারী কোনো ডকুমেন্ট বা পিডিএফ ফাইল আপলোড করে, তবে ডকুমেন্টের ভেতরের তথ্য ভালোভাবে পড়ে সেখান থেকে সুনির্দিষ্ট উত্তর দেবে।
বাংলা ভাষায় উত্তর দেয়ার সময় সহজ-সরল ভাষা ব্যবহার করবে।
"""

def chat_view(request):
    chat_history = request.session.get("chat_history", [])

    if request.method == "POST":
        user_message = request.POST.get("message", "").strip()
        uploaded_file = request.FILES.get("pdf_file")
        
        document_text = ""
        
        if uploaded_file:
            try:
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        document_text += text + "\n"
            except Exception as e:
                return JsonResponse({"error": f"PDF পড়তে সমস্যা হয়েছে: {str(e)}"}, status=400)

        if not user_message and not document_text:
            return JsonResponse({"error": "খালি বার্তা বা ফাইল পাঠানো যাবে না।"}, status=400)
        
        try:
            contents = []
            for msg in chat_history:
                contents.append(
                    types.Content(
                        role=msg["role"],
                        parts=[types.Part.from_text(text=msg["text"])]
                    )
                )
            
            final_prompt = user_message
            if document_text:
                final_prompt = f"এখানে একটি ডকুমেন্টের তথ্য দেওয়া হলো:\n{document_text}\n\nপ্রশ্ন: {user_message if user_message else 'এই ফাইলটির মূল বিষয়বস্তু বা সামারি বল।'}"

            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=final_prompt)]
                )
            )

            # মডেলের নাম লেটেস্ট স্টেবল সংস্করণে আপডেট করা হলো
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.7,
                )
            )

            ai_reply = response.text

            display_message = user_message
            if uploaded_file:
                display_message = f"[PDF: {uploaded_file.name}] {user_message}"

            chat_history.append({"role": "user", "text": display_message})
            chat_history.append({"role": "model", "text": ai_reply})
            
            request.session["chat_history"] = chat_history
            request.session.modified = True

            return JsonResponse({"reply": ai_reply})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    if request.GET.get("action") == "clear":
        request.session["chat_history"] = []
        return render(request, "chatbot/chat.html", {"chat_history": []})

    return render(request, "chatbot/chat.html", {"chat_history": chat_history})