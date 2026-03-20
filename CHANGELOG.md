# Changelog

All notable changes to the N.I.N.A. Astrophotography Home Assistant integration are documented here.

---

## [1.2.0] - 2026-03-20

### Added

#### Per-frame image statistics (`frame_statistics.py`, `frame_stats_sensor.py`)
The integration now maintains a live in-memory ring buffer of every frame saved by N.I.N.A. during the current session, populated in real time from `IMAGE-SAVE` WebSocket events. This is entirely push-driven — sensors update the instant a frame lands, with no polling delay.

**23 new sensor entities:**

| Entity | Description |
|---|---|
| `sensor.last_frame_hfr` | Half-flux radius of the most recent frame |
| `sensor.last_frame_hfr_std_dev` | HFR standard deviation across detected stars |
| `sensor.last_frame_stars` | Star count detected in the most recent frame |
| `sensor.last_frame_mean_adu` | Mean ADU of the most recent frame |
| `sensor.last_frame_median_adu` | Median ADU of the most recent frame |
| `sensor.last_frame_min_adu` | Minimum ADU (sky background indicator) |
| `sensor.last_frame_max_adu` | Maximum ADU (saturation indicator) |
| `sensor.last_frame_adu_std_dev` | ADU standard deviation |
| `sensor.last_frame_filter` | Filter used for the most recent frame |
| `sensor.last_frame_exposure` | Exposure duration of the most recent frame |
| `sensor.last_frame_guide_rms` | Guide RMS string at the time of capture |
| `sensor.last_frame_target` | Target name from the most recent frame |
| `sensor.rolling_avg_hfr_10` | Rolling average HFR over the last 10 frames |
| `sensor.rolling_avg_stars_10` | Rolling average star count over the last 10 frames |
| `sensor.rolling_avg_adu_10` | Rolling average mean ADU over the last 10 frames |
| `sensor.frame_session_count` | Total frames captured this session |
| `sensor.session_integration_time` | Total integration time in minutes |
| `sensor.session_avg_hfr` | Session-wide average HFR |
| `sensor.session_best_hfr` | Best (lowest) HFR recorded this session |
| `sensor.session_worst_hfr` | Worst (highest) HFR recorded this session |
| `sensor.session_avg_stars` | Session-wide average star count |
| `sensor.hfr_trend` | Focus quality trend: `improving`, `degrading`, or `stable` |
| `sensor.hfr_trend_delta` | Numeric HFR delta (last 5 vs previous 5 frames; negative = improving) |
| `sensor.frames_per_filter` | Total frame count with per-filter breakdown in extra attributes |
| `sensor.frame_sparkline_data` | 30-point sparkline arrays in extra attributes (used by the card) |

**New behaviour:**
- Session stats automatically reset when a `SEQUENCE-STARTING` WebSocket event is received
- All frame sensors use `RestoreEntity` — last known values survive HA restarts
- Ring buffer holds up to 500 frames before oldest are dropped

#### Frame Statistics Lovelace Card (`www/nina-frame-stats-card.js`)
A new custom card providing a live per-session imaging dashboard:
- KPI row: last HFR vs rolling average, star count, exposure and filter
- HFR trend chip with numeric delta and colour-coded border (green = improving, red = degrading)
- Session average and best HFR summary
- Three canvas sparkline charts: HFR (with dashed average line), star count, mean ADU — each point colour-coded by the filter used
- Per-filter frame count chips with matching colours
- Graceful empty state before the first frame arrives

Add to a dashboard with:
```yaml
type: custom:nina-frame-stats-card
```

---

## [1.1.0] - 2026-03-20

### Fixed

#### Endpoint paths corrected for N.I.N.A. Advanced API v2.2.x (`api.py`)
All equipment info endpoints were returning 404. The v2.2.x plugin requires an `/info` suffix on every equipment path. Updated all endpoints:

| Old path | Corrected path |
|---|---|
| `/equipment/camera` | `/equipment/camera/info` |
| `/equipment/telescope` | `/equipment/telescope/info` |
| `/equipment/focuser` | `/equipment/focuser/info` |
| `/equipment/filterwheel` | `/equipment/filterwheel/info` |
| `/equipment/guider` | `/equipment/guider/info` |
| `/equipment/rotator` | `/equipment/rotator/info` |
| `/equipment/dome` | `/equipment/dome/info` |
| `/equipment/flatdevice` | `/equipment/flatdevice/info` |

#### Response key names corrected (`sensor.py`, `number.py`)
Several sensor key paths did not match the actual API response structure:

- `TemperatureSetPoint` → `TargetTemp` (camera cooling setpoint sensor and number entity)
- `Temperature` and `CoolerPower` now handle `"NaN"` string values returned when the sensor is unavailable — these correctly resolve to `unknown` rather than surfacing `NaN`
- `Gain` and `Offset` values of `-1` (returned when camera is not connected) now resolve to `unknown` rather than `-1`

#### JSON content-type handling (`api.py`)
Added `content_type=None` to all `resp.json()` calls to prevent parse failures when the API returns `text/plain` or omits the content-type header.

### Added

#### New binary sensors (`binary_sensor.py`)
- `binary_sensor.camera_exposing` — true while a capture is in progress (`IsExposing` key)
- `binary_sensor.mount_at_home` — true when mount is at home position (`AtHome` key)
- `binary_sensor.flatdevice_connected` — flat device connectivity

#### New diagnostic sensors (`sensor.py`)
- `sensor.camera_name` — connected camera device name
- `sensor.focuser_step_size` — focuser step size in micrometres

---

## [1.0.0] - 2026-03-20

### Added
- Initial release
- Full N.I.N.A. Advanced API v2 support via REST polling and WebSocket push events
- 22 measurement and status sensors (camera temperature, guiding RMS, mount coordinates, sequence progress, image statistics)
- 14 binary sensors (equipment connectivity, mount state, guider state, dome shutter, sequence running)
- 7 controllable number entities (camera gain, offset, binning, cooling setpoint, focuser position, filter slot, rotator position)
- 4 switches (camera cooler, mount tracking, autoguiding, flat panel light)
- 2 select entities (active filter by name, mount tracking rate)
- 1 light entity (flat panel with HA brightness control)
- 13 button entities for one-tap actions (park, unpark, auto focus, dither, sequence start/stop, dome open/close, etc.)
- 20 registered HA services for full rig control
- Persistent WebSocket connection with automatic reconnect and exponential backoff
- Every N.I.N.A. event fires a native HA event for automation triggers
- UI config flow with connection validation
- Options flow for adjustable poll interval (5–300 seconds)
- 4 automation blueprints: session startup, session shutdown, guiding quality alert, meridian flip warning
- Custom `nina-observatory-card.js` Lovelace card with equipment status, mount coordinates, guiding RMS bars, image stats, and one-tap control buttons
