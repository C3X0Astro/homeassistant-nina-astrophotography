"""Binary sensors for N.I.N.A. Astrophotography integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NinaDataCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class NinaBinarySensorDescription(BinarySensorEntityDescription):
    """Extends BinarySensorEntityDescription with value callable."""

    value_fn: Any = None  # Callable[[dict], bool | None]


def _safe(data: dict, *keys: str, default=None):
    d = data
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


BINARY_SENSOR_DESCRIPTIONS: list[NinaBinarySensorDescription] = [
    # ── Camera ────────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="camera_connected",
        name="Camera Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:camera",
        value_fn=lambda d: bool(_safe(d, "camera", "Response", "Connected")),
    ),
    NinaBinarySensorDescription(
        key="camera_cooling_enabled",
        name="Camera Cooling",
        icon="mdi:snowflake",
        value_fn=lambda d: bool(_safe(d, "camera", "Response", "CoolerOn")),
    ),

    # ── Mount ─────────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="mount_connected",
        name="Mount Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:telescope",
        value_fn=lambda d: bool(_safe(d, "mount", "Response", "Connected")),
    ),
    NinaBinarySensorDescription(
        key="mount_parked",
        name="Mount Parked",
        icon="mdi:parking",
        value_fn=lambda d: bool(_safe(d, "mount", "Response", "AtPark")),
    ),
    NinaBinarySensorDescription(
        key="mount_tracking",
        name="Mount Tracking",
        icon="mdi:orbit",
        value_fn=lambda d: bool(_safe(d, "mount", "Response", "TrackingEnabled")),
    ),
    NinaBinarySensorDescription(
        key="mount_slewing",
        name="Mount Slewing",
        device_class=BinarySensorDeviceClass.MOVING,
        icon="mdi:rotate-3d-variant",
        value_fn=lambda d: bool(_safe(d, "mount", "Response", "Slewing")),
    ),

    # ── Focuser ───────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="focuser_connected",
        name="Focuser Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:focus-field",
        value_fn=lambda d: bool(_safe(d, "focuser", "Response", "Connected")),
    ),
    NinaBinarySensorDescription(
        key="focuser_is_moving",
        name="Focuser Moving",
        device_class=BinarySensorDeviceClass.MOVING,
        icon="mdi:arrow-expand-horizontal",
        value_fn=lambda d: bool(_safe(d, "focuser", "Response", "IsMoving")),
    ),

    # ── Filter Wheel ──────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="filterwheel_connected",
        name="Filter Wheel Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:filter",
        value_fn=lambda d: bool(_safe(d, "filterwheel", "Response", "Connected")),
    ),

    # ── Guider ────────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="guider_connected",
        name="Guider Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:crosshairs",
        value_fn=lambda d: bool(_safe(d, "guider", "Response", "Connected")),
    ),
    NinaBinarySensorDescription(
        key="guider_is_guiding",
        name="Guider Active",
        icon="mdi:crosshairs-gps",
        value_fn=lambda d: _safe(d, "guider", "Response", "State") == "Guiding",
    ),

    # ── Dome ──────────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="dome_connected",
        name="Dome Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:home-circle",
        value_fn=lambda d: bool(_safe(d, "dome", "Response", "Connected")),
    ),
    NinaBinarySensorDescription(
        key="dome_shutter_open",
        name="Dome Shutter Open",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:home-circle-outline",
        # ShutterStatus: 0=Open, 1=Closed, 2=Opening, 3=Closing, 4=Error
        value_fn=lambda d: _safe(d, "dome", "Response", "ShutterStatus") == 0,
    ),

    # ── Sequence ──────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="sequence_running",
        name="Sequence Running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:play-circle",
        value_fn=lambda d: _safe(d, "sequence", "Response", "Status") == "Running",
    ),
]


class NinaBinarySensor(CoordinatorEntity[NinaDataCoordinator], BinarySensorEntity):
    """A binary sensor entity backed by the N.I.N.A. coordinator."""

    entity_description: NinaBinarySensorDescription

    def __init__(
        self,
        coordinator: NinaDataCoordinator,
        description: NinaBinarySensorDescription,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "N.I.N.A. Astrophotography",
            "manufacturer": "Nighttime Imaging 'N' Astronomy",
            "model": "Advanced API v2",
        }

    @property
    def is_on(self) -> bool | None:
        if self.entity_description.value_fn and self.coordinator.data:
            try:
                return self.entity_description.value_fn(self.coordinator.data)
            except Exception:  # noqa: BLE001
                return None
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NinaDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        NinaBinarySensor(coordinator, description, entry.entry_id)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )
