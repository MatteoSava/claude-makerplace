---
name: trmnl-terminus-ops
description: Operate self-hosted TRMNL or Terminus e-ink device workflows. Use when diagnosing API/device registration issues, repairing devices after server changes, managing screens/playlists, or publishing live e-ink screen content.
argument-hint: "[device or screen task]"
---

# TRMNL Terminus Ops

Use this skill for self-hosted TRMNL and Terminus operations. Treat device identifiers, host URLs, credentials, and API keys as secrets.

## Discovery

Collect:

- Terminus host URL.
- Admin login method.
- Device MAC or friendly ID, if needed.
- Device API key, if needed.
- Target playlist or screen.
- Existing CLI/scripts in the repository.

Do not paste real credentials into source files or shared docs.

## API Health Workflow

1. Authenticate to the admin API.
2. List models, devices, playlists, screens, and firmware.
3. Validate `/api/display` for the target device.
4. Validate `/api/setup` only with the headers expected by the firmware flow.
5. Record which layer failed: auth, model, device, playlist, screen, display, or setup.

## Device Repair Workflow

1. Match an existing device by ID, MAC, or friendly ID.
2. Patch the device record when a match exists.
3. Create a replacement record only when no safe match exists.
4. Reattach playlist or screen assignment.
5. Validate display output.
6. Ask for physical re-pairing only when server-side repair cannot restore the device.

## Screen Publishing Workflow

1. Preview locally in a browser.
2. Render at the target e-ink resolution.
3. Push once to verify.
4. Use watch mode or scheduled refresh only after a successful one-shot push.
5. Keep generated assets and API payloads deterministic.

## Expected Output

Return:

- API health result.
- Device repair action taken or recommended.
- Screen publish status.
- Remaining manual steps.
