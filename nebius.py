import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY")
)

# Initialize conversation with system message
messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]

print("💬 Chatbot started! (type 'quit', 'exit', or 'bye' to stop)")
print("-" * 50)

while True:
    user_input = input("You: ").strip()
    
    if user_input.lower() in ['quit', 'exit', 'bye']:
        print("Goodbye! 👋")
        break
    
    if not user_input:
        continue
    
    # Add user message to conversation
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-LoRa:my-custom-model-lfyy",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9
        )
        
        # Get assistant response
        assistant_message = response.choices[0].message.content
        print(f"Assistant: {assistant_message}")
        
        # Add assistant message to conversation history
        messages.append({"role": "assistant", "content": assistant_message})
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("-" * 50)