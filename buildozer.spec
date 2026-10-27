[app]
title = Flappy Dragon
package.name = flappydragon
package.domain = org.dragon
source.dir = .
source.include_exts = py
source.exclude_dirs = .github, bin, .buildozer, out
version = 0.2.0
requirements = hostpython3==3.10.14,python3==3.10.14,pygame,pyjnius
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.jpg
android.presplash_color = #0B0A14
orientation = landscape
fullscreen = 1
android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
