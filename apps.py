import streamlit as st
import dropbox
from dropbox.exceptions import ApiError

st.set_page_config(page_title="Smartly Asset Checker", layout="wide")

st.title("📦 Smartly Asset Checker")

# Retrieve the token from Streamlit Secrets
try:
    dbx_token = st.secrets["DROPBOX_TOKEN"]
    dbx = dropbox.Dropbox(dbx_token)
except KeyError:
    st.error("Missing secret: 'DROPBOX_TOKEN'. Please add it to your Streamlit App Secrets.")
    st.stop()

# File Upload Section
uploaded_files = st.file_uploader("Upload files to check against Dropbox", accept_multiple_files=True)

if uploaded_files:
    try:
        # Since you use 'App Folder' access, '' refers to the root of that specific folder
        res = dbx.files_list_folder('')
        
        # Get all filenames currently in the Dropbox folder
        dbx_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}

        st.subheader("Comparison Results")
        
        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            col1.text(file.name)
            
            if file.name in dbx_filenames:
                col2.success("Matched ✅")
            else:
                col2.error("Not Matched ❌")
                
    except ApiError as e:
        st.error(f"Dropbox API Error: {e}")
