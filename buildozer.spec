[app]

# (str) Title of your application
title = Gneisswork

# (str) Package name
package.name = gneisswork

# (str) Package domain (needed for android/ios packaging)
package.domain = org.gneisswork

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,html,css,js,json

# (list) List of inclusions using pattern matching
source.include_patterns = sedmob/**/*,sedmob/templates/**/*,sedmob/static/**/*

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .git, .github, .venv, instance, __pycache__, .pytest_cache, docs, media, .archives, .claude, .dev, .kiro, .pwlw-sedmob, _layouts, .logs, .test, p4a-recipes

# (list) List of exclusions using pattern matching
source.exclude_patterns = */tests/*,*/test_*,*/.git/*,*/instance/*,Dockerfile,docker-compose.yml,CNAME,LICENSE,*.md,*.yml,*.yaml,*.spec,*.cfg,*.toml

# (str) Application versioning (method 1)
version = 0.1

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
# C-extension packages (markupsafe) must be listed explicitly so p4a
# uses its compiled recipe instead of attempting a pip install on-device.
requirements = python3,kivy,flask,werkzeug,jinja2,markupsafe,itsdangerous,click,blinker,flask-sqlalchemy,sqlalchemy,sqlite3,jnius,android

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/favicon.png

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 35

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 26b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a,armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# Debug keystore — use a persistent keystore so APK signatures stay
# consistent across CI builds, allowing in-place updates on devices.
# The CI workflow restores this from the DEBUG_KEYSTORE secret.
android.debug_keystore = ~/.android/debug.keystore
android.debug_keystore_passwd = android
android.debug_keyalias = androiddebugkey
android.debug_keyalias_passwd = android

# Use local recipe overrides (Flask 3.x instead of p4a's bundled 2.0.3)
p4a.local_recipes = ./p4a-recipes



[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .ipa) storage
# bin_dir = ./bin

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:key].
#    Each line will be considered as a option to the list.
#    Let's take [app] / source.exclude_patterns.
#    Instead of doing:
#
#[app]
#source.exclude_patterns = license,data/audio/*.wav,data/images/original/*
#
#    This can be translated into:
#
#[app:source.exclude_patterns]
#license
#data/audio/*.wav
#data/images/original/*
#

#    -----------------------------------------------------------------------------
#    Profiles
#
#    You can extend section / key with a profile
#    For example, you want to deploy a demo version of your application without
#    HD content. You could first change the title to add "(demo)" in the name
#    and extend the excluded directories to remove the HD content.
#
#[app@demo]
#title = My Application (demo)
#
#[app:source.exclude_patterns@demo]
#images/hd/*
#
#    Then, invoke the command line with the "demo" profile:
#
#buildozer --profile demo android debug
