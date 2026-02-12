import streamlit as st
import pandas as pd
import requests
import dropbox
import hmac

# --- 1. SECURITY & CONFIG ---
def check_password():
    """Simple password gate for your private app."""
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["APP_PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False): return True
    st.title("🔒 Asset Validator Login")
    st.text_input("Enter App Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password(): st.stop()

# --- 2. DROPBOX LOGIC ---
def get_dropbox_filenames(token, folder_path):
    """Lists filenames from a specific Dropbox folder."""
    dbx = dropbox.Dropbox(token)
    try:
        # We fetch the list of files in the folder
        res = dbx.files_list_folder(folder_path)
        # We only keep files (ignoring sub-folders)
        return [entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)]
    except Exception as e:
        st.error(f"Dropbox Error: {e}")
        return []

# --- 3. SMARTLY LOGIC ---
def check_smartly(filename, smartly_token, account_id):
    """Checks if a filename exists in the Smartly Producer Asset Library."""
    headers = {"Authorization": f"Bearer {smartly_token}"}
    # Note: Using the Producer API endpoint
    url = f"https://api.smartly.io/v1/accounts/{account_id}/producer/assets"
    
    try:
        # Searching for the exact filename
        response = requests.get(url, headers=headers, params={"q": filename})
        if response.status_code == 200:
            data = response.json()
            return "Found" if len(data) > 0 else "Missing"
        return f"Error {response.status_code}"
    except:
        return "Connection Error"

# --- 4. APP INTERFACE ---
st.set_page_config(page_title="Dropbox-to-Smartly Checker", layout="wide")
st.title("🚀 Dropbox ➔ Smartly Asset Sync")

with st.sidebar:
    st.header("Settings")
    # Using the token you provided (it will expire soon!)
    dbx_token = st.text_input("Dropbox Token", value="YOUR_TOKEN_HERE", type="password")
    sm_token = st.text_input("Smartly Producer Token", type="password")
    account_id = st.text_input("Smartly Account ID", placeholder="Found in your browser URL")
    folder_name = st.text_input("Folder Path", value="/Asset checker")

if st.button("Run Audit"):
    if not all([dbx_token, sm_token, account_id]):
        st.error("Missing credentials in the sidebar!")
    else:
        with st.spinner("Scanning Dropbox..."):
            dropbox_files = get_dropbox_filenames(dbx_token, folder_name)
        
        if not dropbox_files:
            st.warning("No files found in Dropbox folder.")
        else:
            st.write(f"Found **{len(dropbox_files)}** files in Dropbox. Checking Smartly...")
            
            results = []
            for name in dropbox_files:
                status = check_smartly(name, sm_token, account_id)
                results.append({
                    "Dropbox Filename": name,
                    "Smartly Status": status,
                    "Status": "✅ Sync'd" if status == "Found" else "❌ Missing"
                })
            
            df = pd.DataFrame(results)
            
            # Display interactive table with highlighting
            st.dataframe(df.style.map(
                lambda x: 'background-color: #ffcccc' if x == "❌ Missing" else 'background-color: #ccffcc' if x == "✅ Sync'd" else '',
                subset=['Status']
            ), use_container_width=True)

            st.download_button("Download Report", df.to_csv(index=False), "sync_report.csv")
