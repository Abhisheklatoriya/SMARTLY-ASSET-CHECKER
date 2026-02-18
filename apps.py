import streamlit as st
import dropbox
from dropbox import Dropbox

st.set_page_config(page_title="Smartly Asset Checker", layout="centered")

# 1. Access Secrets Safely
try:
    # This prevents the KeyError by checking for the specific names we set in step 1
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    dbx_creds = st.secrets["dropbox"]
except KeyError as e:
    st.error(f"Missing Secret: {e}. Please check your Streamlit Cloud Secrets settings.")
    st.stop()

st.title("📦 Smartly Asset Checker")

# 2. Login Sidebar
user_pwd = st.sidebar.text_input("App Password", type="password")
if user_pwd != APP_PASSWORD:
    st.info("Enter the app password in the sidebar to begin.")
    st.stop()

# 3. Initialize Dropbox with Full Access logic
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
        # Ensure it matches the folder name in your screenshot ('Smartly')
        FOLDER_PATH = '/Smartly' 
        
        # List all files in that folder
        res = dbx.files_list_folder(FOLDER_PATH)
        dbx_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}

        st.divider()
        st.subheader(f"Results (Found {len(dbx_filenames)} files in Dropbox)")
        
        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            col1.write(f"📄 {file.name}")
            
            if file.name in dbx_filenames:
                col2.success("Matched ✅")
            else:
                col2.error("Missing ❌")
                
    except dropbox.exceptions.ApiError as e:
        st.error(f"Dropbox Error: Could not find folder '{FOLDER_PATH}'. Check if the folder is in the root of your Dropbox.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
