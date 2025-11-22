import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def verify_api():
    print("Verifying Anthropic API Key...")
    
    # Load .env explicitly
    env_path = Path('.env')
    if env_path.exists():
        print(f"Loading .env from {env_path.absolute()}")
        load_dotenv(env_path)
    else:
        print("WARNING: .env file not found!")
        
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment variables.")
        return
        
    print(f"API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("Sending test request to Claude...")
        
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Hello, are you working?"}
            ]
        )
        
        print("Success! Response received:")
        print(message.content[0].text)
        
    except anthropic.AuthenticationError:
        print("ERROR: Authentication failed. The API key is invalid.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    verify_api()
