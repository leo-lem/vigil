from atexit import register
from shlex import quote
from socket import create_connection
from subprocess import Popen, DEVNULL, PIPE
from time import time, sleep


def tunnel_ssh(ssh_user: str,
               remote_host: str,
               remote_port: int,
               local_port: int,
               jump_host: str | None,
               connect_timeout_s: float = 10.0,
               ready_timeout_s: float = 10.0) -> Popen:
    """Establish an SSH tunnel forwarding a local port to a remote port."""

    target = f"{ssh_user}@{remote_host}"
    jump_part = f"-J {quote(ssh_user + '@' + jump_host)}" if jump_host else ""
    cmd = (
        "ssh -o BatchMode=yes -o ExitOnForwardFailure=yes -o ConnectTimeout=10 "
        "-o ServerAliveInterval=30 -o ServerAliveCountMax=3 "
        f"{jump_part} -N -L {local_port}:127.0.0.1:{remote_port} {quote(target)}"
    )

    proc = Popen(cmd, shell=True, stdout=DEVNULL, stderr=PIPE, text=True)
    register(proc.terminate)

    deadline = time() + ready_timeout_s
    while time() < deadline:
        if proc.poll() is not None:
            stderr = ""
            if proc.stderr is not None:
                try:
                    stderr = proc.stderr.read()[-2000:]
                except Exception:
                    stderr = ""
                finally:
                    proc.stderr.close()
            raise RuntimeError(f"SSH tunnel exited early. Stderr:\n{stderr}")

        try:
            with create_connection(("127.0.0.1", local_port), timeout=connect_timeout_s):
                return proc
        except OSError:
            sleep(0.1)
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        proc.kill()
    raise RuntimeError(f"SSH tunnel not ready on 127.0.0.1:{local_port}")
