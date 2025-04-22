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
from dotenv import load_dotenv, set_key, dotenv_values

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
    "SUPABASE_JWT_ALGORITHM",
    "SUPABASE_JWT_EXPIRES", 
    "SUPABASE_AUTH_ANON_KEY", 
    "SUPABASE_AUTH_SERV_KEY", 
    "SUPABASE_AUTH_JWT_SECRET",
    "BLOCKCHAIN_RPC_URL", 
    "BLOCKCHAIN_CHAIN_ID", 
    "BLOCKCHAIN_DID_REGISTRY_ADDR",
    "BLOCKCHAIN_MERKLE_ADDR", 
    "CRED_SERVER_URL"]

default_envs = {
    "SUPABASE_JWT_ALGORITHM": "HS256",
    "SUPABASE_JWT_EXPIRES": "3600",
    "SUPABASE_URL": "http://localhost:54321" if deploy_mode == "local" else "",
    "BLOCKCHAIN_CHAIN_ID": "270" if deploy_mode == "local" else "300",
    "BLOCKCHAIN_RPC_URL": "http://localhost:10005" if deploy_mode == "local" else "",
    "BLOCKCHAIN_WALLET_PRVT_KEY": (
        "0x7726827caac94a7f9e1b160f7ea819f172f7b6f9d2a97f992c38edeab82d4110"
        if deploy_mode == "local"
        else ""
    ),
    "BLOCKCHAIN_WALLET_ADDR": (
        "0x36615Cf349d7F6344891B1e7CA7C72883F5dc049" if deploy_mode == "local" else ""
    ),
    "ZKSYNC_NODE_TYPE": (
        "dockerizedNode" if deploy_mode == "local" else "zkSyncSepoliaTestnet"
    ),
    "CRED_SERVER_URL": "http://localhost:10002" if deploy_mode == "local" else "",
    "DEBUG": "8" if deploy_mode == "local" else "",
}


# Check if the env file exists
if not env_file.is_file():
    print(f"WARN: {env_file} does not exist. Please create it before running this script.")
    create_file = input(f"Do you want to create {env_file}? (y/n): ").strip().lower()
    if create_file == "y":
        with open(env_file, "w") as f:
            f.write("# Autogen variables\n")
        
        # Set initial values using dotenv
        set_key(str(env_file), "DEPLOY_ENV", deploy_mode)
        set_key(str(env_file), "ENV_FILE", str(env_file))
        
        # Create empty entries for the remaining variables
        for env in envs:
            if env not in ["DEPLOY_ENV", "ENV_FILE"]:
                set_key(str(env_file), env, "")
        
        # Update default env vars
        for env in default_envs:
            set_key(str(env_file), env, default_envs[env])

        print(f"Created {env_file}. Populating with default env vars.")
        # sys.exit(1)
    else:
        print("Exiting script.")
        sys.exit(1)
else:
    # Check if all required environment variables are set
    env_values = dotenv_values(str(env_file))
    missing_vars = []

    # Update default env vars
    for env in default_envs:
        if env not in env_values or not env_values[env]:
            set_key(str(env_file), env, default_envs[env])
            # print(f"Set default value for {env} in {env_file}.")

    for env in envs:
        if env not in env_values or not env_values[env]:
            print(f"WARN: {env} is not set in {env_file}. Please set it.")
            missing_vars.append(env)
    
    if missing_vars:
        print(f"\nMissing {len(missing_vars)} environment variables.")
    else:
        print("\nAll required environment variables are set.")

# Load environment variables from the file (for display only)
env_values = dotenv_values(str(env_file))
print(f"Loaded {len(env_values)} environment variables from {env_file}.")

print(f"\n{'*' * 50}")
print(f"\tChecking if repos are available")
print(f"{'*' * 50}\n")
# Check for repos if they exist
local_repos = {
    "supabase-cli": "../supabase-cli",
    "blockchain-contracts": "../blockchain-contracts",
    "blockchain-local-setup": "../blockchain-local-setup",
    "credential-issuer": "../credential-issuer",
    "connector": "../connector",
    "frontend": "../frontend",
    "grafana": "../grafana"}
public_repos = {
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
        try:
            subprocess.run(["git", "clone", f"https://github.com/blackgateproject/{repo_name}.git", str(repo_path)], check=True)
            print(f"Cloned {repo_name} repository.")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning {repo_name} repository: {e}")
            sys.exit(1)
    else:
        # print(f"{repo_name} repository already exists. Pulling latest changes...")
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
print(f"\tStarting Supabase Deployment")
print(f"{'*' * 50}\n")

# Check if docker is running
try:
    subprocess.run(["docker", "info"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except subprocess.CalledProcessError as e:
    print("Docker is not running. Please start Docker and try again.")
    sys.exit(1)

# Check if JWT secret is set in the env file
env_values = dotenv_values(str(env_file))
if not env_values.get("SUPABASE_AUTH_JWT_SECRET"):
    print(f"WARN: SUPABASE_AUTH_JWT_SECRET is not set. Generating a new one.")

    # Generate a JWT secret. 40 chars random capitalization
    jwt_secret = os.urandom(40).hex()
    jwt_secret = base64_encode(jwt_secret.encode())[0].decode("utf-8")
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

    # Update the env file directly
    # set_key(str(env_file), "SUPABASE_AUTH_JWT_SECRET", f"\"{jwt_secret}\"")
    # set_key(str(env_file), "SUPABASE_AUTH_ANON_KEY", f"\"{anon_key}\"")
    # set_key(str(env_file), "SUPABASE_AUTH_SERV_KEY", f"\"{serv_key}\"")

    set_key(
        str(env_file),
        "SUPABASE_AUTH_JWT_SECRET",
        f"super-secret-jwt-token-with-at-least-32-characters-long",
    )
    set_key(
        str(env_file),
        "SUPABASE_AUTH_ANON_KEY",
        f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
    )
    set_key(
        str(env_file),
        "SUPABASE_AUTH_SERV_KEY",
        f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
    )

    # print(f"Updated {env_file} with new JWT secret and keys.")
    print(f"WARN:: Using default JWT secret and keys. Please update them in {env_file}")

if deploy_mode == "local":
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

    print(f"\n{'*' * 50}")
    print(f"\tStarting Blockchain Deployment")
    print(f"{'*' * 50}\n")
    # Start zksync node first
    try:
        subprocess.run(["docker", "compose", "--env-file", str(env_file),"--profile","blockchain","up",  "-d"], check=True)
        # wait for zksync to be healthy, run docker compose --env-file .env.local ps zksync until the log says (healthy)
        print(f"Waiting for zksync node to be healthy...")
        while True:
            try:
                result = subprocess.run(
                    ["docker", "compose", "--env-file", str(env_file), "ps", "zksync"],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                # print(result.stdout if result.stdout else "No stdout output")
                # print(result.stderr if result.stderr else "No stderr output")
                if "(healthy)" in result.stdout:
                    print(f"ZkSync node is healthy.")
                    break
                else:
                    print(f"ZkSync node is not healthy yet. Waiting...")
                    time.sleep(10)
            except subprocess.CalledProcessError as e:
                print(f"Error starting ZkSync node: {e}")
                print(e.stdout)
                print(e.stderr)
                sys.exit(1)

        # Compile & Deploy contracts (cd ../blockchain-contracts; npm run compile; npm run deploy-local)
        try:
            print(f"Compiling contracts...")
            subprocess.run(["npm", "run", "compile"], cwd="../blockchain-contracts", check=True, shell=True, text=True)
            print(f"Compiled contracts successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error compiling contracts: {e}")
            sys.exit(1)
        try:
            print(f"Deploying contracts...")
            # Set os env var WALLET_PRIVATE_KEY to BLOCKCHAIN_WALLET_PRVT_KEY
            os.environ["WALLET_PRIVATE_KEY"] = env_values["BLOCKCHAIN_WALLET_PRVT_KEY"]
            # run process with env var and capture output
            result = subprocess.run(["npm", "run", "deploy-local"], cwd="../blockchain-contracts", check=True, shell=True, text=True, capture_output=True)
            print(f"Deployed contracts successfully.")

            # Extract contract addresses from output
            output = result.stdout
            # print(f"Deployment output: {output}")
            merkle_match = re.search(r'"Merkle" was successfully deployed:[\s\S]*?Contract address: (0x[a-fA-F0-9]{40})', output)
            did_match = re.search(r'"EthereumDIDRegistry" was successfully deployed:[\s\S]*?Contract address: (0x[a-fA-F0-9]{40})', output)

            merkle_address = merkle_match.group(1) if merkle_match else None
            did_address = did_match.group(1) if did_match else None

            if merkle_address and did_address:
                print(f"Extracted Merkle contract address: {merkle_address}")
                print(f"Extracted DID Registry address: {did_address}")

                # Update the env file with the contract addresses
                set_key(str(env_file), "BLOCKCHAIN_MERKLE_ADDR", merkle_address)
                set_key(str(env_file), "BLOCKCHAIN_DID_REGISTRY_ADDR", did_address)
                print(f"Updated {env_file} with contract addresses.")
            else:
                print("Warning: Could not extract one or both contract addresses from deployment output.")
        except subprocess.CalledProcessError as e:
            print(f"Error deploying contracts: {e}")
            sys.exit(1)

        print(f"Blockchain deployment completed successfully.")
        print(f"Please view logs in Docker Desktop or docker ps...")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Supabase Docker containers: {e}")
        sys.exit(1)

print(f"\n{'*' * 50}")
print(f"\tStarting Remaining Services Deployment")
print(f"{'*' * 50}\n")

# Start supabase docker-compose.yml i.e. other services
try:
    subprocess.run(["docker", "compose", "--env-file", str(env_file),"--profile","deploy","up",  "-d"], check=True)
    print(f"Started Supabase Docker containers successfully.")
    print(f"Please view logs in Docker Desktop or docker ps...")
except subprocess.CalledProcessError as e:
    print(f"Error starting Supabase Docker containers: {e}")
    sys.exit(1)
