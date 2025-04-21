"""
Primary Goals:
    1. OS-Agnostic
    2. Fetch ENV Vars
    3. Download repos if missing
    4. Deploy inital docker containers
    5. Deploy supabase container via supabase-cli
"""

import re
import os, shutil, subprocess, sys, time
from pathlib import Path

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
    "supabase": "../supabase",
    "blockchain": "../blockchain-local-setup",
    "cred-server": "../credential-issuer",
    "connector": "../connector",
    "grafana": "../grafana"}
public_repos = {
    # "supabase": "../supabase",
    # "blockchain": "../blockchain-local-setup",
    "cred-server": "../credential-issuer",
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
        try:
            for repo in repos:
                subprocess.run(["git", "clone", f"https://github.com/blackgateproject/f{repo}.git"], check=True) 
                print(f"Cloned {repo_name} repository.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {repo_name} repository: {e}")
            sys.exit(1)
    else:
        repo_available += 1
        # print(f"{repo_name} repository already exists. Pulling latest changes...")
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

# Call docker-compose with ENV_FILE and DEPLOY_VAR
try:
    subprocess.run(["docker","compose", "--env-file", str(env_file), "up", "-d"], check=True)
    print(f"Started Docker containers successfully.")
    print(f"Please view logs in Docker Desktop or docker ps...")
except subprocess.CalledProcessError as e:
    print(f"Error starting Docker containers: {e}")
    sys.exit(1)
