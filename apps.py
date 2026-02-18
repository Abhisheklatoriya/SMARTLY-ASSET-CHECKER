import streamlit as st
import dropbox
from dropbox import Dropbox

st.set_page_config(page_title="Smartly Asset Checker")

# 1. Access Secrets Safely
try:
    # This matches the names in the TOML block above
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    dbx_creds = st.secrets["dropbox"]
except KeyError as e:
    st.error(f"Secret key {e} not found. Please update Streamlit Cloud Secrets.")
    st.stop()

st.title("📦 Smartly Asset Checker")

# 2. Sidebar Password
user_pwd = st.sidebar.text_input("App Password", type="password")
if user_pwd != APP_PASSWORD:
    st.info("Enter the app password in the sidebar to begin.")
    st.stop()

# 3. Initialize Dropbox with Refresh Token (for Full Access)
@st.cache_resource
def get_dbx_client():
    return Dropbox(
        app_key=dbx_creds["app_key"],
        app_secret=dbx_creds["app_secret"],
        oauth2_refresh_token=dbx_creds["refresh_token"]
    )

dbx = get_dbx_client()

# 4. File Comparison
uploaded_files = st.file_uploader("Upload local files to verify", accept_multiple_files=True)

if uploaded_files:
    try:
        # Since you have FULL access, we specify the folder name exactly
        # Ensure your folder is in the root of Dropbox named 'Smartly'
        FOLDER_PATH = '/Smartly' 
        
        # Get the list of filenames
        res = dbx.files_list_folder(FOLDER_PATH)
        dbx_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}

        st.divider()
        st.subheader(f"Results for folder: {FOLDER_PATH}")
        
        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            col1.write(f"📄 {file.name}")
            
            if file.name in dbx_filenames:
                col2.success("Matched ✅")
            else:
                col2.error("Missing ❌")
                
    except dropbox.exceptions.ApiError as e:
        st.error(f"Dropbox Error: Could not find folder '{FOLDER_PATH}'. Ensure it exists in your main Dropbox.")
    except Exception as e:
        st.error(f"Error: {e}")
