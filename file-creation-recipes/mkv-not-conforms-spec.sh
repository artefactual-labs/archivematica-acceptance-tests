#!/bin/bash

# Create a test MKV file that does *not* conform to the MKV specification.
# MediaConch should indicate fail for a file generated via this ffmpeg command.
# Note: the non-conforming aspect is setting the video codec to libx264.

ffmpeg \
    -f lavfi \
    -i mandelbrot=s=720x540:r=29.97 \
    -f lavfi \
    -i aevalsrc="sin(10*2*PI*t)*sin(880*2*PI*t):c=stereo:s=48000" \
    -t 1 \
    -c:v libx264 \
    -b:v 3M \
    -vf setdar=4/3 \
    -c:a aac \
    -b:a 163840 \
    mkv-not-conforms-spec.mkv
