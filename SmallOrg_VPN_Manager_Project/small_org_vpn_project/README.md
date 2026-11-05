# SmallOrg VPN Manager

A Network Security mini-project for demonstrating how a small organisation can manage secure remote access using **WireGuard VPN**.

## Project overview

Small businesses often need employees to securely access internal resources while working remotely. This project provides a lightweight web-based administration dashboard to create and manage WireGuard client profiles.

### Features
- Admin login for the management dashboard.
- Add employee/device VPN peers.
- Automatically allocate client IP addresses from a configurable VPN subnet.
- Generate WireGuard client `.conf` files.
- Download the server-side `[Peer]` entry for each client.
- Remove peers from the manager.
- SQLite database for peer records.
- Docker support for a repeatable local deployment.

## Architecture

```text
Remote employee device
        |
        | WireGuard encrypted tunnel
        v
Public Internet ----> WireGuard VPN Server ----> Private organisation network
                              ^
                              |
                    SmallOrg VPN Manager
                    (Flask + SQLite)
                              |
                    Admin / IT coordinator
```

The web dashboard is the **management prototype**. It generates configuration material but does not automatically provision a live WireGuard server or configure firewalls.

## Technology stack

- Python 3
- Flask
- SQLite
- WireGuard configuration format
- X25519 key generation (`cryptography`)
- HTML, CSS
- Docker (optional)

## Run locally (Windows / macOS / Linux)

1. Install Python 3.10 or newer.
2. Extract the ZIP and open the project folder in VS Code.
3. Create a virtual environment:

   Windows PowerShell:
   ```powershell
   py -m venv .venv
   .venv\\Scripts\\Activate.ps1
   ```

   macOS / Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env`. Set a strong `FLASK_SECRET_KEY`, `ADMIN_PASSWORD`, your VPN endpoint, and your WireGuard server public key. The app reads environment variables; for a simple local demo you can set them in the terminal before starting Flask. For production, use a proper environment loader or platform secrets manager.
6. Start the app:
   ```bash
   python app.py
   ```
7. Open `http://127.0.0.1:5000`.

### Demo login

- Username: `admin`
- Password: `ChangeMe123!`

Change these values before any deployment. The defaults are only for a local classroom demonstration.

## Docker run

1. Copy `.env.example` to `.env` and update the values.
2. Run:
   ```bash
   docker compose up --build
   ```
3. Open `http://localhost:5000`.

## Configure a real WireGuard server (high-level)

This is a lab/mini-project guide, not an automatic production deployment.

1. Set up a supported Linux server with WireGuard installed.
2. Generate a server key pair on that server using `wg genkey` and `wg pubkey`. Keep the server private key secret.
3. Configure the server interface with a private tunnel address (for example `10.8.0.1/24`), UDP listen port `51820`, and appropriate firewall/NAT rules.
4. Set `SERVER_PUBLIC_KEY` to the server public key and `VPN_ENDPOINT` to the server's public IP or DNS name plus port.
5. In the dashboard, add a peer. Download both its client configuration and server peer entry.
6. Add the server peer entry to the server's WireGuard configuration and apply it using the WireGuard service tools.
7. Import the client `.conf` into the official WireGuard client on the employee device.
8. Test connectivity and access only to the internal subnets that the organisation intends to expose.

**Important:** A generated client configuration contains a private key. Treat it like a password: distribute it securely, do not email it in plain text, and never commit it to GitHub. The database stores client private keys so the dashboard can regenerate configurations; protect the database and host accordingly.

## Suggested demo flow

1. Sign in to the admin dashboard.
2. Add a sample employee called `Accounts-Laptop`.
3. Show the automatically assigned VPN address.
4. Download the client config and server peer entry.
5. Explain how WireGuard uses public/private keys to authenticate peers and encrypt tunnel traffic.
6. Remove the sample peer and explain that the matching live server entry must also be removed.

## Security considerations / limitations

- This is an educational management prototype, not a hardened enterprise VPN control plane.
- Use HTTPS behind a trusted reverse proxy before exposing the dashboard.
- Change demo credentials and use a long random Flask secret.
- Add CSRF protection, rate limiting, audit logging, role-based access control, backup/restore, and secure key storage before production use.
- Restrict `AllowedIPs` to the minimum required network ranges. Avoid `0.0.0.0/0` unless full-tunnel routing is deliberately intended.
- The dashboard's delete action removes the database record only. Remove the corresponding peer from the live WireGuard server too.
- Do not commit `.env`, database files, generated configs, or private keys to source control.

## GitHub upload

From the project folder:

```bash
git init
git add .
git commit -m "Initial commit - SmallOrg VPN Manager"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/smallorg-vpn-manager.git
git push -u origin main
```

Check `git status` before pushing. Confirm `.env`, `vpn_manager.db`, and generated `.conf` files are not staged.

## Mini-project report outline

1. Abstract
2. Introduction and problem statement
3. Existing system and proposed system
4. Objectives
5. System architecture
6. Software and hardware requirements
7. Module description
8. Implementation screenshots
9. Testing and results
10. Advantages, limitations and future enhancements
11. Conclusion
12. References

## References

- WireGuard: https://www.wireguard.com/
- WireGuard Quick Start: https://www.wireguard.com/quickstart/
- Flask documentation: https://flask.palletsprojects.com/
