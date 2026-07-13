# ingestion/upload_to_volume.py
import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

# Find workspace root relative to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Load environment variables before instantiating WorkspaceClient
load_dotenv(os.path.join(ROOT_DIR, ".env"))

w = WorkspaceClient()  # reads DATABRICKS_HOST / DATABRICKS_TOKEN from env
VOLUME_PATH = os.getenv("DATABRICKS_VOLUME_PATH")

def upload_dir(local_dir, remote_subdir):
    if not os.path.exists(local_dir):
        print(f"[WARN] Local directory {local_dir} does not exist. Skipping upload.")
        return

    for fname in os.listdir(local_dir):
        local_path = os.path.join(local_dir, fname)
        remote_path = f"{VOLUME_PATH}/{remote_subdir}/{fname}"
        with open(local_path, "rb") as f:
            w.files.upload(remote_path, f, overwrite=True)
        print(f"Uploaded {local_path} -> {remote_path}")

if __name__ == "__main__":
    upload_dir(os.path.join(ROOT_DIR, "landing_data/prices"), "prices")
    upload_dir(os.path.join(ROOT_DIR, "landing_data/news"), "news")