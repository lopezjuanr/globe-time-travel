# Changelog

This document records the complete development history of the interactive tectonic time-travel viewer in `time-travel.html`. It covers the viewer’s user-facing behavior and its supporting client-side architecture. The repository’s earlier film-rendering assets and production scripts retain their detailed history in Git; they are outside the scope of this page.

The viewer remains a standalone, dependency-free HTML page. It reconstructs present-day pin locations and coastlines against the Merdith2021 plate model through the GPlates Web Service.

## 2026-08-12 — Safer placement and clearer names

### Automatic geographic labels

Map clicks now name a pin after the country containing the selected present-day coordinate instead of assigning a generic sequential name. The page embeds a compact, simplified Natural Earth country-boundary dataset, so country lookup happens locally without an additional request. Its point-in-polygon lookup accounts for holes and disambiguates repeated country labels, such as `Brazil (2)`. A click in open water is labeled `Open ocean`, which also gives the user useful context for a location that may be reconstructed as subducted at deep time. The country data was checked against 37 reference locations in Python and 11 browser checks, including every preset city. [7]

### Placement lock during animation

Pin creation is now disabled while geological-time animation is running. A newly created pin would otherwise lack a reconstruction for the frame currently on screen and could appear at its present-day position against ancient coastlines. Existing pins remain selectable, but map clicks show a clear instruction to stop the animation before placing another pin. The quick-add grid is replaced by an explanatory paused-state message and its buttons are disabled as a second safeguard. [8]

### Color-linked quick-add controls

A quick-add city button now takes on the colour of its existing pin. The coloured border, label, and subtle glow keep the city button, sidebar list, and plotted pin visually aligned. Selecting a city that is already pinned selects its existing pin rather than creating a duplicate. Removing a pin or clearing the list resets the related button state. [8]

## 2026-08-10 — Geological display accuracy and map redesign

### Initial interactive time-travel viewer

The project gained `time-travel.html`, a self-contained browser viewer for placing pins on present-day locations and reconstructing them from 0 to 1,000 million years ago (Ma). The initial release used a Three.js globe, the GPlates Web Service `reconstruct_points` endpoint, and the Merdith2021 plate model. It added ten quick-add cities, time scrubbing, automatic animation, dynamically reconstructed coastlines, and visual drift paths. [1]

### Animation pacing and stale-request protection

The first animation update replaced a fixed 200-millisecond interval with a step-and-wait loop. Each geological-time step now waits for both coastlines and pin reconstructions before it continues, then pauses long enough for the state to be visible. The step size became 10 Ma. Coastline requests also gained cancellation and staleness guards, preventing delayed responses from drawing out-of-date coastlines over the current scene. [2]

### Flat equirectangular map and faster coastline drawing

The viewer moved from a 3D globe to a full-viewport Plate Carrée, or equirectangular, map with a 30-degree graticule. Rendering now uses Canvas 2D rather than creating large numbers of Three.js geometries. A client-side Douglas–Peucker simplification pass reduces coastline coordinates before rendering, preserving map-scale visual detail while reducing drawing work. The coastline loader caches results, shares duplicate in-flight requests, and prefetches upcoming 10 Ma frames. [3]

### Atomic coastline and pin updates

The display pipeline was tightened so a pin cannot move to a reconstructed position until the matching reconstructed coastlines are ready to draw. The map keeps the last complete geological frame on screen during loading and then swaps coastlines and pin positions together in one redraw. Follow-up fixes removed other code paths that could reposition a pin early after a click, preset selection, or background data arrival. This prevents a land pin from temporarily appearing in the ocean while its corresponding coastlines are still loading. [3] [4]

### Per-pin colours and subduction explanation

Pins now cycle through ten high-contrast colours: red, orange, yellow, green, cyan, indigo, pink, amber, teal, and violet. The selected colour is applied consistently to the map marker, glow, sidebar dot, and label. When a reconstruction returns no past coordinate for a pin at a displayed time greater than zero, the map shows a colour-matched banner that identifies the affected location and explains that it was oceanic crust at that time and has since subducted. The banner disappears when no locations meet that condition or when the display returns to the present day. [5]

### Drift trails removed

The coloured dashed drift trails were removed from the map. This leaves the coastline, current reconstructed pin position, and subduction notice as the primary visual elements, reducing clutter during time travel. [6]

## Current viewer behavior

At the current revision, users can add a pin by clicking the present-day map or by selecting one of ten city presets. Every pin receives a distinct, vibrant colour and a meaningful country or open-ocean label. The user can scrub or animate geological time, while the page fetches and caches reconstructed coastlines and locations. The displayed frame remains internally consistent: pins stay on the last complete frame until their next coastline and reconstruction data have both arrived. Locations with no reconstructable continental position at deep time are described in the on-map subduction notice.

## References

[1]: https://github.com/lopezjuanr/globe-time-travel/commit/04ee6cbef3c8ff667d12948094ee4673c2d2cb23 "Add interactive tectonic time-travel globe viewer"
[2]: https://github.com/lopezjuanr/globe-time-travel/commit/e4928e05583e855d93826b3d4403b92172da87c4 "Fix animation: step-and-wait + abort stale coastline fetches"
[3]: https://github.com/lopezjuanr/globe-time-travel/commit/c2eda3f27ae3f88cdc9d69dee1ded9e79eda17df "Rebuild as flat map with atomic pin+coastline swap and faster rendering"
[4]: https://github.com/lopezjuanr/globe-time-travel/commit/67b998afbf153e34e76d9e707c7140239a77a77a "Fix: pins never move before matching coastlines are drawn"
[5]: https://github.com/lopezjuanr/globe-time-travel/commit/d767c8bf4bfd793f9222b77df33fe498f498a527 "Add per-pin colors and subduction banner"
[6]: https://github.com/lopezjuanr/globe-time-travel/commit/592918a9fa976c6ea0fd6dde9314df9f4b26d220 "Remove drift trails from map"
[7]: https://github.com/lopezjuanr/globe-time-travel/commit/187c316fb4408347db8e5ab04866f74ea2eefa2b "Auto-label pins with the country they fall in"
[8]: https://github.com/lopezjuanr/globe-time-travel/commit/16e4776f1fc65498136ce15a8e4a88889d09d637 "Lock pin placement during animation; tint quick-add buttons with pin colour"
