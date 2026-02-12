import streamlit as st
import pandas as pd
import dropbox
import hmac

# --- 1. ACCESS CONTROL ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["APP_PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 Asset Checker")
    st.text_input("App Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password(): st.stop()

# --- 2. DROPBOX PREVIEW LOGIC ---
def get_preview_link(dbx, path):
    try:
        # Generate direct raw link for st.video/st.image
        return dbx.files_get_temporary_link(path).link
    except: return None

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Asset sync", layout="wide")
st.title("📂 Table-Based Dropbox Validator")

with st.sidebar:
    st.header("Settings")
    dbx_token = st.secrets.get("DROPBOX_TOKEN", st.text_input("Dropbox Token", type="password"))
    folder_path = "/Asset checker"

# Step 1: Initialize an empty table
if "df_input" not in st.session_state:
    st.session_state.df_input = pd.DataFrame([{"Expected Filename": ""}] * 10)

st.subheader("1. Paste Filenames into the Table")
st.info("💡 You can copy-paste multiple rows from Excel/Sheets directly into the 'Expected Filename' column.")

# Step 2: Editable Table Input
edited_df = st.data_editor(
    st.session_state.df_input,
    num_rows="dynamic",
    use_container_width=True,
    column_config={"Expected Filename": st.column_config.TextColumn(width="large")}
)

if st.button("🔍 Check Dropbox & Generate Previews"):
    if not dbx_token:
        st.error("Missing Dropbox Token!")
    else:
        dbx = dropbox.Dropbox(dbx_token)
        try:
            # Get current folder state
            files_res = dbx.files_list_folder(folder_path)
            # Create a lookup map (lower-case name -> real path) to solve matching issues
            actual_files = {entry.name.lower(): entry.path_display for entry in files_res.entries}
            
            # Extract names from table (ignore empty rows)
            names_to_check = [row["Expected Filename"].strip() for _, row in edited_df.iterrows() if row["Expected Filename"].strip()]
            
            if not names_to_check:
                st.warning("The table is empty. Please enter or paste some filenames.")
            else:
                for name in names_to_check:
                    # Match ignoring case to prevent "Nothing Matching" errors
                    match_path = actual_files.get(name.lower())
                    preview_url = get_preview_link(dbx, match_path) if match_path else None
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        status = "✅ Found" if match_path else "❌ Missing"
                        st.write(f"### {status}")
                        st.code(name)
                        if match_path:
                            st.caption(f"Path: {match_path}")
                    
                    with col2:
                        if preview_url:
                            # Detect media type
                            if any(ext in name.lower() for ext in [".mp4", ".mov"]):
                                st.video(preview_url)
                            else:
                                st.image(preview_url, width=350)
                        else:
                            st.warning("Preview unavailable (File not found in Dropbox)")
                    st.divider()
                    
        except Exception as e:
            st.error(f"Dropbox Error: {e}")
