import streamlit as st
import dropbox
import re

# --- LOGIC: CLEAN BULK SPLITTING ---
def get_clean_list(text):
    # This finds everything ending in .mp4 and separates it from the next year "2026"
    pattern = r'(.*?\.mp4|.*?\.png|.*?\.jpg)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [m.strip() for m in matches]

# --- LOGIC: FETCH PREVIEW ---
def get_preview(dbx, filename, actual_files_map):
    # Normalize the pasted name to find it in the Dropbox map
    clean_name = filename.strip()
    path = actual_files_map.get(clean_name)
    
    if path:
        try:
            # Generate the direct video/image stream link
            link_metadata = dbx.files_get_temporary_link(path)
            return link_metadata.link
        except:
            return None
    return None

# --- UI ---
st.title("📂 Asset Preview Checker")

with st.sidebar:
    dbx_token = st.text_input("Dropbox Token", type="password")
    folder_path = "/Asset checker"

raw_input = st.text_area("Bulk Paste Filenames:", height=200)

if st.button("Generate Previews"):
    if not dbx_token:
        st.error("Enter your token.")
    else:
        dbx = dropbox.Dropbox(dbx_token)
        try:
            # 1. Get all files in Dropbox first to build a lookup map
            files_res = dbx.files_list_folder(folder_path)
            # Map filenames to their Dropbox paths
            actual_files = {entry.name: entry.path_display for entry in files_res.entries}
            
            # 2. Split the bulk input
            names_to_check = get_clean_list(raw_input)
            
            # 3. Display
            for name in names_to_check:
                preview_url = get_preview(dbx, name, actual_files)
                
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.write(f"**File:** {name}")
                    st.write("Status: ✅ Found" if preview_url else "❌ Not Found")
                
                with col2:
                    if preview_url:
                        if name.lower().endswith(('.mp4', '.mov')):
                            st.video(preview_url)
                        else:
                            st.image(preview_url)
                    else:
                        st.info("No preview available - Check for typos in Dropbox")
                st.divider()
        except Exception as e:
            st.error(f"Error: {e}")
