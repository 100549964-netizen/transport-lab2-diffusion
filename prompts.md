# Prompts

## 1. Video selection and inspection

**LABORATORY 2 — PROMPT 1: Video selection and inspection**

Create a Python program called `analyze_diffusion.py` for Transport Phenomena Laboratory 2: Diffusion.

The experiment compares ink diffusion in hot and cold water.

For this first step, implement ONLY:

1. A menu to choose Cold water, Hot water, or Reference video.
2. A Windows file selection dialog to open the corresponding original video from any folder.
3. Use OpenCV to read and display the video's FPS, duration, frame count, and resolution.
4. Display one frame using Matplotlib so I can check that the ink and Petri dish are visible.
5. Handle invalid files and cancelled selections safely.
Use Python, OpenCV, Matplotlib and tkinter. Keep the code simple and readable.

Do not calculate concentration, perform spatial calibration, or generate graphs yet. Do not modify any Laboratory 1 files or install additional packages.

## 2. Preview frame at 10 seconds

Modify `analyze_diffusion.py` so that the video preview displays the frame at 10 seconds instead of the first frame.

Use the actual video FPS to calculate the frame index, and display the image with correct RGB colors.

If the video is shorter than 10 seconds, use an available frame.

Preserve all existing functionality. Do not add concentration calculations or other features yet. Do not modify the original videos.

## 3. Relative concentration versus time

**LABORATORY 2 — PROMPT 3: Relative concentration versus time**

Modify the existing `analyze_diffusion.py` to implement Part A of Laboratory 2: relative ink concentration versus time.

Preserve the working video selection, metadata inspection and 10-second preview.

Requirements:

1. After opening the video, allow the user to choose the video start time and end time for analysis, in seconds.
2. Display a frame at the selected start time and allow the user to manually select TWO rectangular regions:

- Measurement ROI: a fixed region containing the ink.
- Reference ROI: a separate region containing clear water inside the Petri dish, away from reflections and the ink.
3. Display both selected regions and ask for confirmation before starting the analysis.
4. Sample video frames at a user-selected time interval, with a default of 5 seconds. Use the video's original FPS to obtain correct timestamps.
5. Convert each sampled frame to grayscale using OpenCV.
6. Calculate the average grayscale intensity in both fixed regions for every sampled frame.
7. Calculate relative concentration using:

C_relative(t) = 1 - I_measurement(t) / I_reference(t)
8. Keep the calculated values without artificially clipping negative results. Warn if the reference intensity is zero or if the reference region becomes contaminated.
9. Generate a graph of relative concentration versus time, with:

- X-axis: Time (s)
- Y-axis: Relative concentration (dimensionless)
- Clear title and circular data markers.
10. Save the measurements as a CSV containing time, measurement intensity, reference intensity and relative concentration.
11. Save the graph as a PNG.
12. Store outputs in a uniquely named folder under `results/reference/`, `results/cold/` or `results/hot/` according to the selected experiment. Never overwrite previous results.
13. Verify the calculation independently: if I_measurement = 80 and I_reference = 100, C_relative must equal 0.20.
14. Handle invalid time intervals, cancelled ROI selection and unreadable frames safely.
IMPORTANT:

- Implement ONLY concentration versus time.
- Do NOT implement concentration versus position yet.
- Do NOT calculate a diffusion coefficient.
- Do NOT modify the original videos or Laboratory 1 files.
- Keep the program simple and beginner-friendly.
- Append this instruction to `prompts.md` as Prompt 3.
After implementing, explain briefly how to test this analysis on the reference video.

## 4. Spatial calibration

**LABORATORY 2 — PROMPT 4: Spatial calibration**

Modify `analyze_diffusion.py` to add spatial calibration for Part B of Laboratory 2.

The Petri dish in the professor's reference video has a known diameter of **9 cm**.

Requirements:

1. Keep all existing functionality, especially the completed concentration-versus-time analysis (Part A).
2. After selecting a video, allow the user to choose between Part A (concentration versus time) and Part B (concentration versus distance).
3. For Part B, display a clear video frame and ask the user to click two opposite points on the Petri dish diameter.
4. Use the distance between these points in pixels and the known physical diameter of 9 cm to calculate the calibration factor in cm/pixel.
5. Display the selected points, the measured pixel diameter and the calibration factor for confirmation.
6. Allow the user to repeat the selection if the points are incorrect.
7. Make the physical diameter editable, because the student's own videos may use a different Petri dish.
8. Do not implement the concentration-versus-distance calculations yet.
9. Do not modify the original videos or previously saved results.
10. Append this instruction to `prompts.md` as Prompt 4.
Keep the interface simple and beginner-friendly.

## 5. Relative concentration versus distance

**LABORATORY 2 — PROMPT 5: Relative concentration versus distance**

Extend the existing Part B in `analyze_diffusion.py` to calculate relative ink concentration versus distance.

Preserve Part A and the existing spatial calibration functionality.

Requirements:

1. After the user accepts the Petri dish calibration, continue directly to the spatial concentration analysis.
2. Allow the user to enter at least three different video times in seconds. Suggested default times for the reference video: 10, 60 and 180 seconds.
3. Display a frame showing the ink and let the user select one horizontal rectangular strip crossing the ink. Keep this strip at the same image coordinates for all selected times.
4. Let the user select a separate reference ROI containing clear water inside the Petri dish.
5. Display both regions and ask for confirmation.
6. For each selected time:

- Read the correct video frame using FPS.
- Convert it to grayscale.
- Calculate the mean grayscale intensity along the strip, averaging across its vertical thickness.
- Calculate the mean grayscale intensity of the clear-water reference ROI.
- Calculate relative concentration at every horizontal position using C_relative = 1 - I_strip / I_reference.
7. Convert the horizontal pixel positions along the strip to centimeters using the previously accepted calibration factor. Use the left edge of the strip as distance zero.
8. Plot all concentration-versus-distance curves on the SAME graph, with a separate labeled curve for each time.
9. Label the axes:

- X: Distance (cm)
- Y: Relative concentration (dimensionless)
10. Save a CSV containing time, distance, strip intensity, reference intensity and relative concentration.
11. Save the graph as a PNG in a new timestamped `results/reference/`, `results/cold/` or `results/hot/` folder.
12. Do not artificially clip concentration values. Handle invalid selections and unreadable frames safely.
13. Do not calculate the diffusion coefficient.
14. Do not modify the original videos or previous results.
15. Append this instruction to `prompts.md` as Prompt 5.
Keep the implementation simple and explain how to test Part B with the professor's reference video.

## 6. Improve program navigation

**LABORATORY 2 — PROMPT 6: Improve program navigation**

Improve the user experience in `analyze_diffusion.py`.

Currently, I need to press Ctrl+C and restart the script between analyses.

Please make these changes:

1. After completing Part A or Part B and closing any graph windows, automatically return to the main menu.
2. Allow the user to select another video and another analysis without restarting Python.
3. Add an option `0. Exit program` to close the application normally.
4. Ensure all video files and graph windows are properly closed between analyses.
5. Handle cancelled selections gracefully by returning to the menu.
6. Keep ALL existing calculations, calibration, graphs, CSV outputs and results unchanged.
7. Do not modify or delete any previously saved results.
8. Append this instruction to `prompts.md` as Prompt 6.
Make only the changes necessary to improve navigation. Do not redesign the program.
