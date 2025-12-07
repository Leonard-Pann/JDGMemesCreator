#!/bin/sh

set -e

mkdir -p videos && cd videos
yt-dlp https://www.youtube.com/@joueurdugrenier
