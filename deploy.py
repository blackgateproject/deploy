"""
Primary Goals:
    1. OS-Agnostic
    2. Fetch ENV Vars
    3. Download repos if missing
    4. Deploy inital docker containers
    5. Deploy supabase container via supabase-cli
"""

from encodings.base64_codec import base64_encode
import re
import os, shutil, subprocess, sys, time
from pathlib import Path
import jwt
print(f"\n{'*' * 50}")
print(f"\tStarting Deployment Script")
print(f"{'*' * 50}\n")


deploy_mode = input("Set a deploy mode \n1. Local \n2. Public\n\n")
print(f"Deploy mode set to: {deploy_mode}")
if deploy_mode == "1":
    deploy_mode = "local"
elif deploy_mode == "2":
    deploy_mode = "public"
else:
    print("Invalid deploy mode. Exiting.")
    sys.exit(1)

# Check if .env.local or .env.public exists
if deploy_mode == "local":
    env_file = Path(".env.local")
else:
    env_file = Path(".env.public")



print(f"\n{'*' * 50}")
print(f"\tChecking for Environment Variables")
print(f"{'*' * 50}\n")
envs = [
    "DEPLOY_ENV",
    "ENV_FILE",
    "SUPABASE_URL", 
    "SUPABASE_JWT_ALGORITHIM",
    "SUPABASE_JWT_EXPIRES", 
    "SUPABASE_AUTH_ANON_KEY", 
    "SUPABASE_AUTH_SERV_KEY", 
    "SUPABASE_AUTH_JWT_SECRET",
    "BLOCKCHAIN_RPC_URL", 
    "BLOCKCHAIN_CHAIN_ID", 
    "BLOCKCHAIN_DID_REGISTRY_ADDR",
    "BLOCKCHAIN_MERKLE_ADDR", 
    "CRED_SERVER_URL"]

# Check if the env file exists
if not env_file.is_file():
    print(f"WARN: {env_file} does not exist. Please create it before running this script.")
    # Prompt for confirmation to create the file
    create_file = "y"
    create_file = input(f"Do you want to create {env_file}? (y/n): ").strip().lower()
    if create_file == "y":
        with open(env_file, "w") as f:
            f.write("# Autogen variables\n")
            for env in envs:
                if env == "ENV_FILE" and deploy_mode == "local":
                #    f.write(f"{env}=.env.${{DEPLOY_ENV}}\n")
                    f.write(f"{env}={env_file}\n")
                elif env == "ENV_FILE" and deploy_mode == "public":
                #    f.write(f"{env}=.env.${{DEPLOY_ENV}}\n")
                    f.write(f"{env}={env_file}\n")
                elif env == "DEPLOY_ENV":
                #    f.write(f"{env}=.env.${{{deploy_mode}}}\n")
                   f.write(f"{env}={deploy_mode}\n")
                else:                
                    f.write(f"{env}=\n")
        print(f"Created {env_file}. Please add your environment variables.")
        sys.exit(1)
    else:
        print("Exiting script.")
        sys.exit(1)
else:
    # Check if all envs are set i.e. have some value
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                if key in envs and not value:
                    print(f"WARN: {key} is not set in {env_file}. Please set it.")
    print()                


# Load environment variables from the selected env file
with open(env_file) as f:
    var_count = 0
    for line in f:
        if line.strip() and not line.startswith("#"):
            key, value = line.strip().split("=", 1)
            os.environ[key] = value
            var_count += 1
    print(f"Loaded {var_count} environment variables from {env_file}.")

print(f"\n{'*' * 50}")
print(f"\tChecking if repos are available")
print(f"{'*' * 50}\n")
# Check for repos if they exist
local_repos = {
    "supabase": "../supabase-cli",
    "blockchain-local-setup": "../blockchain-local-setup",
    "credential-issuer": "../credential-issuer",
    "connector": "../connector",
    "grafana": "../grafana"}
public_repos = {
    # "supabase": "../supabase",
    # "blockchain": "../blockchain-local-setup",
    "credential-issuer": "../credential-issuer",
    "connector": "../connector",
    "grafana": "../grafana"}

if deploy_mode == "local":
    repos = local_repos
else:
    repos = public_repos

repo_available = 0
for repo_name, repo_path in repos.items():
    repo_path = Path(repo_path)
    if not repo_path.is_dir():
        print(f"Cloning {repo_name} repository...")
        # try:
        #     subprocess.run(["git", "clone", f"https://github.com/blackgateproject/{repo_name}.git", str(repo_path)], check=True)
        #     print(f"Cloned {repo_name} repository.")
        # except subprocess.CalledProcessError as e:
        #     print(f"Error cloning {repo_name} repository: {e}")
        #     sys.exit(1)
    else:
        print(f"{repo_name} repository already exists. Pulling latest changes...")
        # try:
        #     subprocess.run(["git", "-C", str(repo_path), "pull"], check=True)
        #     print(f"Pulled latest changes for {repo_name} repository.")
        # except subprocess.CalledProcessError as e:
        #     print(f"Error pulling latest changes for {repo_name} repository: {e}")
        #     sys.exit(1)
        repo_available += 1
print(f"Available Repositories: {repo_available}/{len(repos)}")
# Start deployment on docker
print(f"\n{'*' * 50}")
print(f"\tStarting Docker Deployment")
print(f"{'*' * 50}\n")

# Check if docker is running
try:
    subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except subprocess.CalledProcessError as e:
    print("Docker is not running. Please start Docker and try again.")
    sys.exit(1)

# # Call docker-compose with ENV_FILE and DEPLOY_VAR
# try:
#     subprocess.run(["docker","compose", "--env-file", str(env_file), "up", "-d"], check=True)
#     print(f"Started Docker containers successfully.")
#     print(f"Please view logs in Docker Desktop or docker ps...")
# except subprocess.CalledProcessError as e:
#     print(f"Error starting Docker containers: {e}")
#     sys.exit(1)

# Stage deployment
# Public: 
#       1. blockchain-local-setup/supabase
#           1a. generate supabase keys

# Check if SUPABASE_JWT_SECRET is set/or empty in the env file
if os.environ.get("SUPABASE_AUTH_JWT_SECRET") == "" or os.environ.get("SUPABASE_AUTH_JWT_SECRET") is None:
    print(f"WARN: SUPABASE_AUTH_JWT_SECRET is not set. Generating a new one.")
    
    # Generate a JWT secret. 40 chars random capitlization
    jwt_secret = os.urandom(40).hex()
    jwt_secret = base64_encode(jwt_secret.encode())[0].decode("utf-8")

    #strip any new lines from jwt_secret
    jwt_secret = re.sub(r'[\n\r]', '', jwt_secret)

    print(f"Generated SUPABASE_JWT_SECRET: {jwt_secret}")

    # Generate anon key based on JWT secret
    anon_key = jwt.encode(
                            {"role": "anon", 
                            "iss": "supabase", 
                            "iat": int(time.time()), 
                            "exp": int(time.time()) + 60 * 60 * 24 * 365 * 5}  # expire after 5 years
                            , jwt_secret, algorithm="HS256")
    print(f"Generated SUPABASE_AUTH_ANON_KEY: {anon_key}")

    serv_key = jwt.encode(
                            {"role": "service_role", 
                            "iss": "supabase", 
                            "iat": int(time.time()), 
                            "exp": int(time.time()) + 60 * 60 * 24 * 365 * 5}
                            , jwt_secret, algorithm="HS256")
    print(f"Generated SUPABASE_AUTH_SERV_KEY: {serv_key}")

    # Update all 3 vars to the .env file, find the lines and replace them
    # with the new values
    with open(env_file, "r") as f:
        lines = f.readlines()

    with open(env_file, "w") as f:
        for line in lines:
            if "SUPABASE_AUTH_JWT_SECRET" in line:
                line = f"SUPABASE_AUTH_JWT_SECRET=\"{jwt_secret}\"\n"
            elif "SUPABASE_AUTH_ANON_KEY" in line:
                line = f"SUPABASE_AUTH_ANON_KEY=\"{anon_key}\"\n"
            elif "SUPABASE_AUTH_SERV_KEY" in line:
                line = f"SUPABASE_AUTH_SERV_KEY=\"{serv_key}\"\n"
            elif "SUPABASE_JWT_ALGORITHIM" in line:
                line = f"SUPABASE_JWT_ALORITHM=\"HS256\"\n"
            elif "SUPABASE_JWT_EXPIRES" in line:
                line = f"SUPABASE_JWT_EXPIRES=3600\n"
            f.write(line)
    print(f"Updated {env_file} with new JWT secret and keys.")

# Start supabase
try:
    result = subprocess.run(
        ["npx", "supabase", "start"],
        cwd="..\\supabase-cli\\",
        shell=True,
        text=True
    )
    print(result.stdout if result.stdout else "No stdout output")
    print(result.stderr if result.stderr else "No stderr output")
except subprocess.CalledProcessError as e:
    print(f"Error starting Supabase CLI: {e}")
    print(e.stdout)
    print(e.stderr)
    sys.exit(1)


# Start supabase docker-compose.yml i.e. other services
try:
    # subprocess.run(["docker", "compose", "--env-file", str(env_file), "-f", "../blockchain-local-setup/docker-compose.yml", "up", "-d"], check=True)
    subprocess.run(["docker", "compose", "--env-file", str(env_file),"up", "-d"], check=True)
    print(f"Started Supabase Docker containers successfully.")
    print(f"Please view logs in Docker Desktop or docker ps...")
except subprocess.CalledProcessError as e:
    print(f"Error starting Supabase Docker containers: {e}")
    sys.exit(1)
    

