"""Small Flask service for creating Adobe Connect meeting rooms."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin
from xml.etree import ElementTree

import requests
from flask import Flask, jsonify, request


@dataclass(frozen=True)
class AdobeConnectConfig:
    """Runtime configuration for Adobe Connect XML API calls."""

    base_url: str
    username: str
    password: str
    folder_id: str

    @property
    def api_url(self) -> str:
        return urljoin(self.base_url.rstrip("/") + "/", "api/xml")


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def home() -> tuple[str, int]:
        return "Server is running 🚀", 200

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    @app.route("/create-room", methods=["GET", "POST"])
    def create_room() -> tuple[Any, int]:
        try:
            config = load_config()
            room_name = room_name_from_request()
            access = request.args.get("access", "protected").lower()

            client = AdobeConnectClient(config)
            client.login()
            meeting = client.create_meeting(room_name)
            client.set_public_access(meeting["sco_id"], access)

            return jsonify(meeting), 201
        except AdobeConnectError as exc:
            return jsonify({"error": str(exc)}), exc.status_code
        except requests.RequestException as exc:
            return jsonify({"error": f"Adobe Connect request failed: {exc}"}), 502

    return app


class AdobeConnectError(Exception):
    """Application-level error with an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class AdobeConnectClient:
    """Thin client for the Adobe Connect XML API."""

    def __init__(self, config: AdobeConnectConfig) -> None:
        self.config = config
        self.session = requests.Session()

    def login(self) -> None:
        xml = self._get(
            {
                "action": "login",
                "login": self.config.username,
                "password": self.config.password,
            }
        )
        ensure_ok(xml, "login")

    def create_meeting(self, name: str) -> dict[str, str]:
        url_path = f"/{slugify(name)}/"
        xml = self._get(
            {
                "action": "sco-update",
                "type": "meeting",
                "name": name,
                "folder-id": self.config.folder_id,
                "url-path": url_path,
            }
        )
        ensure_ok(xml, "create meeting")

        sco = xml.find("sco")
        if sco is None:
            raise AdobeConnectError("Adobe Connect did not return a meeting SCO.", 502)

        sco_id = sco.attrib.get("sco-id")
        returned_url_path = text_or_none(sco.find("url-path")) or url_path
        if not sco_id:
            raise AdobeConnectError("Adobe Connect response did not include sco-id.", 502)

        return {
            "sco_id": sco_id,
            "name": name,
            "url_path": returned_url_path,
            "room": urljoin(self.config.base_url.rstrip("/") + "/", returned_url_path.lstrip("/")),
        }

    def set_public_access(self, sco_id: str, access: str) -> None:
        permissions = {
            "public": "view-hidden",
            "protected": "remove",
            "private": "denied",
        }
        permission_id = permissions.get(access)
        if permission_id is None:
            raise AdobeConnectError("access must be one of: public, protected, private")

        xml = self._get(
            {
                "action": "permissions-update",
                "acl-id": sco_id,
                "principal-id": "public-access",
                "permission-id": permission_id,
            }
        )
        ensure_ok(xml, "set meeting access")

    def _get(self, params: dict[str, str]) -> ElementTree.Element:
        response = self.session.get(self.config.api_url, params=params, timeout=30)
        response.raise_for_status()
        try:
            return ElementTree.fromstring(response.text)
        except ElementTree.ParseError as exc:
            raise AdobeConnectError("Adobe Connect returned invalid XML.", 502) from exc


def load_config() -> AdobeConnectConfig:
    values = {
        "AC_BASE_URL": os.getenv("AC_BASE_URL"),
        "AC_USER": os.getenv("AC_USER"),
        "AC_PASS": os.getenv("AC_PASS"),
        "AC_FOLDER_ID": os.getenv("AC_FOLDER_ID"),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise AdobeConnectError(f"Missing environment variables: {', '.join(missing)}", 500)

    return AdobeConnectConfig(
        base_url=values["AC_BASE_URL"].rstrip("/"),
        username=values["AC_USER"],
        password=values["AC_PASS"],
        folder_id=values["AC_FOLDER_ID"],
    )


def room_name_from_request() -> str:
    payload = request.get_json(silent=True) or {}
    requested_name = payload.get("name") or request.args.get("name")
    if requested_name:
        return str(requested_name).strip()
    return f"hangout_{int(time.time())}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    if not slug:
        raise AdobeConnectError("Room name must contain at least one letter or number.")
    return slug[:60]


def ensure_ok(xml: ElementTree.Element, action_name: str) -> None:
    status = xml.find("status")
    code = status.attrib.get("code") if status is not None else None
    if code == "ok":
        return

    subcode = status.attrib.get("subcode") if status is not None else None
    detail = f" ({subcode})" if subcode else ""
    raise AdobeConnectError(f"Adobe Connect could not {action_name}: {code or 'missing status'}{detail}", 502)


def text_or_none(element: ElementTree.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return element.text.strip()


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
