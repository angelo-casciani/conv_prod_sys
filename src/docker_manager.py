import subprocess
import sys
import signal
import atexit
import time
import shutil
import requests


_containers_stopped = False
_docker_cmd = None
_compose_cmd = None

def get_docker_command():
    global _docker_cmd
    if _docker_cmd is not None:
        return _docker_cmd
    
    docker_path = shutil.which('docker')
    if not docker_path:
        return None
    
    try:
        result = subprocess.run(['docker', 'info'], capture_output=True, timeout=5)
        if result.returncode == 0:
            _docker_cmd = ['docker']
            return _docker_cmd
    except (subprocess.TimeoutExpired, Exception):
        pass
    try:
        result = subprocess.run(['sudo', 'docker', 'info'], capture_output=True, timeout=5)
        if result.returncode == 0:
            _docker_cmd = ['sudo', 'docker']
            return _docker_cmd
    except (subprocess.TimeoutExpired, Exception):
        pass
    
    _docker_cmd = ['docker']
    return _docker_cmd


def get_compose_command(docker_cmd):
    global _compose_cmd
    if _compose_cmd is not None:
        return _compose_cmd

    # Preferred path: docker compose plugin.
    try:
        result = subprocess.run(
            docker_cmd + ['compose', 'version'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            _compose_cmd = docker_cmd + ['compose']
            return _compose_cmd
    except (subprocess.TimeoutExpired, Exception):
        pass

    # Fallback: standalone docker-compose binary.
    docker_compose_path = shutil.which('docker-compose')
    if docker_compose_path:
        if docker_cmd and docker_cmd[0] == 'sudo':
            _compose_cmd = ['sudo', 'docker-compose']
        else:
            _compose_cmd = ['docker-compose']
        return _compose_cmd

    return None


def wait_for_dtlogextsim(url="http://127.0.0.1:6662/", max_attempts=30, delay=1):
    print("Waiting for DTLogExtSim service to be ready...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code in [200, 404, 405]:  # Any response means it's alive
                print(f"DTLogExtSim service is ready (attempt {attempt + 1})")
                return True
        except (requests.ConnectionError, requests.Timeout):
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"DTLogExtSim service not responding after {max_attempts} attempts")
                return False
        except Exception as e:
            print(f"Unexpected error checking DTLogExtSim: {e}")
            return False
    return False


def start_docker_containers():
    try:
        docker_cmd = get_docker_command()
        if not docker_cmd:
            print("Warning: docker command not found, skipping container startup")
            return False

        compose_cmd = get_compose_command(docker_cmd)
        
        print("Starting Docker containers...")
        result = None

        if compose_cmd:
            result = subprocess.run(
                compose_cmd + ['up', '-d'],
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            print("Warning: No compose command available; trying direct container startup")

        if result is not None and result.returncode == 0:
            print("Docker containers started successfully")
            # Wait for DTLogExtSim to be ready
            wait_for_dtlogextsim()
            return True

        # Fallback path when compose is unavailable or failed.
        fallback_result = subprocess.run(
            docker_cmd + ['start', 'uppaal-engine', 'extractor-service'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if fallback_result.returncode == 0:
            print("Docker containers started successfully (fallback)")
            wait_for_dtlogextsim()
            return True

        print(f"Warning: Docker containers may not have started properly")
        if result is not None and result.stderr:
            print(f"   Error: {result.stderr}")
        if fallback_result.stderr:
            print(f"   Fallback error: {fallback_result.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("Warning: Docker startup timed out")
        return False
    except FileNotFoundError:
        print("Warning: docker command not found, skipping container startup")
        return False
    except Exception as e:
        print(f"Warning: Error starting Docker containers: {e}")
        return False


def stop_docker_containers():
    global _containers_stopped
    if _containers_stopped:
        return
    
    _containers_stopped = True
    try:
        docker_cmd = get_docker_command()
        if not docker_cmd:
            print("Warning: docker command not found, skipping container shutdown")
            return

        compose_cmd = get_compose_command(docker_cmd)
        
        print("\nStopping Docker containers...")
        result = None
        if compose_cmd:
            result = subprocess.run(
                compose_cmd + ['down'],
                capture_output=True,
                text=True,
                timeout=30
            )

        if result is not None and result.returncode == 0:
            print("Docker containers stopped successfully")
            return

        fallback_result = subprocess.run(
            docker_cmd + ['stop', 'uppaal-engine', 'extractor-service'],
            capture_output=True,
            text=True,
            timeout=20
        )
        if fallback_result.returncode == 0:
            print("Docker containers stopped successfully (fallback)")
        else:
            print(f"Warning: Docker containers may not have stopped properly")
            if result is not None and result.stderr:
                print(f"   Error: {result.stderr}")
            if fallback_result.stderr:
                print(f"   Fallback error: {fallback_result.stderr}")
    except subprocess.TimeoutExpired:
        print("Warning: Docker shutdown timed out")
    except FileNotFoundError:
        print("Warning: docker command not found, skipping container shutdown")
    except Exception as e:
        print(f"Warning: Error stopping Docker containers: {e}")


def check_docker_status():
    try:
        docker_cmd = get_docker_command()
        if not docker_cmd:
            return False

        compose_cmd = get_compose_command(docker_cmd)

        if compose_cmd:
            result = subprocess.run(
                compose_cmd + ['ps', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0

        result = subprocess.run(
            docker_cmd + ['ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False

        names = set(result.stdout.splitlines())
        return {'uppaal-engine', 'extractor-service'}.issubset(names)
    except Exception:
        return False


def signal_handler(sig, frame):
    print("\n\nReceived interrupt signal. Shutting down gracefully...")
    stop_docker_containers()
    sys.exit(0)


def setup_docker_lifecycle():
    start_docker_containers()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(stop_docker_containers)
    
    print("Docker lifecycle management initialized\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "start":
            start_docker_containers()
        elif sys.argv[1] == "stop":
            stop_docker_containers()
        elif sys.argv[1] == "status":
            if check_docker_status():
                print("Docker containers are running!")
            else:
                print("Docker containers are not running...")
    else:
        setup_docker_lifecycle()
        print("Docker lifecycle setup complete. Press Ctrl+C to stop containers.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
