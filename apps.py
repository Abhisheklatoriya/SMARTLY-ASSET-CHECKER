import streamlit as st
import pandas as pd
import dropbox
import hmac
import re

# --- 1. SECURITY (Password Gate) ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["APP_PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True
    st.title("🔒 Asset Preview Checker")
    st.text_input("App Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# --- 2. DROPBOX API LOGIC ---
def get_preview_link(dbx, path):
    """Generates a direct temporary link for st.video/st.image."""
    try:
        # This bypasses the Dropbox UI to get the raw media stream
        return dbx.files_get_temporary_link(path).link
    except Exception:
        return None

def fetch_dropbox_files(token, folder_path):
    """Builds a map of all files in the folder for fast lookup."""
    dbx = dropbox.Dropbox(token)
    try:
        res = dbx.files_list_folder(folder_path)
        # We store keys in lowercase and strip spaces to maximize match probability
        return {entry.name.lower().strip(): entry.path_display for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}
    except Exception as e:
        st.error(f"Dropbox Connection Error: {e}")
        return {}

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Asset sync", layout="wide")
st.title("📂 3-Column Asset Sync & Preview")

# Pull credentials from Streamlit Secrets
try:
    DBX_TOKEN = st.secrets["DROPBOX_TOKEN"]
    FOLDER_PATH = "/Asset checker"
except Exception:
    st.error("Missing 'DROPBOX_TOKEN' in Secrets! Please add it to your .streamlit/secrets.toml or Cloud Dashboard.")
    st.stop()

# Initialize the 3-column table state
if "df_input" not in st.session_state:
    st.session_state.df_input = pd.DataFrame(
        [{"Campaign": "", "Language": "", "Filename": ""}] * 10
    )

st.subheader("1. Paste your data")
st.caption("Paste 3 columns from Excel (Campaign | Language | Filename). Each file must be in its own row.")

# Editable Table
edited_df = st.data_editor(
    st.session_state.df_input,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Campaign": st.column_config.TextColumn(width="medium"),
        "Language": st.column_config.TextColumn(width="small"),
        "Filename": st.column_config.TextColumn(width="large", help="Paste the exact filename here"),
    }
)

if st.button("🔍 Run Audit & Generate Previews"):
    dbx = dropbox.Dropbox(DBX_TOKEN)
    
    with st.spinner("Scanning Dropbox folder..."):
        # Map filenames to paths to solve the 'Nothing Matching' issue
        actual_files_map = fetch_dropbox_files(DBX_TOKEN, FOLDER_PATH)
    
    if not actual_files_map:
        st.warning("No files found in Dropbox folder. Check the folder name or token permissions.")
    else:
        st.divider()
        found_count = 0
        total_rows = 0
        
        # Iterate through the table entries
        for index, row in edited_df.iterrows():
            # Clean up the pasted filename
            raw_filename = str(row["Filename"]).strip()
            if not raw_filename:
                continue
            
            total_rows += 1
            # Normalize for matching
            lookup_key = raw_filename.lower()
            match_path = actual_files_map.get(lookup_key)
            
            # Generate the specific preview link for this file
            preview_url = get_preview_link(dbx, match_path) if match_path else None
            
            # Create a display row
            col1, col2, col3 = st.columns([1, 3, 3])
            
            with col1:
                if preview_url:
                    st.success("✅ FOUND")
                    found_count += 1
                else:
                    st.error("❌ MISSING")
            
            with col2:
                st.markdown(f"**Campaign:** {row['Campaign']}")
                st.markdown(f"**Lang:** {row['Language']}")
                st.code(raw_filename)
                if match_path:
                    st.caption(f"Dropbox Path: {match_path}")

            with col3:
                if preview_url:
                    # Determine if it's a video or image based on extension
                    ext = raw_filename.lower()
                    if any(x in ext for x in [".mp4", ".mov"]):
                        st.video(preview_url)
                    elif any(x in ext for x in [".png", ".jpg", ".jpeg", ".gif"]):
                        st.image(preview_url, use_container_width=True)
                    else:
                        st.info("Preview not supported for this file type.")
                else:
                    st.warning("No Preview Available: Check for typos or special characters.")
            
            st.divider()
        
        # Summary Metric
        if total_rows > 0:
            st.metric("Sync Rate", f"{(found_count/total_rows)*100:.1f}%", f"{found_count} of {total_rows} found")
