import streamlit as st
import pandas as pd
import dropbox
import hmac

# --- 1. ACCESS CONTROL (Hidden Secrets) ---
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

# --- 2. DROPBOX PREVIEW LOGIC ---
def get_preview_link(dbx, path):
    try:
        # Generates direct stream link for video/image
        return dbx.files_get_temporary_link(path).link
    except: return None

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Asset sync", layout="wide")
st.title("📂 3-Column Bulk Asset Validator")

# Fetch token from secrets (No UI input needed)
DBX_TOKEN = st.secrets["DROPBOX_TOKEN"]
FOLDER_PATH = "/Asset checker"

# Initialize 3-column table
if "df_input" not in st.session_state:
    st.session_state.df_input = pd.DataFrame(
        [{"Campaign": "", "Language": "", "Filename": ""}] * 15
    )

st.subheader("1. Paste your data below")
st.caption("You can paste 3 columns directly from Excel/Sheets (e.g., Campaign | Lang | Filename)")

# 3-Column Editable Table
edited_df = st.data_editor(
    st.session_state.df_input,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Campaign": st.column_config.TextColumn(width="medium"),
        "Language": st.column_config.TextColumn(width="small"),
        "Filename": st.column_config.TextColumn(width="large"),
    }
)

if st.button("🔍 Check Dropbox & Generate Previews"):
    dbx = dropbox.Dropbox(DBX_TOKEN)
    try:
        # Build lookup map of folder contents
        files_res = dbx.files_list_folder(FOLDER_PATH)
        actual_files = {entry.name.lower().strip(): entry.path_display for entry in files_res.entries}
        
        # Process entries
        for index, row in edited_df.iterrows():
            filename = str(row["Filename"]).strip()
            if not filename: continue # Skip empty rows
            
            match_path = actual_files.get(filename.lower())
            preview_url = get_preview_link(dbx, match_path) if match_path else None
            
            # Display Results in Rows
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 2])
                
                with col1:
                    if match_path:
                        st.success("✅ FOUND")
                    else:
                        st.error("❌ MISSING")
                
                with col2:
                    st.markdown(f"**{row['Campaign']}** ({row['Language']})")
                    st.code(filename)
                
                with col3:
                    if preview_url:
                        if any(ext in filename.lower() for ext in [".mp4", ".mov"]):
                            st.video(preview_url)
                        else:
                            st.image(preview_url, use_container_width=True)
                    else:
                        st.info("No Preview Available")
                st.divider()
                
    except Exception as e:
        st.error(f"Dropbox Error: {e}")
