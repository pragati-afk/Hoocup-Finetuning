import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = "gpt-35-turbo"
deployment = "gpt-35-turbod"

subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

# Initialize conversation with system message
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant.",
    }
]

print("🤖 Azure OpenAI Chat Bot")
print("Type 'quit' or 'exit' to end the conversation\n")

while True:
    # Get user input
    user_input = input("You: ").strip()
    
    # Check for exit commands
    if user_input.lower() in ['quit', 'exit', 'bye']:
        print("Goodbye! 👋")
        break
    
    # Skip empty messages
    if not user_input:
        continue
    
    # Add user message to conversation
    messages.append({
        "role": "user",
        "content": user_input
    })
    
    try:
        # Get response from Azure OpenAI
        response = client.chat.completions.create(
            messages=messages,
            max_tokens=4096,
            temperature=1.0,
            top_p=1.0,
            model=deployment
        )
        
        # Get assistant's response
        assistant_response = response.choices[0].message.content
        
        # Add assistant's response to conversation history
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # Print the response
        print(f"Assistant: {assistant_response}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        # Remove the user message if there was an error
        messages.pop()