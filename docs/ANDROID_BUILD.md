---
layout: default
title: Android APK Build
---

# Building Gneisswork as an Android APK

Gneisswork can be packaged as a standalone Android APK using [Buildozer](https://buildozer.readthedocs.io/) and [Python for Android](https://python-for-android.readthedocs.io/).

## How It Works

The APK bundles:
- Python 3 runtime
- Flask web server
- Kivy (Android bootstrap only)
- All Gneisswork dependencies
- SQLite database

When launched, the app:
1. Starts a local Flask server in a background thread on `127.0.0.1:5000`
2. Polls until the server is ready
3. Replaces the Kivy surface with a native Android `WebView` (via pyjnius) displaying the Flask UI
4. Runs completely offline on the device

## Automated Builds (GitHub Actions)

The repository includes a GitHub Action workflow (`.github/workflows/build-apk.yml`) that automatically builds APKs:

### Triggers
- **Push to main/master**: Builds a debug APK
- **Pull requests**: Builds for testing
- **Version tags** (`v*`): Builds and creates a GitHub release
- **Manual dispatch**: Build on-demand from Actions tab

### Artifacts
- Debug APKs are uploaded as workflow artifacts (30-day retention)
- Release APKs are attached to GitHub releases for tagged versions

### Build Time
First build: ~30-45 minutes (downloads Android SDK/NDK)
Subsequent builds: ~10-15 minutes (with caching)

## Local Build (Linux/macOS)

### Prerequisites
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
  python3-pip build-essential git \
  libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
  libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
  zlib1g-dev autoconf automake libtool pkg-config cmake \
  openjdk-17-jdk

# Install Buildozer
pip install buildozer cython==3.0.11
```

### Build Commands
```bash
# Debug APK (includes debugging symbols, unsigned)
buildozer android debug

# Release APK (optimized, requires signing)
buildozer android release

# Clean build cache (if issues arise)
buildozer android clean
```

Output APK location: `bin/gneisswork-*.apk`

## Configuration

All build settings are in `buildozer.spec`:
- **App metadata**: Name, version, icon
- **Requirements**: Python packages to include
- **Permissions**: Android permissions (INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION)
- **Architecture**: Builds for ARM64 and ARMv7 by default
- **API levels**: Targets Android 14 (API 35), minimum Android 5.0 (API 21)

### Custom python-for-android Recipes

The `p4a-recipes/` directory contains local recipe overrides for python-for-android. These are referenced via `p4a.local_recipes = ./p4a-recipes` in `buildozer.spec` and take precedence over the recipes bundled with p4a.

Currently overridden:

| Recipe | Bundled Version | Local Version | Reason                         |
| ------ | --------------- | ------------- | ------------------------------ |
| Flask      | 2.0.3           | 3.1.1         | Gneisswork requires Flask 3.0+                    |
| SQLAlchemy | 1.3.3           | 2.0.40        | Flask-SQLAlchemy 3.x requires SQLAlchemy 2.0+     |
| Werkzeug   | (p4a default)   | 3.1.7         | Pinned for Flask 3.x compatibility                |

Each recipe is a Python class in `p4a-recipes/<package>/__init__.py` that extends `PythonRecipe`. Flask downloads source from GitHub and uses the default PythonRecipe install. Werkzeug and SQLAlchemy bypass the source-based workflow — they override `build_arch` to pip-install the wheel directly from PyPI into the target site-packages, because their modern versions use `pyproject.toml` which PythonRecipe cannot handle. If you need to pin or override another dependency for the APK build, add a new recipe following the same pattern.

## Installation

### From GitHub Actions
1. Go to Actions → Build Android APK workflow
2. Download the `gneisswork-debug-apk` artifact
3. Extract the `.apk` file
4. Transfer to Android device
5. Enable "Install from Unknown Sources" in Android settings
6. Install the APK

### From Release
1. Go to Releases page
2. Download the APK from the latest release
3. Install on device

## Troubleshooting

### Build Fails with "Command failed"
- Check system dependencies are installed
- Try `buildozer android clean` and rebuild
- Check `buildozer.spec` for typos

### APK Crashes on Launch
- Check logs: `adb logcat | grep python`
- Verify all requirements are listed in `buildozer.spec`
- Check file permissions in `source.include_patterns`

### Large APK Size
- Expected size: 50-80 MB (includes Python runtime)
- To reduce: exclude unused packages from requirements
- Use `buildozer android release` for optimized builds

### Database Issues
- The SQLite database is created in private app storage
- Data persists between app restarts
- To reset: clear app data in Android settings

## Development Workflow

1. Develop and test using `python run.py` (desktop Flask)
2. Commit changes to repository
3. Push to trigger automatic APK build
4. Download and test APK on device
5. Tag release (`git tag v1.0.0`) to create public release

## Notes

- First build downloads ~2GB of Android SDK/NDK components
- Build cache is stored in `.buildozer/` (git-ignored)
- The `main.py` file is the Android entry point (Kivy bootstrap → Flask thread → native Android WebView via pyjnius)
- The regular `run.py` is still used for desktop development
- WebView requires Android 5.0+ (API 21)
