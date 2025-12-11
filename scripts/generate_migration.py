import sys
import os
import subprocess
from datetime import datetime

def generate_migration():
    if len(sys.argv) != 2:
        print("Usage: python generate_migration.py 'migration message'")
        sys.exit(1)

    folder_path = "./alembic/versions"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' was created.")
    else:
        print(f"Folder '{folder_path}' already exists.")

    message = sys.argv[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_name = f"{timestamp}_{message.lower().replace(' ', '_')}"

    try:
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", message], check=True)
        print(f"Successfully generated migration: {migration_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_migration()