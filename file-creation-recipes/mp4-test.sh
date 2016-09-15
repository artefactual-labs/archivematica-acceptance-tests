#!/bin/bash

# Create an MP4 test file that can be used as the original for testing that
# normalization to MKV works.

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
    mp4-test.mp4
