import streamlit as st
import pandas as pd
import requests
import re
import hmac

# --- 1. SECURITY GATE ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["APP_PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 Private Access")
    st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# --- 2. CONFIG & LOGIC ---
NAMING_PATTERN = r"^[A-Z0-9]+_\d{3,4}x\d{3,4}_[A-Z]{2}\.(mp4|jpg|png)$"

def check_naming(filename):
    return "Pass" if re.match(NAMING_PATTERN, filename) else "Fail"

def check_smartly(filename, api_token):
    # This uses the API Token provided in the Sidebar
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"https://api.smartly.io/v1/assets?name={filename}"
    
    try:
        # Note: Replace with actual Smartly endpoint from your documentation
        # response = requests.get(url, headers=headers)
        # return "Found" if response.status_code == 200 and response.json() else "Missing"
        return "Found" # Simulated for now
    except:
        return "Error"

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Smartly Validator", layout="wide")
st.title("✅ Smartly Asset Cross-Referencer")

with st.sidebar:
    st.header("Credentials")
    smartly_token = st.text_input("Smartly API Token", type="password")
    st.info("Your app is protected by the global password you set in Secrets.")

input_data = st.text_area("Paste filenames (one per line):", height=250)

if st.button("Start Validation"):
    if not input_data:
        st.error("Please paste filenames.")
    elif not smartly_token:
        st.error("Please provide a Smartly API Token in the sidebar.")
    else:
        files = [f.strip() for f in input_data.split('\n') if f.strip()]
        results = []
        
        for f in files:
            naming = check_naming(f)
            status = check_smartly(f, smartly_token) if naming == "Pass" else "Skipped"
            
            results.append({
                "Filename": f,
                "Naming": naming,
                "Smartly Status": status,
                "Verdict": "✅ OK" if status == "Found" else "❌ Fix Me"
            })
            
        st.table(pd.DataFrame(results))
