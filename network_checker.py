
import socket
import subprocess
import platform
import time
import ipaddress
import re


def valid_target(host):
    """Validate an IP address or a basic hostname."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    if len(host) > 253 or not host:
        return False

    # Allow standard hostname characters and an optional final dot.
    name = host[:-1] if host.endswith(".") else host
    labels = name.split(".")

    return all(
        label
        and len(label) <= 63
        and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", label)
        for label in labels
    )


def ping_host(host):
    """Check whether the target responds to ping."""
    print("\n[1] PING CHECK")

    if platform.system().lower() == "windows":
        command = ["ping", "-n", "1", "-w", "2000", host]
    else:
        command = ["ping", "-c", "1", "-W", "2", host]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"[SUCCESS] {host} responded to ping.")
            return True

        print(
            f"[FAILED] No ping response from {host}. "
            "The target may be offline or block ping."
        )
        return False

    except subprocess.TimeoutExpired:
        print("[ERROR] Ping command timed out.")
    except FileNotFoundError:
        print("[ERROR] The system ping command was not found.")
    except OSError as error:
        print(f"[ERROR] Could not run ping: {error}")

    return False


def dns_check(host):
    """Resolve the target to an IP address."""
    print("\n[2] DNS / ADDRESS CHECK")

    try:
        ip_address = socket.gethostbyname(host)
        print(f"[SUCCESS] {host} resolved to {ip_address}.")
        return ip_address

    except socket.gaierror as error:
        print(f"[FAILED] Name resolution failed: {error}")
    except OSError as error:
        print(f"[ERROR] DNS/address lookup error: {error}")

    return None


def check_tcp_port(host, port):
    """Test a TCP connection and measure connection time."""
    print(f"\n[TCP PORT CHECK: {port}]")

    start = time.perf_counter()

    try:
        with socket.create_connection((host, port), timeout=3):
            elapsed = (time.perf_counter() - start) * 1000
            print(
                f"[SUCCESS] Port {port} is reachable "
                f"({elapsed:.2f} ms)."
            )
            return True

    except ConnectionRefusedError:
        print(f"[FAILED] Port {port}: connection refused.")
    except (socket.timeout, TimeoutError):
        print(f"[FAILED] Port {port}: connection timed out.")
    except socket.gaierror as error:
        print(f"[FAILED] Port {port}: hostname resolution failed ({error}).")
    except OSError as error:
        print(f"[FAILED] Port {port}: network error ({error}).")

    return False


def main():
    print("=" * 48)
    print("       NETWORK CONNECTIVITY CHECKER")
    print("=" * 48)

    host = input("Enter an IP address or hostname: ").strip()

    if not host:
        print("[ERROR] Hostname or IP address cannot be empty.")
        return

    if not valid_target(host):
        print("[ERROR] Invalid IP address or hostname format.")
        return

    ports_input = input(
        "Enter TCP ports (e.g. 80,443), or press Enter to skip: "
    ).strip()

    ports = []

    if ports_input:
        try:
            items = [item.strip() for item in ports_input.split(",")]

            if any(not item.isdigit() for item in items):
                raise ValueError

            ports = list(dict.fromkeys(int(item) for item in items))

            if any(port < 1 or port > 65535 for port in ports):
                raise ValueError

        except ValueError:
            print(
                "[ERROR] Invalid ports. Enter comma-separated "
                "numbers from 1 to 65535, such as 80,443."
            )
            return

    print(f"\nChecking target: {host}")

    ping_result = ping_host(host)
    resolved_ip = dns_check(host)

    port_results = {}

    for port in ports:
        port_results[port] = check_tcp_port(host, port)

    print("\n" + "=" * 48)
    print("                 SUMMARY")
    print("=" * 48)
    print(f"Target: {host}")
    print(f"Ping:   {'SUCCESS' if ping_result else 'FAILED'}")
    print(f"DNS:    {'SUCCESS' if resolved_ip else 'FAILED'}")

    for port, success in port_results.items():
        status = "REACHABLE" if success else "NOT REACHABLE"
        print(f"TCP {port}: {status}")

    if not port_results:
        print("TCP ports: Not checked")

    print("=" * 48)


if __name__ == "__main__":
    main()
