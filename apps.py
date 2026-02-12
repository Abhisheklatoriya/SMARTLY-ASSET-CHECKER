import streamlit as st
import dropbox
import hmac
import pandas as pd

# --- 1. ACCESS CONTROL (Secrets) ---
def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["APP_PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 Private Asset Checker")
    st.text_input("App Password", type="password", on_change=password_entered, key="password")
    return False

if not check_password(): st.stop()

# --- 2. DROPBOX LOGIC ---
def get_dropbox_preview(dbx, file_path):
    """Generates a temporary link to preview/display the file."""
    try:
        # Get a direct link for image/video rendering
        link_res = dbx.files_get_temporary_link(file_path)
        return link_res.link
    except:
        return None

def scan_dropbox_folder(token, folder_path):
    dbx = dropbox.Dropbox(token)
    try:
        # List files in the "Asset checker" folder
        res = dbx.files_list_folder(folder_path)
        # Create a dictionary of {filename: full_path}
        return {entry.name: entry.path_display for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)}
    except Exception as e:
        st.error(f"Error accessing Dropbox: {e}")
        return {}

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Dropbox Asset Checker", layout="wide")
st.title("📂 Dropbox Asset Naming Validator")

with st.sidebar:
    st.header("Setup")
    # You can also move this to st.secrets for better security
    dbx_token = st.secrets.get("DROPBOX_TOKEN", st.text_input("Dropbox Token", type="password"))
    folder_path = "/Asset checker"
    st.info(f"Checking Folder: `{folder_path}`")

# Step 1: Input Naming Conventions
st.subheader("1. Paste your Naming Conventions")
raw_input = st.text_area("One filename per line (e.g., PROMO_1080x1080_EN.mp4)", height=200)

if st.button("🔍 Check Dropbox"):
    if not dbx_token:
        st.error("Please provide a Dropbox Token.")
    elif not raw_input:
        st.warning("Please paste your filenames first.")
    else:
        # Step 2: Get actual files from Dropbox
        with st.spinner("Fetching data from Dropbox..."):
            actual_files = scan_dropbox_folder(dbx_token, folder_path)
        
        # Step 3: Compare
        expected_files = [line.strip() for line in raw_input.split('\n') if line.strip()]
        results = []
        
        dbx = dropbox.Dropbox(dbx_token)
        
        for name in expected_files:
            if name in actual_files:
                path = actual_files[name]
                preview_url = get_dropbox_preview(dbx, path)
                results.append({"Filename": name, "Status": "✅ Found", "Path": path, "Preview": preview_url})
            else:
                results.append({"Filename": name, "Status": "❌ Missing", "Path": None, "Preview": None})

        # Step 4: Display Results
        df = pd.DataFrame(results)
        
        for _, row in df.iterrows():
            with st.expander(f"{row['Status']} | {row['Filename']}"):
                if row['Status'] == "✅ Found":
                    st.success(f"File exists at: `{row['Path']}`")
                    if row['Preview']:
                        # Display Image or Video based on extension
                        ext = row['Filename'].lower().split('.')[-1]
                        if ext in ['png', 'jpg', 'jpeg', 'gif']:
                            st.image(row['Preview'], width=400)
                        elif ext in ['mp4', 'mov']:
                            st.video(row['Preview'])
                        else:
                            st.write("[Preview not supported for this file type]")
                else:
                    st.error("This file was not found in the 'Asset checker' folder. Please check for typos or underscores.")

        st.download_button("Download Audit Report", df.to_csv(index=False), "dropbox_audit.csv")
