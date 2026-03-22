import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

try:
    from google import genai
    client = genai.Client(api_key=api_key)
    
    # Try gemini-3.1-flash-lite-preview
    try:
        print("Trying gemini-3.1-flash-lite-preview...")
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents="hello"
        )
        print("Success:", response.text)
    except Exception as e:
        print("Error with 3.1:", e)

    # Try gemini-2.0-flash
    try:
        print("\nTrying gemini-2.0-flash...")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="hello"
        )
        print("Success:", response.text)
    except Exception as e:
        print("Error with 2.0:", e)

    # List models to see what's actually available
    print("\nAvailable models:")
    for m in client.models.list():
        if "gemini" in m.name and "vision" not in m.name:
            print(m.name)
            
except Exception as e:
    print("Failed to init genai:", e)
