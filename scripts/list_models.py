# list_models.py
from config import client

def main():
    models = client.models.list()
    data = getattr(models, "data", models)
    print("=== AVAILABLE MODEL IDS ===")
    for m in data:
        try:
            print("-", m.id)
        except Exception:
            print("-", m)

if __name__ == "__main__":
    main()
