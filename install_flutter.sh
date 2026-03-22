#!/bin/bash
cd /home/adiroyroy143/.openclaw/workspace
if [ ! -d "flutter" ]; then
    echo "Downloading Flutter..."
    curl -O https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.19.4-stable.tar.xz
    echo "Extracting Flutter..."
    tar xf flutter_linux_3.19.4-stable.tar.xz
    rm flutter_linux_3.19.4-stable.tar.xz
fi
echo "Flutter installation complete."
