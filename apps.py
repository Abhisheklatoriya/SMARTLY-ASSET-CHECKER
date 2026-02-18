import streamlit as st
import dropbox
from dropbox.exceptions import ApiError

st.title("📦 Smartly File Matcher")

# Sidebar for Configuration
with st.sidebar:
    st.header("Settings")
    dbx_token = st.text_input("Enter Dropbox Access Token", type="password")
    st.info("Note: Your app is restricted to the 'Smartly' App folder.")

if not dbx_token:
    st.warning("Please enter your Dropbox Access Token to proceed.")
else:
    dbx = dropbox.Dropbox(dbx_token)

    # 1. File Upload Section
    st.subheader("Upload Local Files")
    uploaded_files = st.file_uploader("Drop files here to check against Dropbox", accept_multiple_files=True)

    if uploaded_files:
        try:
            # IMPORTANT: For "App folder" access, use '' to refer to the folder itself
            res = dbx.files_list_folder('')
            
            # Create a set of filenames currently in the 'Smartly' folder
            dropbox_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}
            
            st.divider()
            st.subheader("Results")

            for file in uploaded_files:
                col1, col2 = st.columns([3, 1])
                col1.text(file.name)
                
                if file.name in dropbox_filenames:
                    col2.success("Matched")
                else:
                    col2.error("Not Matched")
                    
        except ApiError as e:
            st.error(f"Could not connect to Dropbox. Check if your token is valid. Error: {e}")
