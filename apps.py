import streamlit as st
import pandas as pd
import requests
import dropbox
import re
import hmac

# --- SECURITY & CONFIG ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["APP_PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 Private Access")
    st.text_input("App Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password(): st.stop()

# --- DROPBOX LOGIC ---
def get_dropbox_files(token, folder_path=""):
    dbx = dropbox.Dropbox(token)
    try:
        # If folder_path is empty, it looks at the root
        res = dbx.files_list_folder(folder_path)
        return [entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)]
    except Exception as e:
        st.error(f"Dropbox Error: {e}")
        return []

# --- SMARTLY LOGIC ---
def check_smartly(filename, smartly_token, account_id):
    headers = {"Authorization": f"Bearer {smartly_token}"}
    url = f"https://api.smartly.io/v1/accounts/{account_id}/producer/assets"
    try:
        # Search Smartly for this specific filename
        response = requests.get(url, headers=headers, params={"q": filename})
        if response.status_code == 200:
            return "Found" if len(response.json()) > 0 else "Missing"
        return f"Error {response.status_code}"
    except:
        return "Conn Error"

# --- UI ---
st.set_page_config(page_title="Dropbox -> Smartly Validator")
st.title("📂 Dropbox-to-Smartly Sync Check")

with st.sidebar:
    st.header("API Credentials")
    dbx_token = st.text_input("Dropbox Access Token", type="password")
    sm_token = st.text_input("Smartly Producer Token", type="password")
    account_id = st.text_input("Smartly Account ID")
    folder_path = st.text_input("Dropbox Folder Path", value="", placeholder="/Campaign_Assets")

if st.button("🔍 Scan & Cross-Reference"):
    if not all([dbx_token, sm_token, account_id]):
        st.error("Please fill in all API credentials in the sidebar.")
    else:
        with st.spinner("Fetching files from Dropbox..."):
            filenames = get_dropbox_files(dbx_token, folder_path)
        
        if not filenames:
            st.warning("No files found in that Dropbox folder.")
        else:
            results = []
            for name in filenames:
                status = check_smartly(name, sm_token, account_id)
                results.append({
                    "Filename": name,
                    "Smartly Status": status,
                    "Verdict": "✅ OK" if status == "Found" else "❌ Missing in Smartly"
                })
            
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            
            # Export
            st.download_button("Download Report", df.to_csv(index=False), "audit.csv")
