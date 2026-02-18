import streamlit as st
import dropbox
from dropbox import Dropbox

st.set_page_config(page_title="Smartly Asset Checker")

# 1. Secure Access Check
if "dropbox" not in st.secrets or "APP_PASSWORD" not in st.secrets:
    st.error("Please configure Secrets in the Streamlit Dashboard.")
    st.stop()

st.title("📦 Smartly Asset Checker")

# Simple Sidebar Login
user_pwd = st.sidebar.text_input("Enter App Password", type="password")
if user_pwd != st.secrets["APP_PASSWORD"]:
    st.info("Please enter the password in the sidebar to begin.")
    st.stop()

# 2. Connect to Dropbox (using Refresh Token for long-term access)
@st.cache_resource
def init_dropbox():
    return Dropbox(
        app_key=st.secrets["dropbox"]["app_key"],
        app_secret=st.secrets["dropbox"]["app_secret"],
        oauth2_refresh_token=st.secrets["dropbox"]["refresh_token"]
    )

dbx = init_dropbox()

# 3. File Comparison UI
uploaded_files = st.file_uploader("Upload files to check against Dropbox", accept_multiple_files=True)

if uploaded_files:
    try:
        # Since you have 'App Folder' access, '' points to /Apps/Smartly asset checker/
        res = dbx.files_list_folder('')
        dbx_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}

        st.subheader("Comparison Results")
        if not dbx_filenames:
            st.warning("Your Dropbox App Folder is currently empty.")

        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            col1.write(f"📄 {file.name}")
            if file.name in dbx_filenames:
                col2.success("Matched ✅")
            else:
                col2.error("Missing ❌")
                
    except Exception as e:
        st.error(f"Error: {e}")
