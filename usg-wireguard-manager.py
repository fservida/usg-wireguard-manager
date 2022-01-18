import json
import subprocess
from subprocess import CalledProcessError

file_path = "config.gateway.json"
persistent_keepalive = 25
server_pubkey = "REPLACE_WITH_SERVER_PUBKEY"
server_endpoint = "hostname_or_ip:51820" # match your server hostname/ip and listening port
server_ip_ranges = "172.16.1.0/24, 172.21.0.0/16" # Comma separated server IP ranges in CIDR notation
dns_servers = "1.1.1.1, 1.0.0.1" # Comma separated DNS servers (eg. your internal DNS servers

with open(file_path, "r+") as gateway_config:
    config = json.load(gateway_config)
    peers = config.get("interfaces").get("wireguard").get("wg0").get("peer")
    print("Current Peers: ")
    for peer in peers:
        for key, peer_config in peer.items():
            print(key, peer_config)

    action = input("\nAction [add, a, delete, d]: ")
    while action not in ("add", "a", "delete", "d"):
        action = input("\nAction [add, delete]: ")
    if action in ("delete", "d"):
        pubkey = input("\nPublic Key of peer to delete: ")
        for peer in peers:
            for key, peer_config in peer.items():
                if key == pubkey:
                    print("Found peer to delete")
                    peers.pop(peers.index(peer))

    if action in ("add", "a"):
        try:
            seckey = subprocess.run("wg genkey", text=True, shell=True, check=True, capture_output=True).stdout.replace("\n", "")
            pubkey = subprocess.run("wg pubkey", input=seckey, text=True, shell=True, check=True, capture_output=True).stdout.replace("\n", "")
        except CalledProcessError as exception:
            print(exception)
        interface_ip = input("Enter interface IP in CIDR format: ")
        allowed_ips = input("Enter additional allowed IPs ranges in CIDR format, comma separated: ")
        if allowed_ips:
            allowed_ips.split(",")
            allowed_ips.append(interface_ip)
        else:
            allowed_ips = [interface_ip]

        peer_config = """
        [Interface]
        PrivateKey = private_key
        Address = interface
        DNS = dns_servers

        [Peer]
        PublicKey = server_pubkey
        Endpoint = server_endpoint
        AllowedIPs = server_ip_ranges
        PersistentKeepAlive = persistent_keepalive
        """.replace("private_key", seckey).replace("interface", interface_ip).replace("dns_servers", dns_servers).replace("server_pubkey", server_pubkey).replace("server_endpoint", server_endpoint).replace("server_ip_ranges", server_ip_ranges).replace("persistent_keepalive", str(persistent_keepalive))
        print(peer_config)
        qr = subprocess.run("qrencode -o - -t ansiutf8", input=peer_config, text=True, shell=True, check=True, capture_output=True).stdout
        print(qr)
        peer = { pubkey : {'allowed-ips': allowed_ips, 'persistent-keepalive': persistent_keepalive}}
        print(peer)
        peers.append(peer)

    # Save Peers
    config["interfaces"]["wireguard"]["wg0"]["peer"] = peers

with open(file_path, "w") as gateway_config:
    json.dump(config, gateway_config, indent=2)
