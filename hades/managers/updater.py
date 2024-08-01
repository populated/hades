from pathlib import Path
from typing import Union, List, Dict, Any

import os
import requests
import sys

class Updater:
    REPO = "https://api.github.com/repos/populated/hades/contents/"
    RAW = "https://raw.githubusercontent.com/populated/hades/main/"
    UPDATE = f"{RAW}update.json"
    TO_IGNORE = {"README.md"}

    def __init__(self, current_version: Union[float, int, str]):
        self.current = float(current_version) if '.' in str(current_version) else int(current_version)

    @staticmethod
    def latest() -> float:
        return float(requests.get(Updater.UPDATE).json().get("version"))

    @staticmethod
    def fetch(repo_url: str) -> List[Dict[str, Any]]:
        return requests.get(repo_url).json()

    @staticmethod
    def download(url: str, path: Path) -> None:
        response = requests.get(url)
        response.raise_for_status()
        path.write_bytes(response.content)

    def has_update(self) -> bool:
        return (latest := self.latest()) > self.current

    def replace_files(self, repo_files: List[Dict[str, Any]], base_path: Path = Path(".")) -> None:
        update_config = requests.get(self.UPDATE).json().get("update_config", False)
        print("[HADES UPDATER] The config will be updated! (reset)") if update_config else None

        [
            self.process_file(file_info, base_path, update_config) 
            for file_info in repo_files 
            if file_info["name"] not in self.TO_IGNORE
        ]

    def process_file(self, file_info: Dict[str, Any], base_path: Path, update_config: bool) -> None:
        path = base_path / file_info["path"]

        if file_info["type"] == "file" and (file_info["name"] != "config.json" or update_config):
            self.download(f'{self.RAW}{file_info["path"]}', path)
            
        elif file_info["type"] == "dir":
            path.mkdir(parents=True, exist_ok=True)
            self.replace_files(self.fetch(file_info["_links"]["self"]), base_path)

    def restart(self) -> None:
        os.execv(sys.executable, ["python"] + sys.argv)

    def run(self) -> None:
        if self.has_update():
            print("[HADES UPDATER] An update is available. Updating...")
            self.replace_files(self.fetch(self.REPO))
            print("[HADES UPDATER] Update completed. Restarting application...")
            self.current = self.latest()
            self.restart()
        else:
            print("[HADES UPDATER] No update available.")
