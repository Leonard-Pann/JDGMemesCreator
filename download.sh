#!/bin/sh

set -e

mkdir -p videos videos/raw

# Download the raw videos
cd videos/raw
yt-dlp --format mp4 https://www.youtube.com/@joueurdugrenier

# Remove the suffix that yt-dlp adds for no reason
for video in *.{mp4,mkv,webm}; do
	newname=${video// \[*\]./.}
	if [ ! -f "$newname" ]; then
		mv "$video" "$newname"
	fi
done

cd ..

# Convert whatever shitty format we got to mp4
cp raw/*.mp4 .
for video in raw/*.{mkv,webm}; do
	filename=$(basename "$video")
	converted=${filename/".mkv"/".mp4"}
	converted=${filename/".webm"/".mp4"}
	if [ ! -f "$converted" ]; then
		echo "CONVERTING: $converted"
		ffmpeg -loglevel warning -y -i "$video" "$converted"
	else
		echo "SKIPPING:   $converted"
	fi
done
