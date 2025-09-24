#!/usr/bin/env python3
"""
Simple Azure OpenAI Chatbot

A clean, easy-to-use chatbot for Azure OpenAI.
Automatically detects your deployments and provides a smooth chat experience.

Features:
- Auto-detects available deployments
- Clean conversation interface
- Easy model switching
- Conversation memory
- Simple commands

Usage:
    python simple_chatbot.py
"""

import os
import requests
import time
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleChatBot:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT').rstrip('/')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
        
        self.client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
        )
        
        self.current_deployment = None
        self.messages = []
        
    def get_deployments(self):
        """Get available deployments"""
        try:
            url = f"{self.endpoint}/openai/deployments?api-version={self.api_version}"
            headers = {"api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    deployments = []
                    for dep in data["data"]:
                        if dep.get('status') == 'succeeded':  # Only working deployments
                            deployments.append({
                                'name': dep.get('id', 'Unknown'),
                                'model': dep.get('model', 'Unknown')
                            })
                    return deployments
                else:
                    return []
            else:
                print(f"❌ Error fetching deployments: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return []
    
    def select_deployment(self):
        """Let user choose a deployment"""
        deployments = self.get_deployments()
        
        if not deployments:
            print("❌ No working deployments found!")
            print("Please create a deployment in Azure Portal first.")
            return False
        
        print("\n🤖 Available Chat Models:")
        print("=" * 50)
        
        for i, dep in enumerate(deployments):
            model_type = "🎯 Fine-tuned" if 'ft-' in dep['model'] else "📋 Base"
            print(f"  {i+1}. {dep['name']} ({model_type})")
        
        while True:
            try:
                choice = input(f"\nChoose a model (1-{len(deployments)}): ").strip()
                choice_num = int(choice) - 1
                
                if 0 <= choice_num < len(deployments):
                    selected = deployments[choice_num]
                    self.current_deployment = selected['name']
                    
                    model_type = "🎯 Fine-tuned Model" if 'ft-' in selected['model'] else "📋 Base Model"
                    print(f"\n✅ Selected: {selected['name']}")
                    print(f"   Type: {model_type}")
                    return True
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return False
    
    def start_conversation(self):
        """Initialize conversation with system message"""
        self.messages = [
            {
                "role": "system", 
                "content": "You are a helpful and friendly assistant. Be conversational and engaging."
            }
        ]
    
    def chat(self):
        """Main chat loop"""
        print(f"\n💬 Chatting with: {self.current_deployment}")
        print("=" * 60)
        print("Commands:")
        print("  • Type 'quit' or 'exit' to leave")
        print("  • Type 'clear' to start fresh")
        print("  • Type 'switch' to change model")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n🗣️  You: ").strip()
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Thanks for chatting! Goodbye!")
                    break
                    
                elif user_input.lower() == 'clear':
                    self.start_conversation()
                    print("🧹 Conversation cleared! Starting fresh.")
                    continue
                    
                elif user_input.lower() == 'switch':
                    if self.select_deployment():
                        self.start_conversation()
                        continue
                    else:
                        break
                        
                elif not user_input:
                    continue
                
                # Add user message
                self.messages.append({"role": "user", "content": user_input})
                
                # Get AI response
                try:
                    response = self.client.chat.completions.create(
                        model=self.current_deployment,
                        messages=self.messages,
                        max_tokens=300,
                        temperature=0.7,
                        top_p=0.9
                    )
                    
                    assistant_response = response.choices[0].message.content.strip()
                    
                    # Add assistant response to conversation
                    self.messages.append({"role": "assistant", "content": assistant_response})
                    
                    # Display response
                    print(f"\n🤖 Assistant: {assistant_response}")
                    
                except Exception as e:
                    print(f"\n❌ Error getting response: {e}")
                    # Remove the user message if we couldn't get a response
                    self.messages.pop()
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
    
    def run(self):
        """Main chatbot entry point"""
        print("🤖 Simple Azure OpenAI Chatbot")
        print("=" * 40)
        
        # Select deployment
        if not self.select_deployment():
            return
        
        # Start conversation
        self.start_conversation()
        
        # Begin chatting
        self.chat()

def main():
    """Run the chatbot"""
    try:
        bot = SimpleChatBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()