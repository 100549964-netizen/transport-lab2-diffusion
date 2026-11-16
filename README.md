# Laboratory II - Diffusion (UC3M)

This program measures relative dye concentration versus time (Part A) and versus distance (Part B) in a video of a Petri dish.

## Requirements
- Python 3.10 or later, with tkinter available (included in standard Windows Python installers)
- OpenCV and Matplotlib (install below)
- A video recorded with a fixed camera, plus a known physical dimension for calibration in Part B

## Installation
From this directory, open a terminal:

```powershell
py -m pip install -r requirements.txt
```

If the `py` launcher is unavailable, use your configured Python interpreter, e.g. `python -m pip install -r requirements.txt`.

## Run

```powershell
py analyze_diffusion.py
```

Select 1 (cold water), 2 (hot water), or 3 (reference video). Select the video file through the dialog. Then choose Part A or Part B. Return to the main menu after closing each figure; choose 0 to exit.

- **Part A:** input start/end times and the sampling interval; select a fixed ink ROI and a separate clear-water reference ROI. Results are a time-series CSV and plot.
- **Part B:** enter the actual physical Petri-dish diameter in cm; click two opposite points across the dish; confirm spatial calibration; input 3 or more frame times; select a horizontal strip across the dye and a separate reference ROI. Results are a spatial CSV and plot.

The program computes `C_relative = 1 - I_measurement / I_reference` from grayscale intensities. This is a dimensionless relative indicator, **not** absolute concentration in mol/L. Spatial coordinates are cm from the left edge of the selected strip.

## Files
- `analyze_diffusion.py`: complete Python code for both analyses
- `prompts.md`: chronological Copilot prompt history
- `results/`: saved CSV measurements and figures for the reference, cold, and hot videos

Each run writes to a timestamped folder under `results/reference`, `results/cold`, or `results/hot`. Previous results are not overwritten. Original videos are selected separately and must not be placed in this submission archive.

## Verification
The tool was tested on a supplied instructor reference video and a numerical example: I_measurement = 80, I_reference = 100 => C_relative = 0.20. Check your spatial calibration against the actual physical dimension used in the recording.
