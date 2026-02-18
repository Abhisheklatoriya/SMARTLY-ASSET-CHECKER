import streamlit as st
import dropbox
from dropbox import Dropbox

st.set_page_config(page_title="Smartly Asset Checker", layout="centered")

# 1. Access Secrets
try:
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    dbx_creds = st.secrets["dropbox"]
except KeyError as e:
    st.error(f"Missing Secret Key: {e}. Please check your Streamlit Secrets configuration.")
    st.stop()

st.title("📦 Smartly Asset Checker")

# 2. Simple Password Lock
user_pwd = st.sidebar.text_input("App Password", type="password")
if user_pwd != APP_PASSWORD:
    st.info("Please enter the password in the sidebar to access the checker.")
    st.stop()

# 3. Initialize Dropbox with Refresh Token
@st.cache_resource
def get_dbx_client():
    return Dropbox(
        app_key=dbx_creds["app_key"],
        app_secret=dbx_creds["app_secret"],
        oauth2_refresh_token=dbx_creds["refresh_token"]
    )

dbx = get_dbx_client()

# 4. File Comparison Logic
uploaded_files = st.file_uploader("Upload local files to verify", accept_multiple_files=True)

if uploaded_files:
    try:
        # In 'App Folder' mode, '' refers to the root of your 'Smartly asset checker' folder
        res = dbx.files_list_folder('')
        dbx_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}

        st.divider()
        st.subheader("Results")
        
        if not dbx_filenames:
            st.warning("The Dropbox App Folder appears to be empty.")

        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            col1.write(f"📄 {file.name}")
            
            if file.name in dbx_filenames:
                col2.success("Matched ✅")
            else:
                col2.error("Missing ❌")
                
    except Exception as e:
        st.error(f"Dropbox Error: {e}")
