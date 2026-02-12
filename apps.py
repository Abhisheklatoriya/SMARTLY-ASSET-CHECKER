import streamlit as st
import pandas as pd
import dropbox
import hmac
import re

# --- 1. SECURITY ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["APP_PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 Asset Checker Login")
    st.text_input("App Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password(): st.stop()

# --- 2. THE MATCHING ENGINE ---
def get_preview_link(dbx, path):
    try:
        # Generates a direct raw link for the video/image player
        return dbx.files_get_temporary_link(path).link
    except: return None

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Asset sync", layout="wide")
st.title("📂 3-Column Asset Sync & Preview")

# Auto-fetch from Secrets
try:
    DBX_TOKEN = st.secrets["DROPBOX_TOKEN"]
    FOLDER_PATH = "/Asset checker"
except:
    st.error("Missing DROPBOX_TOKEN in Secrets!")
    st.stop()

# Initialize 3-column table
if "df_input" not in st.session_state:
    st.session_state.df_input = pd.DataFrame(
        [{"Campaign": "", "Language": "", "Filename": ""}] * 10
    )

st.subheader("1. Paste your data below")
st.caption("Paste 3 columns from Excel (Campaign | Language | Filename)")

# Editable Table
edited_df = st.data_editor(
    st.session_state.df_input,
    num_rows="dynamic",
    use_container_width=True
)

if st.button("🔍 Run Audit"):
    dbx = dropbox.Dropbox(DBX_TOKEN)
    try:
        # Build lookup map: normalize keys by stripping spaces and lowercasing
        files_res = dbx.files_list_folder(FOLDER_PATH)
        actual_files = {entry.name.lower().strip(): entry.path_display for entry in files_res.entries}
        
        for index, row in edited_df.iterrows():
            # STRIP ALL HIDDEN SPACES from your pasted text
            filename = str(row["Filename"]).strip()
            if not filename: continue
            
            # Match using the normalized key
            match_path = actual_files.get(filename.lower())
            preview_url = get_preview_link(dbx, match_path) if match_path else None
            
            col1, col2, col3 = st.columns([1, 2, 2])
            with col1:
                if match_path: st.success("✅ FOUND")
                else: st.error("❌ MISSING")
            
            with col2:
                st.markdown(f"**{row['Campaign']}**")
                st.code(filename) # Displays exactly what was pasted
            
            with col3:
                if preview_url:
                    if ".mp4" in filename.lower() or ".mov" in filename.lower():
                        st.video(preview_url)
                    else:
                        st.image(preview_url, use_container_width=True)
                else:
                    st.info("No Preview: Check for hidden spaces or typos")
            st.divider()
                
    except Exception as e:
        st.error(f"Dropbox Error: {e}. Your token might be expired.")
