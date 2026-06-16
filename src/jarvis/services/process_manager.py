from pathlib import Path
import time

import psutil


class ProcessManager:

    def get_exe_name(self, app_path: str) -> str:
        return Path(app_path).name

    def normalize_process_name(self, name: str) -> str:
        return name.lower().strip()

    def find_processes_by_exe(self, exe_name: str):
        exe_name = self.normalize_process_name(exe_name)
        matched_processes = []

        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "exe"
            ]
        ):
            try:
                proc_name = proc.info.get("name")

                if not proc_name:
                    continue

                if self.normalize_process_name(proc_name) == exe_name:
                    matched_processes.append(proc)

            except Exception:
                continue

        return matched_processes

    def close_by_exe(self, exe_name: str) -> bool:
        processes = self.find_processes_by_exe(exe_name)

        if not processes:
            return False

        closed_any = False

        for proc in processes:
            try:
                proc.terminate()
                closed_any = True
            except Exception:
                continue

        deadline = time.time() + 2

        while time.time() < deadline:
            still_running = []

            for proc in processes:
                try:
                    if proc.is_running():
                        still_running.append(proc)
                except Exception:
                    continue

            if not still_running:
                return closed_any

            time.sleep(0.2)

        for proc in processes:
            try:
                if proc.is_running():
                    proc.kill()
                    closed_any = True
            except Exception:
                continue

        return closed_any