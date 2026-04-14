#! /bin/bash

sudo apt update
sudo apt install build-essential flatpak flatpak-builder gnome-software-plugin-flatpak -y
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.gnome.Platform//48 org.gnome.Sdk//48


##
# in Unbound3D-slicer folder, run following command to build Orca
# # First time build
# flatpak-builder --state-dir=.flatpak-builder --keep-build-dirs --user --force-clean build-dir scripts/flatpak/com.unbound3d.Unbound3DSlicer.yml

# # Subsequent builds (only rebuilding Unbound3D-slicer)
# flatpak-builder --state-dir=.flatpak-builder --keep-build-dirs --user build-dir scripts/flatpak/com.unbound3d.Unbound3DSlicer.yml --build-only=Unbound3D-slicer