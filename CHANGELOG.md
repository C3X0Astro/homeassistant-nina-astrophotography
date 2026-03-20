# Changelog

All notable changes to the N.I.N.A. Astrophotography Home Assistant integration are documented here.

---

## [1.3.0] - 2026-03-20

### Added

#### Image streaming via Advanced API (`api.py`)
Added `get_image_bytes()` and `get_image_stream_url()` methods to `NinaApiClient`. The Advanced API v2.2.x serves JPEG frames directly at:

```
GET /v2/api/image?index=0&stream=true&useAutoStretch=true
```

`index=0` returns the most recent frame; `index=1` returns the one before it, and so on through history. `useAutoStretch=true` applies N.I.N.A.'s auto-stretch so the image is viewable without further processing.

#### HA Image entity — `image.nina_latest_captured_frame` (`image.py`)
A native Home Assistant `ImageEntity` that fetches JPEG bytes from the streaming endpoint on demand. Behaviour:
- Automatically marks itself updated the instant an `IMAGE-SAVE` WebSocket event fires — no polling delay
- Compatible with the built-in **Picture Entity Card** and any HA integration that reads image entities
- Returns cached bytes on network error so the last good frame remains visible after a brief disconnect
- `image_last_updated` timestamp advances on every new frame, triggering browser cache invalidation in frontend cards

Use in any standard HA card:
```yaml
type: picture-entity
entity: image.nina_latest_captured_frame
```

#### Image Panel Lovelace Card — `www/nina-image-panel-card.js`
A full-featured image viewer card fetching frames directly from the N.I.N.A. PC streaming endpoint.

**Features:**
- Live image display with auto-refresh on `nina_image_save` HA events
- Stats overlay on the image: filter name, HFR, star count, guide RMS string, target name
- Animated exposing indicator bar while `binary_sensor.camera_exposing` is `on`
- **ADU histogram** synthesised from `sensor.last_frame_min_adu`, `max_adu`, `mean_adu`, `median_adu` — shows approximate pixel distribution with mean (teal) and median (dashed) marker lines and a saturation warning zone
- **Stats row** below the image: HFR (green < 2px / amber > 3.5px), star count, mean ADU, exposure time
- **Recent frames strip**: last 6 thumbnails loaded at reduced quality (40%) for fast rendering, with filter labels overlaid; click any thumbnail to jump to that frame
- **Click-to-fullscreen**: click the image to open a modal showing the full-quality version
- Graceful no-image state with setup hint before the first frame is captured

**Card configuration:**
```yaml
type: custom:nina-image-panel-card
host: 192.168.1.100      # N.I.N.A. PC IP address (required)
port: 1888               # API port (default: 1888)
stretch: true            # Apply N.I.N.A. auto-stretch (default: true)
quality: 85              # JPEG quality 1–100 (default: 85)
show_strip: true         # Show recent frames strip (default: true)
show_histogram: true     # Show ADU histogram (default: true)
strip_count: 6           # Thumbnails in strip (default: 6)
refresh_on_save: true    # Auto-refresh on IMAGE-SAVE event (default: true)
```

> **Note:** The card fetches images directly from the N.I.N.A. PC, not proxied through HA. Your browser must be able to reach `host:port` on your local network. This works on a home LAN. For remote access outside your network, use a VPN.

> **Prerequisite:** Ensure **Create Thumbnails** is enabled in the Advanced API plugin settings in N.I.N.A. (it was visible as ON in the plugin screenshot).

#### Sky Map Lovelace Card — `www/nina-sky-map-card.js`
An all-sky stereographic projection showing live telescope pointing.

**Features:**
- Stereographic polar projection (standard planisphere view): zenith at centre, horizon as outer green ring, North at top
- Altitude rings at 15°/30°/45°/60°/75° with degree labels
- Dashed azimuth spokes every 45°, N/S/E/W compass labels
- **Star field**: 40 bright stars (Sirius through Polaris) projected from RA/Dec using the observer's latitude and the mount's sidereal time (`sensor.mount_sidereal_time`) — rotates correctly as the night progresses. Orion belt stars connected with faint constellation lines. Subtle Milky Way band
- **Meridian line**: dashed purple line. Pulses amber and shows countdown label when `sensor.mount_time_to_meridian_flip` < 15 minutes
- **Telescope reticle**: crosshair + circle at current Alt/Az position with soft glow. Colour reflects mount state — teal (tracking), amber (parked), orange-red (slewing)
- **Pointing trail**: last 60 positions drawn as a fading teal line
- Info row: altitude, azimuth, RA (h m s format), Dec (° ′ ″ format)
- Status bar: tracking / parked / slewing / disconnected state

**Card configuration:**
```yaml
type: custom:nina-sky-map-card
latitude: 38.5      # Your observing latitude — improves star field accuracy (default: 40)
trail_length: 60    # Historical positions in trail (default: 60)
map_size: 320       # Canvas diameter in px (default: 320)
```

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
