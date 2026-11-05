# SmallOrg VPN Manager – Mini Project Report Draft

## Abstract
Small organisations may not have dedicated network-security teams, yet employees still need secure access to internal resources while working remotely. This project presents a lightweight VPN peer-management dashboard built with Flask and SQLite, designed around the WireGuard VPN protocol. An administrator can register employee devices, allocate tunnel IP addresses, generate client configuration files, and export server-side peer entries. The prototype demonstrates key-based VPN authentication and centralised peer administration. Live VPN routing is handled by a separately configured WireGuard server.

## Problem statement
Small organisations need an affordable and manageable method for enabling secure remote access without maintaining a complex enterprise VPN management platform.

## Objectives
- Demonstrate secure remote-access VPN concepts using WireGuard.
- Provide a simple administrator interface for peer management.
- Allocate unique VPN client addresses from a configurable subnet.
- Generate client and server configuration snippets.
- Store peer metadata in a lightweight SQLite database.

## Modules
1. Admin authentication – protects access to the management dashboard.
2. Peer registration – captures device/user details and generates a WireGuard key pair.
3. IP allocation – assigns an unused address from the configured VPN network.
4. Client configuration generator – creates a client `.conf` file.
5. Server peer exporter – exports the public-key entry to add on the WireGuard server.
6. Peer removal – removes the record from the local manager.

## Testing checklist
- Admin login accepts valid credentials and rejects invalid credentials.
- A new peer is assigned a unique address.
- Client config contains interface and peer sections.
- Server snippet contains the peer public key and assigned address.
- Deleting a peer removes it from the dashboard.
- Health endpoint returns service status.

## Expected outcome
A working local dashboard that demonstrates the administration workflow for a small-organisation WireGuard VPN. A separately configured WireGuard server and firewall are required for actual encrypted network connectivity.

## Future enhancements
- HTTPS and CSRF protection.
- Multi-admin roles and audit logs.
- Automated WireGuard server provisioning.
- Peer expiry, disable/enable, and usage monitoring.
- Multi-factor authentication and secure secrets storage.
