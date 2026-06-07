import json
import subprocess
import time
from typing import Callable


class DockerDeployError(Exception):
    pass


class DockerPullError(DockerDeployError):
    pass


class DockerCleanupError(DockerDeployError):
    pass


class DockerCreateError(DockerDeployError):
    pass


class DockerStartError(DockerDeployError):
    pass


class DockerDeployer:
    def __init__(self, client=None):
        # The 'client' argument is ignored; we always use the CLI.
        pass

    def deploy(
        self,
        image_name: str,
        container_name: str,
        port_bindings: dict[str, int],
        environment: dict[str, str] | None = None,
        log_callback: Callable[[str, str], None] | None = None,
    ) -> str:
        """
        Pull, stop, remove, run, and verify a container using the docker CLI.
        """

        def log(msg: str, level: str = "info"):
            if log_callback:
                log_callback(msg, level)

        def run_docker(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
            """Helper to run a docker command and capture output."""
            cmd = ["docker"] + args
            log(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 and check:
                raise DockerDeployError(
                    f"Docker command failed: {' '.join(cmd)}\n"
                    f"stderr: {result.stderr.strip()}"
                )
            return result

        # 1. Pull image
        log(f"Pulling image: {image_name}")
        try:
            run_docker(["pull", image_name])
        except DockerDeployError as e:
            raise DockerPullError(str(e))

        # 2. Stop and remove existing container (if any)
        try:
            result = run_docker(["inspect", container_name], check=False)
            if result.returncode == 0:
                log(f"Stopping existing container {container_name}")
                run_docker(["stop", "--time=10", container_name])
                log(f"Removing existing container {container_name}")
                run_docker(["rm", "-f", container_name])
        except DockerDeployError as e:
            log(f"Cleanup warning: {e}", "warning")

        # 3. Run new container (detached)
        run_args = [
            "run",
            "--detach",
            "--name", container_name,
        ]
        # port bindings: {"80/tcp": 8080} -> -p 8080:80
        for container_port, host_port in port_bindings.items():
            c_port = container_port.split("/")[0]
            run_args.extend(["-p", f"{host_port}:{c_port}"])
        if environment:
            for k, v in environment.items():
                run_args.extend(["-e", f"{k}={v}"])
        run_args.append(image_name)

        log(f"Running container {container_name}")
        try:
            result = run_docker(run_args)
            container_id = result.stdout.strip()
        except DockerDeployError as e:
            raise DockerCreateError(str(e))

        # 4. Verify container is running
        time.sleep(2)
        inspect_result = run_docker(["inspect", container_id])
        try:
            data = json.loads(inspect_result.stdout)
            status = data[0]["State"]["Status"]
        except (json.JSONDecodeError, KeyError, IndexError):
            raise DockerStartError("Could not inspect container state")

        if status == "running":
            log(f"Container {container_name} ({container_id[:12]}) is running")
            return container_id[:12]
        else:
            # Grab logs
            logs_result = run_docker(["logs", "--tail=50", container_id], check=False)
            log(f"Container exited prematurely. Logs:\n{logs_result.stdout}", "error")
            try:
                run_docker(["rm", "-f", container_id], check=False)
            except Exception:
                pass
            raise DockerStartError(f"Container status '{status}' – expected 'running'")