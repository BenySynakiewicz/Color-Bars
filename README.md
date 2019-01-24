# Color Bars 1.1

A command-line application for generating the so-called *movie barcodes* of video files. Uses OpenCV for decoding and postprocessing images.

## Dependencies

- **OpenCV** (opencv-python).
- **NumPy** (numpy).

## Changelog

### Version 1.1

+ You can now pass multiple input files in a single command (i.e. "python color-bars.py 1.mp4 2.mp4").
+ You can now pass a text file with a list of input video file paths (i.e. "python color-bars.py 1.mp4 ListOfPaths.txt 2.mp4").
+ Improved the UI.

## Notes

Tested with **Python 3.7.2**, **OpenCV 4.0.0.21** and **NumPy 1.16.0**.