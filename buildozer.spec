[app]
title = Startup Tycoon
package.name = startuptycoon
# Change the domain to one you own before publishing on Google Play (it is the app's unique id).
package.domain = com.startuptycoon

source.dir = .
source.include_exts = py,png,json,ttf,txt
source.include_patterns = locales/*.json,assets/*,assets/fonts/*
source.exclude_dirs = tests,tools,dist,web,build,bin,.github,.buildozer,__pycache__
source.exclude_patterns = *.ico,*.icns,favicon.png

version = 1.1.0
requirements = python3,pygame

orientation = landscape
fullscreen = 1
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/icon.png
presplash.color = #0F121C

android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
