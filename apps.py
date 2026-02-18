import streamlit as st
import dropbox
from dropbox.exceptions import ApiError

st.set_page_config(page_title="Smartly Asset Checker", layout="centered")

st.title("📦 Smartly Asset Checker")

# Retrieve the token safely from Streamlit Secrets
if "DROPBOX_TOKEN" not in st.secrets:
    st.error("Missing 'DROPBOX_TOKEN' in Streamlit Secrets!")
    st.stop()

dbx_token = st.secrets["DROPBOX_TOKEN"]
dbx = dropbox.Dropbox(dbx_token)

# 1. File Upload Section
st.subheader("Step 1: Upload Local Assets")
uploaded_files = st.file_uploader("Upload files to check", accept_multiple_files=True)

if uploaded_files:
    try:
        # 2. Fetch current Dropbox files
        # Using '' because you have 'App Folder' access restricted to /Smartly
        res = dbx.files_list_folder('')
        
        # Create a set of filenames for fast matching
        dbx_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}

        st.divider()
        st.subheader("Step 2: Comparison Results")
        
        # 3. Match Logic
        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            col1.write(f"📄 {file.name}")
            
            if file.name in dbx_filenames:
                col2.success("Matched ✅")
            else:
                col2.error("Missing ❌")
                
    except ApiError as e:
        st.error(f"Dropbox connection failed. Check your token permissions. Error: {e}")
