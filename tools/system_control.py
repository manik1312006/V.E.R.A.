"""System control tool for V.E.R.A. — process and app management."""

import subprocess
import platform
import psutil
from utils.logger import get_logger

logger = get_logger("vera.tools")


class SystemControl:
    """Controls system processes and applications."""

    def execute(self, action: str, parameters: str) -> str:
        """Execute a system control action.

        Args:
            action: The action to perform.
            parameters: Action parameters.

        Returns:
            Result message string.
        """
        handler = {
            "open_app": self.open_app,
            "close_app": self.close_app,
            "list_processes": self.list_processes,
            "kill_process": self.kill_process,
            "shutdown": self.shutdown,
            "restart": self.restart,
        }.get(action)

        if not handler:
            return f"Unknown action: {action}. Available: {list(self._actions().keys())}"

        return handler(parameters)

    def _actions(self) -> dict:
        return {
            "open_app": "Open an application (params: app_name)",
            "close_app": "Close an application (params: app_name)",
            "list_processes": "List running processes (params: optional filter)",
            "kill_process": "Kill a process (params: process_name or PID)",
            "shutdown": "Shutdown the computer (params: none)",
            "restart": "Restart the computer (params: none)",
        }

    def open_app(self, app_name: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.Popen(["start", "", app_name], shell=True)
            elif system == "darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen(["xdg-open", app_name] if "." in app_name else [app_name],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Opened application: {app_name}"
        except Exception as e:
            return f"Failed to open '{app_name}': {e}"

    def close_app(self, app_name: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.run(["taskkill", "/F", "/IM", f"{app_name}.exe"],
                               capture_output=True)
            else:
                subprocess.run(["pkill", "-f", app_name], capture_output=True)
            return f"Closed application: {app_name}"
        except Exception as e:
            return f"Failed to close '{app_name}': {e}"

    def list_processes(self, filter_str: str = "") -> str:
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                name = info["name"].lower()
                if filter_str and filter_str.lower() not in name:
                    continue
                processes.append(
                    f"PID: {info['pid']:>6} | {info['name']:<25} | "
                    f"CPU: {info['cpu_percent']:>5.1f}% | MEM: {info['memory_percent']:>5.1f}%"
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if not processes:
            return f"No processes found matching '{filter_str}'"

        header = f"{'PID':>6} | {'Name':<25} | {'CPU':>5} | {'MEM':>5}"
        separator = "-" * len(header)
        return f"{header}\n{separator}\n" + "\n".join(processes[:50])

    def kill_process(self, target: str) -> str:
        try:
            if target.isdigit():
                proc = psutil.Process(int(target))
                proc.kill()
                return f"Killed process PID: {target}"
            else:
                killed = []
                for proc in psutil.process_iter(["pid", "name"]):
                    if target.lower() in proc.info["name"].lower():
                        proc.kill()
                        killed.append(str(proc.info["pid"]))
                if killed:
                    return f"Killed processes: {', '.join(killed)}"
                return f"No processes found matching '{target}'"
        except Exception as e:
            return f"Failed to kill '{target}': {e}"

    def shutdown(self, _: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.run(["shutdown", "/s", "/t", "10"])
            elif system == "darwin":
                subprocess.run(["osascript", "-e", 'tell app "System Events" to shut down'])
            else:
                subprocess.run(["sudo", "shutdown", "-h", "+1"])
            return "Shutdown initiated."
        except Exception as e:
            return f"Failed to shutdown: {e}"

    def restart(self, _: str) -> str:
        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.run(["shutdown", "/r", "/t", "10"])
            elif system == "darwin":
                subprocess.run(["osascript", "-e", 'tell app "System Events" to restart'])
            else:
                subprocess.run(["sudo", "shutdown", "-r", "+1"])
            return "Restart initiated."
        except Exception as e:
            return f"Failed to restart: {e}"
