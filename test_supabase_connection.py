
import toml
from supabase import create_client

def test_connection():
    try:
        # Load secrets
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["supabase"]["url"]
        key = secrets["supabase"]["key"]
        
        print(f"Testing connection to: {url}")
        
        # Init client
        supabase = create_client(url, key)
        
        # Try a simple select (should return empty list if table exists but empty, or list of rows)
        response = supabase.table("searches").select("*").limit(1).execute()
        
        print("Connection successful!")
        print(f"Data received: {response.data}")
        
    except FileNotFoundError:
        print("Error: .streamlit/secrets.toml not found.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
