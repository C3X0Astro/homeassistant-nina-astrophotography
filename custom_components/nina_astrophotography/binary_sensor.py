"""Binary sensors for N.I.N.A. Astrophotography — corrected for v2.2.15 API."""
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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NinaDataCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class NinaBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Any = None


def _safe(data, *keys, default=None):
    d = data
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


def _bool(data, *keys):
    """Return bool from nested key, treating None/missing as False."""
    v = _safe(data, *keys)
    if v is None:
        return False
    return bool(v)


BINARY_SENSOR_DESCRIPTIONS: list[NinaBinarySensorDescription] = [

    # ── Camera ────────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="camera_connected",
        name="Camera Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:camera",
        value_fn=lambda d: _bool(d, "camera", "Response", "Connected"),
    ),
    NinaBinarySensorDescription(
        key="camera_cooling_enabled",
        name="Camera Cooling",
        icon="mdi:snowflake",
        # API key confirmed: "CoolerOn"
        value_fn=lambda d: _bool(d, "camera", "Response", "CoolerOn"),
    ),
    NinaBinarySensorDescription(
        key="camera_exposing",
        name="Camera Exposing",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:camera-burst",
        # API key confirmed: "IsExposing"
        value_fn=lambda d: _bool(d, "camera", "Response", "IsExposing"),
    ),

    # ── Mount ─────────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="mount_connected",
        name="Mount Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:telescope",
        value_fn=lambda d: _bool(d, "mount", "Response", "Connected"),
    ),
    NinaBinarySensorDescription(
        key="mount_parked",
        name="Mount Parked",
        icon="mdi:parking",
        # API key: "AtPark"
        value_fn=lambda d: _bool(d, "mount", "Response", "AtPark"),
    ),
    NinaBinarySensorDescription(
        key="mount_tracking",
        name="Mount Tracking",
        icon="mdi:orbit",
        # API key: "TrackingEnabled"
        value_fn=lambda d: _bool(d, "mount", "Response", "TrackingEnabled"),
    ),
    NinaBinarySensorDescription(
        key="mount_slewing",
        name="Mount Slewing",
        device_class=BinarySensorDeviceClass.MOVING,
        icon="mdi:rotate-3d-variant",
        value_fn=lambda d: _bool(d, "mount", "Response", "Slewing"),
    ),
    NinaBinarySensorDescription(
        key="mount_at_home",
        name="Mount At Home",
        icon="mdi:home",
        value_fn=lambda d: _bool(d, "mount", "Response", "AtHome"),
    ),

    # ── Focuser ───────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="focuser_connected",
        name="Focuser Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:focus-field",
        value_fn=lambda d: _bool(d, "focuser", "Response", "Connected"),
    ),
    NinaBinarySensorDescription(
        key="focuser_is_moving",
        name="Focuser Moving",
        device_class=BinarySensorDeviceClass.MOVING,
        icon="mdi:arrow-expand-horizontal",
        value_fn=lambda d: _bool(d, "focuser", "Response", "IsMoving"),
    ),

    # ── Filter Wheel ──────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="filterwheel_connected",
        name="Filter Wheel Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:filter",
        value_fn=lambda d: _bool(d, "filterwheel", "Response", "Connected"),
    ),

    # ── Guider ────────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="guider_connected",
        name="Guider Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:crosshairs",
        value_fn=lambda d: _bool(d, "guider", "Response", "Connected"),
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
        value_fn=lambda d: _bool(d, "dome", "Response", "Connected"),
    ),
    NinaBinarySensorDescription(
        key="dome_shutter_open",
        name="Dome Shutter Open",
        device_class=BinarySensorDeviceClass.OPENING,
        icon="mdi:home-circle-outline",
        # ShutterStatus: 0=Open, 1=Closed, 2=Opening, 3=Closing, 4=Error
        value_fn=lambda d: _safe(d, "dome", "Response", "ShutterStatus") == 0,
    ),

    # ── Flat Device ───────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="flatdevice_connected",
        name="Flat Device Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:lightbulb",
        value_fn=lambda d: _bool(d, "flatdevice", "Response", "Connected"),
    ),

    # ── Sequence ──────────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="sequence_running",
        name="Sequence Running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:play-circle",
        value_fn=lambda d: _safe(d, "sequence", "Response", "Status") == "Running",
    ),

    # ── Weather station ───────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="weather_connected",
        name="Weather Station Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:weather-partly-cloudy",
        value_fn=lambda d: _bool(d, "weather", "Response", "Connected"),
    ),

    # ── Safety monitor ────────────────────────────────────────────────────
    NinaBinarySensorDescription(
        key="safetymonitor_connected",
        name="Safety Monitor Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        icon="mdi:shield-check",
        value_fn=lambda d: _bool(d, "safetymonitor", "Response", "Connected"),
    ),
    NinaBinarySensorDescription(
        key="safetymonitor_is_safe",
        name="Observatory Safe",
        device_class=BinarySensorDeviceClass.SAFETY,
        icon="mdi:shield-check-outline",
        # IsSafe=True means conditions are SAFE (binary_sensor "on" = problem by HA convention
        # for SAFETY class, but we invert: on = safe so the icon makes sense in dashboards)
        # Using SAFETY device class: on = unsafe. We flip: store !IsSafe so "on" means UNSAFE
        # so HA's red alert icon fires correctly when conditions turn bad.
        value_fn=lambda d: not _bool(d, "safetymonitor", "Response", "IsSafe"),
    ),
]


class NinaBinarySensor(CoordinatorEntity[NinaDataCoordinator], BinarySensorEntity):
    entity_description: NinaBinarySensorDescription

    def __init__(self, coordinator, description, entry_id):
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
    def is_on(self):
        if self.entity_description.value_fn and self.coordinator.data:
            try:
                return self.entity_description.value_fn(self.coordinator.data)
            except Exception:
                return None
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        NinaBinarySensor(coordinator, description, entry.entry_id)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )
