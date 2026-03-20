"""N.I.N.A. Advanced API client for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import API_BASE

_LOGGER = logging.getLogger(__name__)


class NinaApiError(Exception):
    """Raised when the N.I.N.A. API returns an error."""


class NinaConnectionError(Exception):
    """Raised when a connection to N.I.N.A. cannot be established."""


class NinaApiClient:
    """Async HTTP client wrapping the N.I.N.A. Advanced API v2."""

    def __init__(
        self,
        host: str,
        port: int,
        api_version: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._base = API_BASE.format(host=host, port=port, version=api_version)
        self._session = session

    # ─── Low-level helpers ───────────────────────────────────────────────────

    async def _get(self, path: str, params: dict | None = None) -> Any:
        url = self._base + path
        try:
            async with self._session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                text = await resp.text()
                raise NinaApiError(f"GET {path} → {resp.status}: {text}")
        except aiohttp.ClientConnectorError as exc:
            raise NinaConnectionError(f"Cannot reach N.I.N.A. at {url}") from exc
        except asyncio.TimeoutError as exc:
            raise NinaConnectionError(f"Timeout reaching N.I.N.A. at {url}") from exc

    async def _post(self, path: str, data: dict | None = None, params: dict | None = None) -> Any:
        url = self._base + path
        try:
            async with self._session.post(
                url, json=data, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status in (200, 204):
                    try:
                        return await resp.json()
                    except Exception:
                        return {}
                text = await resp.text()
                raise NinaApiError(f"POST {path} → {resp.status}: {text}")
        except aiohttp.ClientConnectorError as exc:
            raise NinaConnectionError(f"Cannot reach N.I.N.A. at {url}") from exc
        except asyncio.TimeoutError as exc:
            raise NinaConnectionError(f"Timeout reaching N.I.N.A. at {url}") from exc

    # ─── Application ─────────────────────────────────────────────────────────

    async def get_version(self) -> dict:
        return await self._get("/version")

    async def get_app_info(self) -> dict:
        return await self._get("/application")

    # ─── Camera ──────────────────────────────────────────────────────────────

    async def get_camera(self) -> dict:
        return await self._get("/equipment/camera")

    async def connect_camera(self) -> dict:
        return await self._get("/equipment/camera/connect")

    async def disconnect_camera(self) -> dict:
        return await self._get("/equipment/camera/disconnect")

    async def cool_camera(self, temperature: float, minutes: float = 10) -> dict:
        """Start cooling the camera to `temperature` °C over `minutes` minutes."""
        return await self._get(
            "/equipment/camera/cool",
            params={"temperature": temperature, "minutes": minutes},
        )

    async def warm_camera(self, minutes: float = 10) -> dict:
        """Gradually warm the camera over `minutes` minutes."""
        return await self._get("/equipment/camera/warm", params={"minutes": minutes})

    async def capture_image(
        self,
        exposure: float,
        gain: int | None = None,
        filter_index: int | None = None,
        binning: int = 1,
        save: bool = False,
    ) -> dict:
        params: dict[str, Any] = {"time": exposure, "binning": binning, "save": str(save).lower()}
        if gain is not None:
            params["gain"] = gain
        if filter_index is not None:
            params["filter_index"] = filter_index
        return await self._get("/equipment/camera/capture", params=params)

    async def abort_capture(self) -> dict:
        return await self._get("/equipment/camera/abort")

    # ─── Mount / Telescope ───────────────────────────────────────────────────

    async def get_mount(self) -> dict:
        return await self._get("/equipment/telescope")

    async def connect_mount(self) -> dict:
        return await self._get("/equipment/telescope/connect")

    async def disconnect_mount(self) -> dict:
        return await self._get("/equipment/telescope/disconnect")

    async def slew_mount(self, ra: float, dec: float) -> dict:
        """Slew to J2000 RA/Dec coordinates (decimal degrees)."""
        return await self._get(
            "/equipment/telescope/slew-to-coordinates-j2000",
            params={"ra": ra, "dec": dec},
        )

    async def park_mount(self) -> dict:
        return await self._get("/equipment/telescope/park")

    async def unpark_mount(self) -> dict:
        return await self._get("/equipment/telescope/unpark")

    async def set_tracking(self, enabled: bool) -> dict:
        return await self._get(
            "/equipment/telescope/tracking", params={"on": str(enabled).lower()}
        )

    async def find_home(self) -> dict:
        return await self._get("/equipment/telescope/find-home")

    # ─── Focuser ─────────────────────────────────────────────────────────────

    async def get_focuser(self) -> dict:
        return await self._get("/equipment/focuser")

    async def connect_focuser(self) -> dict:
        return await self._get("/equipment/focuser/connect")

    async def disconnect_focuser(self) -> dict:
        return await self._get("/equipment/focuser/disconnect")

    async def move_focuser(self, position: int) -> dict:
        return await self._get("/equipment/focuser/move", params={"position": position})

    async def auto_focus(self) -> dict:
        return await self._get("/equipment/focuser/auto-focus")

    # ─── Filter Wheel ────────────────────────────────────────────────────────

    async def get_filterwheel(self) -> dict:
        return await self._get("/equipment/filterwheel")

    async def connect_filterwheel(self) -> dict:
        return await self._get("/equipment/filterwheel/connect")

    async def disconnect_filterwheel(self) -> dict:
        return await self._get("/equipment/filterwheel/disconnect")

    async def change_filter(self, index: int) -> dict:
        return await self._get(
            "/equipment/filterwheel/change-filter", params={"filterId": index}
        )

    # ─── Guider ──────────────────────────────────────────────────────────────

    async def get_guider(self) -> dict:
        return await self._get("/equipment/guider")

    async def connect_guider(self) -> dict:
        return await self._get("/equipment/guider/connect")

    async def disconnect_guider(self) -> dict:
        return await self._get("/equipment/guider/disconnect")

    async def start_guiding(self, force_calibration: bool = False) -> dict:
        return await self._get(
            "/equipment/guider/start-guiding",
            params={"forceCalibration": str(force_calibration).lower()},
        )

    async def stop_guiding(self) -> dict:
        return await self._get("/equipment/guider/stop-guiding")

    async def dither(self) -> dict:
        return await self._get("/equipment/guider/dither")

    # ─── Rotator ─────────────────────────────────────────────────────────────

    async def get_rotator(self) -> dict:
        return await self._get("/equipment/rotator")

    async def connect_rotator(self) -> dict:
        return await self._get("/equipment/rotator/connect")

    async def disconnect_rotator(self) -> dict:
        return await self._get("/equipment/rotator/disconnect")

    async def move_rotator(self, position: float) -> dict:
        return await self._get("/equipment/rotator/move", params={"position": position})

    # ─── Dome ────────────────────────────────────────────────────────────────

    async def get_dome(self) -> dict:
        return await self._get("/equipment/dome")

    async def connect_dome(self) -> dict:
        return await self._get("/equipment/dome/connect")

    async def disconnect_dome(self) -> dict:
        return await self._get("/equipment/dome/disconnect")

    async def open_dome(self) -> dict:
        return await self._get("/equipment/dome/open")

    async def close_dome(self) -> dict:
        return await self._get("/equipment/dome/close")

    async def park_dome(self) -> dict:
        return await self._get("/equipment/dome/park")

    async def home_dome(self) -> dict:
        return await self._get("/equipment/dome/home")

    # ─── Flat Device ─────────────────────────────────────────────────────────

    async def get_flatdevice(self) -> dict:
        return await self._get("/equipment/flatdevice")

    async def connect_flatdevice(self) -> dict:
        return await self._get("/equipment/flatdevice/connect")

    async def toggle_flat_light(self, on: bool) -> dict:
        return await self._get(
            "/equipment/flatdevice/toggle-light", params={"on": str(on).lower()}
        )

    async def set_flat_brightness(self, brightness: int) -> dict:
        return await self._get(
            "/equipment/flatdevice/set-brightness", params={"brightness": brightness}
        )

    # ─── Sequence ────────────────────────────────────────────────────────────

    async def get_sequence(self) -> dict:
        return await self._get("/sequence")

    async def start_sequence(self) -> dict:
        return await self._get("/sequence/start")

    async def stop_sequence(self) -> dict:
        return await self._get("/sequence/stop")

    async def load_sequence(self, path: str) -> dict:
        return await self._get("/sequence/load", params={"path": path})

    # ─── Images ──────────────────────────────────────────────────────────────

    async def get_image_history(self, count: int = 10) -> dict:
        return await self._get("/image/history", params={"count": count})

    async def get_latest_image(self) -> dict:
        return await self._get("/image/latest")

    # ─── Convenience: poll all equipment in one pass ──────────────────────────

    async def poll_all(self) -> dict[str, Any]:
        """Fetch all equipment data concurrently. Returns {subsystem: data}."""
        tasks = {
            "camera": self.get_camera(),
            "mount": self.get_mount(),
            "focuser": self.get_focuser(),
            "filterwheel": self.get_filterwheel(),
            "guider": self.get_guider(),
            "rotator": self.get_rotator(),
            "dome": self.get_dome(),
            "sequence": self.get_sequence(),
            "image_history": self.get_image_history(count=1),
            "flatdevice": self.get_flatdevice(),
        }
        results: dict[str, Any] = {}
        responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for key, response in zip(tasks.keys(), responses):
            if isinstance(response, Exception):
                _LOGGER.debug("Poll error for %s: %s", key, response)
                results[key] = {}
            else:
                results[key] = response
        return results
