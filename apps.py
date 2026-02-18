import streamlit as st
import dropbox
from dropbox.exceptions import ApiError

# App Title
st.title("📦 Dropbox File Matcher")

# Sidebar for Configuration
with st.sidebar:
    st.header("Settings")
    dbx_token = st.text_input("Enter Dropbox Access Token", type="password")

if not dbx_token:
    st.warning("Please enter your Dropbox Access Token to proceed.")
else:
    # Initialize Dropbox
    dbx = dropbox.Dropbox(dbx_token)

    # 1. File Upload Section
    st.subheader("Upload Local Files")
    uploaded_files = st.file_uploader("Choose files to check against Dropbox", accept_multiple_files=True)

    if uploaded_files:
        # 2. Fetch Dropbox File List
        try:
            # We list files in the root; change '' to a specific folder path if needed
            res = dbx.files_list_folder('')
            # Extract filenames into a set for O(1) lookup efficiency
            dropbox_filenames = {entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}
            
            st.divider()
            st.subheader("Matching Results")

            # 3. Comparison Logic
            for file in uploaded_files:
                col1, col2 = st.columns([2, 1])
                col1.write(f"**{file.name}**")
                
                if file.name in dropbox_filenames:
                    col2.success("Matched ✅")
                else:
                    col2.error("Not Matched ❌")
                    
        except ApiError as e:
            st.error(f"Dropbox API Error: {e}")
