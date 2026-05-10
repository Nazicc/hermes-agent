---
name: findmy
description: "Use when tracking Apple devices and AirTags via FindMy.app on macOS using AppleScript and screen capture. NOT for: non-Apple devices, Android tracking, or when FindMy app UI is more efficient."
category: general
version: 1.0.0
...
author: Hermes Agent
...
license: MIT
...
platforms: [macos]
---

---
name: findmy
description: "Use when tracking Apple devices and AirTags via FindMy.app on macOS using AppleScript and screen capture. NOT for: non-Apple devices, Android tracking, or when FindMy app UI is more efficient."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  sources: []
  hermes:
    tags: [FindMy, AirTag, location, tracking, macOS, Apple]
---

## Environment Requirements

- **macOS** required (AppleScript is macOS-only)
- **FindMy.app** must be installed and signed in
- **Screen recording permission** required in System Preferences > Security & Privacy > Privacy
- **Accessibility permission** may be required for AppleScript execution

## How It Works

1. **AppleScript automation** opens FindMy.app and navigates to the target device
2. **Screen capture** captures the current location display
3. **OCR/text extraction** parses the location data from the screenshot
4. **Structured output** returns device name, location coordinates, last seen time, and battery level

## Tools

- **AppleScript** — Interact with FindMy.app via `osascript`
- **screencapture** — Capture FindMy UI state for parsing

## Usage

**Trigger signals:**
- "Find my iPhone/Mac/iPad/AirTag"
- "Track my Apple device"
- "Where is my [device]"
- "Locate my AirTag or lost Apple device"
- "Get alerts when items are left behind"
- "FindMy location"
- Any variant involving Apple device location services

**Anti-trigger signals:**
- Android or non-Apple device tracking
- Real-time GPS navigation (use Apple Maps instead)
- Web-based FindMy usage (native app is faster)
- Emergency location services (use Find My Friends / dedicated emergency services)

## Limitations & Notes

- Requires physical access or iCloud credentials to the target device
- Location updates depend on device connectivity (online devices update in real-time; offline devices show last known location)
- AirTag location requires the AirTag to be in Bluetooth range of any Apple device in the Find My network
- Works offline if device was recently located
- Rate limiting may occur if too many queries are made in short succession
- Screen capture parsing is fragile to UI changes — verify selectors match your macOS version
- This tool is for on-demand queries, not continuous location logging
