import os
import sys
import traceback
from dotenv import load_dotenv
load_dotenv()

# ---------- Configuration (can be set via env or hardcoded defaults) ----------
DEFAULT_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")  # replace "abc" with real key if you wish
DEFAULT_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
DEFAULT_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://work-mfswaj2r-swedencentral.cognitiveservices.azure.com/"
)
# IMPORTANT: This should be the Azure *deployment name* for your fine-tuned model,
# not the long fine-tune model id. You can leave empty and choose at runtime.
DEFAULT_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

# ---------- Import Azure client ----------
try:
    from openai import AzureOpenAI
except Exception as e:
    print("ERROR: openai package not found. Install with: pip install openai")
    raise

# Create client using configured values
API_KEY = DEFAULT_API_KEY
API_VERSION = DEFAULT_API_VERSION
AZURE_ENDPOINT = DEFAULT_ENDPOINT

client = AzureOpenAI(
    api_key=API_KEY,
    api_version=API_VERSION,
    azure_endpoint=AZURE_ENDPOINT,
)




def list_deployments():
    """
    Print available deployments for the configured Azure OpenAI resource.
    Use this to find the correct deployment name to place in model=...
    """
    try:
        import requests
        url = f"{AZURE_ENDPOINT.rstrip('/')}/openai/deployments?api-version={API_VERSION}"
        headers = {"api-key": API_KEY}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        deployments = response.json()
        print("\nAvailable deployments:")
        print("=" * 50)
        
        if "data" in deployments:
            for deployment in deployments["data"]:
                name = deployment.get("id", "Unknown")
                model = deployment.get("model", "Unknown")
                status = deployment.get("status", "Unknown")
                print(f"• {name} (Model: {model}, Status: {status})")
        else:
            print("No deployments found")
            
    except Exception as e:
        print(f"Failed to list deployments. Error: {e}")




def get_deployment_name():
    """
    Resolve the deployment name to use.
    Priority:
      1) AZURE_OPENAI_DEPLOYMENT env
      2) DEFAULT_DEPLOYMENT constant
      3) Ask user interactively (with an option to list deployments)
    """
    if DEFAULT_DEPLOYMENT:
        return DEFAULT_DEPLOYMENT

    env_val = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    if env_val:
        return env_val

    # Ask user
    while True:
        print("\nNo deployment name provided.")
        print("1) Type the deployment name now")
        print("2) List deployments from the resource (recommended if unsure)")
        print("3) Quit")
        choice = input("Choose (1/2/3): ").strip()
        if choice == "1":
            name = input("Enter deployment name (exact, case-sensitive): ").strip()
            if name:
                return name
        elif choice == "2":
            list_deployments()
        elif choice == "3":
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid choice, try again.")


def chat_loop(deployment_name: str):
    """
    Main interactive chat loop. Uses client.chat.completions.create
    with model=<deployment_name>.
    """
    print("\nWelcome to Azure OpenAI CLI Chat! Type 'exit' or 'quit' to end.")
    messages = [{"role": "system", "content": "You are a helpful fine-tuned assistant."}]

    while True:
        try:
            user_input = input("You: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model=deployment_name,  # Must be deployment name from Azure portal
                messages=messages,
            )
        except Exception as e:
            # Helpful error handling for common Azure deployment not found
            err_msg = ""
            try:
                # many exceptions contain .args with details
                err_msg = str(e)
            except Exception:
                err_msg = "Unknown error"

            print("\nRequest failed:")
            print(err_msg)
            if "DeploymentNotFound" in err_msg or "deployment" in err_msg.lower():
                print("\nIt looks like the deployment name may be incorrect or doesn't exist.")
                print("Use the 'list_deployments' function to show available deployment names.")
                want_list = input("List deployments now? (y/N): ").strip().lower()
                if want_list == "y":
                    list_deployments()
                else:
                    print("Please verify the deployment name and try again.")
                # allow user to change deployment interactively
                new_name = input("Enter a new deployment name (or press Enter to keep current): ").strip()
                if new_name:
                    deployment_name = new_name
                    print(f"Using new deployment: {deployment_name}")
                continue
            else:
                # print full traceback for other errors and continue
                traceback.print_exc()
                continue

        # SDK response -> extract assistant message
        try:
            # Many SDKs return choices list; guard for variations
            choices = getattr(response, "choices", None)
            if choices and len(choices) > 0:
                # some SDK types: choices[0].message.content
                first = choices[0]
                msg = getattr(first, "message", None)
                if msg:
                    bot_reply = getattr(msg, "content", None) or msg
                else:
                    # fallback: the choice may be raw dict-like
                    bot_reply = getattr(first, "text", None) or first
            else:
                # fallback: try to access response.choices[0]["message"]["content"]
                try:
                    bot_reply = response["choices"][0]["message"]["content"]
                except Exception:
                    bot_reply = str(response)
        except Exception:
            bot_reply = str(response)

        print(f"Bot: {bot_reply}\n")
        messages.append({"role": "assistant", "content": bot_reply})


def main():
    print("Azure OpenAI endpoint:", AZURE_ENDPOINT)
    print("API version:", API_VERSION)
    # show whether key looks present (do not print key)
    # if not DEFAULT_API_KEY == "abc":
    #     print("WARNING: API key looks like default/placeholder. Set AZURE_OPENAI_API_KEY env var or edit the script.")
    #     # still proceed; user might want a prompt to enter it
    #     if input("Enter API key now? (press Enter to skip) ").strip():
    #         new_key = input("Paste API key: ").strip()
    #         if new_key:
    #             # re-init client with new key
    #             global client
    #             API_KEY = new_key
    #             client = AzureOpenAI(api_key=API_KEY, api_version=API_VERSION, azure_endpoint=AZURE_ENDPOINT)

    deployment_name = get_deployment_name()
    if not deployment_name:
        print("No deployment name provided. Exiting.")
        return

    print(f"Using deployment: {deployment_name}")
    chat_loop(deployment_name)


if __name__ == "__main__":
    main()
