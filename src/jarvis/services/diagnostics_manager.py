import json
from pathlib import Path

import requests

from jarvis.services.training_logger import PRIVACY_POLICY_FILE


DIAGNOSTICS_SETTINGS_FILE = Path(
    "data/settings/diagnostics_settings.json"
)


DEFAULT_DIAGNOSTICS_SETTINGS = {
    "allow_diagnostics_upload": False,
    "privacy_policy_accepted": False,
    "privacy_policy_version": "1.0",
    "upload_endpoint": "",
    "last_export_path": "",
    "last_upload_status": ""
}


class DiagnosticsManager:

    def __init__(
        self
    ):
        self.settings = DEFAULT_DIAGNOSTICS_SETTINGS.copy()
        self.load()

    def load(
        self
    ):
        DIAGNOSTICS_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not DIAGNOSTICS_SETTINGS_FILE.exists():
            self.save()
            return self.settings

        try:
            with open(
                DIAGNOSTICS_SETTINGS_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(
                    f
                )

            if isinstance(
                data,
                dict
            ):
                self.settings.update(
                    data
                )

        except Exception:
            self.settings = DEFAULT_DIAGNOSTICS_SETTINGS.copy()
            self.save()

        return self.settings

    def save(
        self
    ):
        DIAGNOSTICS_SETTINGS_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            DIAGNOSTICS_SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.settings,
                f,
                indent=4
            )

    def is_upload_allowed(
        self
    ) -> bool:
        return bool(
            self.settings.get(
                "allow_diagnostics_upload",
                False
            )
        ) and bool(
            self.settings.get(
                "privacy_policy_accepted",
                False
            )
        )

    def get_status(
        self
    ) -> str:
        return (
            "Diagnostics Status:\n"
            f"- Upload allowed: {self.is_upload_allowed()}\n"
            f"- Privacy policy accepted: {self.settings.get('privacy_policy_accepted', False)}\n"
            f"- Upload endpoint configured: {bool(self.settings.get('upload_endpoint', ''))}\n"
            f"- Last export path: {self.settings.get('last_export_path', '') or 'none'}\n"
            f"- Last upload status: {self.settings.get('last_upload_status', '') or 'none'}"
        )

    def read_privacy_policy(
        self
    ) -> str:
        if not PRIVACY_POLICY_FILE.exists():
            return "Privacy policy file was not found."

        with open(
            PRIVACY_POLICY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return f.read()

    def accept_policy_and_enable_upload(
        self
    ) -> str:
        self.settings["privacy_policy_accepted"] = True
        self.settings["allow_diagnostics_upload"] = True
        self.save()

        return (
            "Diagnostics upload consent saved. "
            "Uploads are now allowed only when you manually send diagnostics."
        )

    def disable_upload(
        self
    ) -> str:
        self.settings["allow_diagnostics_upload"] = False
        self.save()

        return "Diagnostics upload disabled."

    def set_upload_endpoint(
        self,
        endpoint: str
    ) -> str:
        self.settings["upload_endpoint"] = str(
            endpoint
        ).strip()

        self.save()

        return "Diagnostics upload endpoint saved."

    def export_logs(
        self,
        logger
    ) -> str:
        export_path = logger.export_logs()

        self.settings["last_export_path"] = export_path
        self.save()

        return f"Training_Data exported to: {export_path}"

    def delete_logs(
        self,
        logger
    ) -> str:
        return logger.delete_logs()

    def send_diagnostics(
        self,
        logger
    ) -> str:
        if not self.is_upload_allowed():
            return (
                "Diagnostics upload is disabled. "
                "Read the privacy policy and enable diagnostics upload first."
            )

        endpoint = str(
            self.settings.get(
                "upload_endpoint",
                ""
            )
        ).strip()

        export_path = logger.export_logs()

        self.settings["last_export_path"] = export_path

        if not endpoint:
            self.settings["last_upload_status"] = (
                "No upload endpoint configured."
            )
            self.save()

            return (
                "Diagnostics package was created, but no upload endpoint is configured.\n"
                f"Exported package: {export_path}"
            )

        try:
            with open(
                export_path,
                "rb"
            ) as f:
                response = requests.post(
                    endpoint,
                    files={
                        "file": f
                    },
                    timeout=30
                )

            if response.status_code >= 400:
                self.settings["last_upload_status"] = (
                    f"Upload failed: HTTP {response.status_code}"
                )
                self.save()

                return self.settings["last_upload_status"]

            self.settings["last_upload_status"] = "Upload successful."
            self.save()

            return "Diagnostics uploaded successfully."

        except Exception as e:
            self.settings["last_upload_status"] = f"Upload failed: {e}"
            self.save()

            return self.settings["last_upload_status"]