import os
import sys

def update_env(key, value):
    env_file = '.env'
    if not os.path.exists(env_file):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
        else:
            with open(env_file, 'w') as f:
                f.write('')

    with open(env_file, 'r') as f:
        lines = f.readlines()

    new_lines = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}\n")

    with open(env_file, 'w') as f:
        f.writelines(new_lines)

def main():
    print("--- Vector AI Bridge Environment Configurator ---")
    print("This script will help you set up your .env file for direct connection.")

    if len(sys.argv) > 1:
        # Simple CLI argument support for automated agents
        # Usage: python configure_env.py IP NAME SERIAL GUID CERT_PATH
        if len(sys.argv) == 6:
            update_env("VECTOR_IP", sys.argv[1])
            update_env("VECTOR_NAME", sys.argv[2])
            update_env("VECTOR_SERIAL", sys.argv[3])
            update_env("VECTOR_GUID", sys.argv[4])
            update_env("VECTOR_CERT_PATH", sys.argv[5])
            print("Successfully updated .env with provided arguments.")
            return
        else:
            print("Usage: python configure_env.py <IP> <NAME> <SERIAL> <GUID> <CERT_PATH>")
            sys.exit(1)

    # Interactive mode
    ip = input("Vector IP: ")
    name = input("Vector Name (e.g. Vector-A1B2): ")
    serial = input("Vector Serial: ")
    guid = input("Vector GUID: ")
    cert = input("Vector Cert Path: ")

    update_env("VECTOR_IP", ip)
    update_env("VECTOR_NAME", name)
    update_env("VECTOR_SERIAL", serial)
    update_env("VECTOR_GUID", guid)
    update_env("VECTOR_CERT_PATH", cert)

    print("\nSuccessfully updated .env file!")
    print("You can now run the bridge using: python src/core/vector_ollama.py")

if __name__ == "__main__":
    main()
