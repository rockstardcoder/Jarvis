import subprocess


class PackageManager:

    def winget_available(self) -> bool:
        try:
            result = subprocess.run(
                [
                    "winget",
                    "--version"
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            return result.returncode == 0

        except Exception:
            return False

    def clean_winget_output(self, output: str) -> str:
        lines = output.splitlines()
        clean_lines = []

        table_started = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("Name "):
                table_started = True

            if table_started:
                clean_lines.append(line)

        if clean_lines:
            return "\n".join(clean_lines)

        fallback_lines = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            if "█" in stripped or "▒" in stripped:
                continue

            if "%" in stripped and "/" not in stripped:
                continue

            fallback_lines.append(line)

        return "\n".join(fallback_lines).strip()

    def search(self, query: str) -> str:
        if not self.winget_available():
            return "winget is not available on this PC."

        try:
            result = subprocess.run(
                [
                    "winget",
                    "search",
                    query,
                    "--source",
                    "winget",
                    "--accept-source-agreements",
                    "--disable-interactivity"
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45
            )

            output = result.stdout.strip()

            if not output:
                output = result.stderr.strip()

            output = self.clean_winget_output(output)

            if not output:
                return "No package results found."

            return output

        except Exception as e:
            return f"Package search failed: {e}"

    def list_installed(self, query: str | None = None) -> str:
        if not self.winget_available():
            return "winget is not available on this PC."

        command = [
            "winget",
            "list",
            "--disable-interactivity"
        ]

        if query:
            command.append(query)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45
            )

            output = result.stdout.strip()

            if not output:
                output = result.stderr.strip()

            output = self.clean_winget_output(output)

            if not output:
                return "No installed package results found."

            return output

        except Exception as e:
            return f"Installed package search failed: {e}"

    def install_by_id(self, package_id: str) -> str:
        if not self.winget_available():
            return "winget is not available on this PC."

        try:
            subprocess.Popen(
                [
                    "winget",
                    "install",
                    "--id",
                    package_id,
                    "--exact",
                    "--source",
                    "winget",
                    "--accept-source-agreements",
                    "--accept-package-agreements"
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            return (
                f"Started installer for package '{package_id}'. "
                "A new terminal window may open. After installation finishes, run 'refresh apps'."
            )

        except Exception as e:
            return f"Failed to start installer: {e}"

    def uninstall_by_id(self, package_id: str) -> str:
        if not self.winget_available():
            return "winget is not available on this PC."

        try:
            subprocess.Popen(
                [
                    "winget",
                    "uninstall",
                    "--id",
                    package_id,
                    "--exact"
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            return (
                f"Started uninstaller for package '{package_id}'. "
                "A new terminal window may open. After uninstall finishes, run 'refresh apps'."
            )

        except Exception as e:
            return f"Failed to start uninstaller: {e}"

    def open_installed_apps_settings(self) -> str:
        try:
            subprocess.Popen(
                [
                    "explorer.exe",
                    "ms-settings:appsfeatures"
                ]
            )

            return "Opening installed apps settings."

        except Exception as e:
            return f"Failed to open installed apps settings: {e}"