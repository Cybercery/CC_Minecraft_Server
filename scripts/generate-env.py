import os
import shutil
import secrets
import stat

if os.path.exists(".env"):
    print(".env already exists. Aborting.")
    exit(1)

print("Generating .env from .env.example...")
shutil.copy(".env.example", ".env")

with open(".env", "r") as f:
    content = f.read()

rand_rcon = secrets.token_urlsafe(12)
rand_api = secrets.token_urlsafe(24)
rand_hmac = secrets.token_urlsafe(32)

content = content.replace("RCON_PASSWORD=", f"RCON_PASSWORD={rand_rcon}")
content = content.replace("PLUGIN_API_KEY=", f"PLUGIN_API_KEY={rand_api}")
content = content.replace("CODE_HMAC_SECRET=", f"CODE_HMAC_SECRET={rand_hmac}")

# Try to find docker GID - not as easy on Windows, but default to 10001 or 0
docker_gid = "10001"
try:
    if os.path.exists("/var/run/docker.sock"):
        docker_gid = str(os.stat("/var/run/docker.sock").st_gid)
except Exception:
    pass

content = content.replace("DOCKER_GID=999", f"DOCKER_GID={docker_gid}")

with open(".env", "w") as f:
    f.write(content)

print(f"Set DOCKER_GID to {docker_gid}")
print(".env created successfully.")
