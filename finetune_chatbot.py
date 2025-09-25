import os
import json
import requests
from datetime import datetime
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FineTuneChatBot:
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
        self.conversation_history = []
        self.available_deployments = []
        
    def get_deployments(self):
        """Fetch available deployments from Azure OpenAI"""
        try:
            url = f"{self.endpoint}/openai/deployments?api-version={self.api_version}"
            headers = {"api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    deployments = []
                    for dep in data["data"]:
                        deployments.append({
                            'name': dep.get('id', 'Unknown'),
                            'model': dep.get('model', 'Unknown'),
                            'status': dep.get('status', 'Unknown')
                        })
                    return deployments
                else:
                    print("⚠️  No deployments found in response")
                    return []
            else:
                print(f"❌ Failed to fetch deployments: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching deployments: {e}")
            return []
    
    def select_deployment(self):
        """Let user select which deployment to use"""
        deployments = self.get_deployments()
        
        if not deployments:
            print("❌ No deployments available. Please create a deployment first.")
            return False
        
        print("\n🚀 Available Deployments:")
        print("=" * 60)
        
        # Separate base models and fine-tuned models
        base_models = []
        finetuned_models = []
        
        for i, dep in enumerate(deployments):
            model_name = dep['model']
            if 'ft-' in model_name or 'fine' in model_name.lower():
                finetuned_models.append((i, dep))
            else:
                base_models.append((i, dep))
        
        # Display base models
        if base_models:
            print("\n📋 Base Models:")
            for i, dep in base_models:
                print(f"  {i+1}. {dep['name']} ({dep['model']}) - Status: {dep['status']}")
        
        # Display fine-tuned models
        if finetuned_models:
            print("\n🎯 Fine-tuned Models:")
            for i, dep in finetuned_models:
                print(f"  {i+1}. {dep['name']} ({dep['model']}) - Status: {dep['status']}")
        
        print(f"\n  {len(deployments)+1}. Compare two models side-by-side")
        print(f"  {len(deployments)+2}. Exit")
        
        while True:
            try:
                choice = input(f"\nChoose deployment (1-{len(deployments)+2}): ").strip()
                
                if choice == str(len(deployments)+1):
                    return self.compare_models_mode()
                elif choice == str(len(deployments)+2):
                    return False
                
                choice_num = int(choice) - 1
                if 0 <= choice_num < len(deployments):
                    selected = deployments[choice_num]
                    self.current_deployment = selected['name']
                    self.available_deployments = deployments
                    
                    print(f"\n✅ Selected: {selected['name']} ({selected['model']})")
                    
                    # Check if it's a fine-tuned model
                    if 'ft-' in selected['model'] or 'fine' in selected['model'].lower():
                        print("🎯 This is a FINE-TUNED model!")
                    else:
                        print("📋 This is a BASE model")
                    
                    return True
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def compare_models_mode(self):
        """Compare responses from two different models"""
        deployments = self.available_deployments or self.get_deployments()
        
        if len(deployments) < 2:
            print("❌ Need at least 2 deployments for comparison")
            return False
        
        print("\n🔄 Model Comparison Mode")
        print("Choose two models to compare:")
        
        # Select first model
        print("\n📋 Select FIRST model:")
        for i, dep in enumerate(deployments):
            print(f"  {i+1}. {dep['name']} ({dep['model']})")
        
        while True:
            try:
                choice1 = int(input("First model: ")) - 1
                if 0 <= choice1 < len(deployments):
                    model1 = deployments[choice1]
                    break
                print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a number")
        
        # Select second model
        print("\n📋 Select SECOND model:")
        for i, dep in enumerate(deployments):
            if i != choice1:
                print(f"  {i+1}. {dep['name']} ({dep['model']})")
        
        while True:
            try:
                choice2 = int(input("Second model: ")) - 1
                if 0 <= choice2 < len(deployments) and choice2 != choice1:
                    model2 = deployments[choice2]
                    break
                print("❌ Invalid choice or same as first model")
            except ValueError:
                print("❌ Please enter a number")
        
        print(f"\n🔄 Comparing:")
        print(f"  Model 1: {model1['name']} ({model1['model']})")
        print(f"  Model 2: {model2['name']} ({model2['model']})")
        
        return self.run_comparison_chat(model1['name'], model2['name'])
    
    def run_comparison_chat(self, model1_name, model2_name):
        """Run chat with side-by-side comparison"""
        print(f"\n🤖 Comparison Chat Mode")
        print("Type 'quit' to exit, 'switch' to change models, 'save' to export conversation")
        print("=" * 80)
        
        while True:
            user_input = input("\n🗣️  You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'switch':
                return self.select_deployment()
            elif user_input.lower() == 'save':
                self.save_conversation()
                continue
            elif not user_input:
                continue
            
            print(f"\n{'='*80}")
            print(f"📤 Question: {user_input}")
            print(f"{'='*80}")
            
            # Get response from both models
            response1 = self.get_model_response(user_input, model1_name)
            response2 = self.get_model_response(user_input, model2_name)
            
            # Display side by side
            print(f"\n🤖 {model1_name}:")
            print("─" * 40)
            print(response1)
            
            print(f"\n🎯 {model2_name}:")
            print("─" * 40)
            print(response2)
            
            # Save to history
            self.conversation_history.append({
                'timestamp': datetime.now().isoformat(),
                'user': user_input,
                'model1_name': model1_name,
                'model1_response': response1,
                'model2_name': model2_name,
                'model2_response': response2
            })
        
        return True
    
    def get_model_response(self, message, deployment_name):
        """Get response from a specific model deployment"""
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant that replies in Hinglish (female style)."},
                {"role": "user", "content": message}
            ]
            
            response = self.client.chat.completions.create(
                model=deployment_name,
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"❌ Error: {str(e)[:100]}..."
    
    def run_single_model_chat(self):
        """Run chat with single selected model"""
        print(f"\n🤖 Chatting with: {self.current_deployment}")
        print("Type 'quit' to exit, 'switch' to change model, 'save' to export conversation")
        print("=" * 60)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that replies in Hinglish (female style)."}
        ]
        
        while True:
            user_input = input("\n🗣️  You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'switch':
                return self.select_deployment()
            elif user_input.lower() == 'save':
                self.save_conversation()
                continue
            elif user_input.lower() == 'clear':
                messages = [messages[0]]  # Keep only system message
                print("🧹 Conversation cleared!")
                continue
            elif not user_input:
                continue
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            try:
                response = self.client.chat.completions.create(
                    model=self.current_deployment,
                    messages=messages,
                    max_tokens=200,
                    temperature=0.7
                )
                
                assistant_response = response.choices[0].message.content.strip()
                messages.append({"role": "assistant", "content": assistant_response})
                
                print(f"\n🤖 {self.current_deployment}: {assistant_response}")
                
                # Save to history
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'user': user_input,
                    'model': self.current_deployment,
                    'response': assistant_response
                })
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                messages.pop()  # Remove user message if error occurred
        
        return True
    
    def save_conversation(self):
        """Save conversation history to file"""
        if not self.conversation_history:
            print("📝 No conversation to save!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Conversation saved to: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save conversation: {e}")
    
    def run(self):
        """Main chatbot loop"""
        print("🎯 Fine-Tuned Model Chatbot")
        print("=" * 50)
        print("Test and compare your fine-tuned models!")
        
        while True:
            if not self.select_deployment():
                break
            
            if not self.run_single_model_chat():
                break

if __name__ == "__main__":
    bot = FineTuneChatBot()
    bot.run()