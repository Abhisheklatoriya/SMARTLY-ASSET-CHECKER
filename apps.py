import streamlit as st
import dropbox
import re
import pandas as pd

# --- LOGIC: SPLITTING BULK TEXT ---
def split_filenames(text):
    # Regex finds anything ending in .mp4, .png, .jpg, etc., even if they are stuck together
    pattern = r'[\w\s\.\+\$\-]+?\.(?:mp4|png|jpg|jpeg|mov)'
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches]

# --- LOGIC: DROPBOX PREVIEW ---
def get_direct_link(dbx, path):
    try:
        # This returns a link that expires in 4 hours, perfect for a secure preview
        link_metadata = dbx.files_get_temporary_link(path)
        return link_metadata.link
    except Exception as e:
        return None

# --- UI ---
st.set_page_config(page_title="Asset sync", layout="wide")
st.title("📂 Bulk Dropbox Checker")

with st.sidebar:
    dbx_token = st.text_input("Dropbox Token", type="password")
    folder_path = "/Asset checker"

# 1. Paste Input
raw_input = st.text_area("Paste your bulk filenames here:", height=250)

if st.button("🔍 Cross-Reference & Preview"):
    if not dbx_token:
        st.error("Missing Token!")
    else:
        dbx = dropbox.Dropbox(dbx_token)
        
        # Step 1: Clean and split the bulk text
        clean_names = split_filenames(raw_input)
        
        # Step 2: Get everything currently in the 'Asset checker' folder
        try:
            folder_res = dbx.files_list_folder(folder_path)
            # Create a dictionary of {lowercase_name: full_path} for easy lookup
            actual_files = {entry.name.lower(): entry.path_display for entry in folder_res.entries}
            
            results = []
            for name in clean_names:
                match_path = actual_files.get(name.lower())
                preview_url = get_direct_link(dbx, match_path) if match_path else None
                
                results.append({
                    "Filename": name,
                    "In Dropbox": "✅ Yes" if match_path else "❌ No",
                    "Preview_URL": preview_url
                })

            # Step 3: Display results with Previews
            for item in results:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**{item['Filename']}**")
                    st.write(f"Status: {item['In Dropbox']}")
                
                with col2:
                    if item['Preview_URL']:
                        ext = item['Filename'].lower()
                        if any(x in ext for x in ['.mp4', '.mov']):
                            st.video(item['Preview_URL'])
                        else:
                            st.image(item['Preview_URL'], width=200)
                    else:
                        st.caption("No preview available")
                st.divider()
                
        except Exception as e:
            st.error(f"Dropbox Error: {e}")
