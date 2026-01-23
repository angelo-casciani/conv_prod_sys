import subprocess
import sys
import signal
import atexit
import time
import os


_containers_stopped = False

def cleanup_parameters():
    params_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'parameters')
    if os.path.exists(params_dir):
        for filename in os.listdir(params_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(params_dir, filename)
                try:
                    os.remove(file_path)
                    print(f"Cleaned up: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")

def start_docker_containers():
    try:
        print("Starting Docker containers...")
        result = subprocess.run(
            ['sudo', 'docker', 'compose', 'up', '-d'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("Docker containers started successfully")
            # Give containers a moment to initialize
            time.sleep(2)
            return True
        else:
            print(f"Warning: Docker containers may not have started properly")
            if result.stderr:
                print(f"   Error: {result.stderr}")
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
        print("\nStopping Docker containers...")
        result = subprocess.run(
            ['sudo', 'docker', 'compose', 'down'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("Docker containers stopped successfully")
        else:
            print(f"Warning: Docker containers may not have stopped properly")
            if result.stderr:
                print(f"   Error: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("Warning: Docker shutdown timed out")
    except FileNotFoundError:
        print("Warning: docker command not found, skipping container shutdown")
    except Exception as e:
        print(f"Warning: Error stopping Docker containers: {e}")


def check_docker_status():
    try:
        result = subprocess.run(
            ['sudo', 'docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def signal_handler(sig, frame):
    print("\n\n🛑 Received interrupt signal. Shutting down gracefully...")
    cleanup_parameters()
    stop_docker_containers()
    sys.exit(0)


def setup_docker_lifecycle():
    start_docker_containers()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_parameters)
    atexit.register(stop_docker_containers)
    
    print("✓ Docker lifecycle management initialized\n")


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
