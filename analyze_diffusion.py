import csv
import math
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import cv2
import matplotlib.pyplot as plt


EXPERIMENTS = {
    "1": ("Cold water", "cold"),
    "2": ("Hot water", "hot"),
    "3": ("Reference video", "reference"),
}
REFERENCE_CONTAMINATION_DROP = 0.10


def relative_concentration(measurement_intensity, reference_intensity):
    if reference_intensity == 0:
        return None
    return 1 - measurement_intensity / reference_intensity


def read_frame(capture, frame_index):
    if not capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index):
        return None
    success, frame = capture.read()
    return frame if success else None


def get_analysis_times(duration, fps):
    while True:
        try:
            start_time = float(input("Analysis start time in seconds: "))
            end_time = float(input("Analysis end time in seconds: "))
            interval = float(input("Sampling interval in seconds [5]: ") or "5")
        except ValueError:
            print("Enter valid numbers for the start time, end time, and interval.")
            continue

        if not all(math.isfinite(value) for value in (start_time, end_time, interval)):
            print("Times and interval must be finite numbers.")
        elif start_time < 0 or end_time <= start_time or end_time > duration:
            print(f"Use times with 0 <= start < end <= {duration:.2f} seconds.")
        elif interval < 1 / fps:
            print(f"The interval must be at least one frame ({1 / fps:.4f} seconds).")
        else:
            return start_time, end_time, interval


def select_roi(title, frame):
    try:
        x, y, width, height = cv2.selectROI(
            title, frame, showCrosshair=True, fromCenter=False
        )
    except cv2.error as error:
        print(f"Could not open the ROI selection window: {error}")
        return None
    finally:
        cv2.destroyAllWindows()

    roi = (int(x), int(y), int(width), int(height))
    if roi[2] == 0 or roi[3] == 0:
        return None
    return roi


def roi_crop(frame, roi):
    x, y, width, height = roi
    return frame[y : y + height, x : x + width]


def roi_fits_frame(frame, roi):
    x, y, width, height = roi
    frame_height, frame_width = frame.shape[:2]
    return (
        x >= 0
        and y >= 0
        and x + width <= frame_width
        and y + height <= frame_height
    )


def rois_overlap(first, second):
    first_x, first_y, first_width, first_height = first
    second_x, second_y, second_width, second_height = second
    return (
        first_x < second_x + second_width
        and first_x + first_width > second_x
        and first_y < second_y + second_height
        and first_y + first_height > second_y
    )


def show_selected_rois(frame, measurement_roi, reference_roi):
    measurement_rgb = cv2.cvtColor(roi_crop(frame, measurement_roi), cv2.COLOR_BGR2RGB)
    reference_rgb = cv2.cvtColor(roi_crop(frame, reference_roi), cv2.COLOR_BGR2RGB)

    figure, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(measurement_rgb)
    axes[0].set_title("Measurement ROI (ink)")
    axes[1].imshow(reference_rgb)
    axes[1].set_title("Reference ROI (clear water)")
    for axis in axes:
        axis.axis("off")
    figure.tight_layout()
    plt.show()


def get_physical_diameter():
    while True:
        try:
            diameter = float(
                input("Petri dish diameter in cm [9]: ") or "9"
            )
        except ValueError:
            print("Enter a valid number for the dish diameter.")
            continue

        if math.isfinite(diameter) and diameter > 0:
            return diameter
        print("The dish diameter must be a positive, finite number.")


def calibrate_spatial_scale(frame):
    physical_diameter = get_physical_diameter()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    while True:
        figure, axis = plt.subplots()
        axis.imshow(frame_rgb)
        axis.set_title(
            "Click two opposite points on the Petri dish diameter"
        )
        axis.axis("off")
        figure.tight_layout()
        plt.show(block=False)
        points = plt.ginput(2, timeout=0, show_clicks=True)
        plt.close(figure)

        if len(points) != 2:
            retry = input("Two points were not selected. Try again? [y/n]: ")
            if retry.strip().lower() in ("y", "yes"):
                continue
            return None

        first_point, second_point = points
        pixel_diameter = math.hypot(
            second_point[0] - first_point[0],
            second_point[1] - first_point[1],
        )
        if pixel_diameter == 0:
            print("The points must be different. Please select them again.")
            continue

        calibration_factor = physical_diameter / pixel_diameter
        confirmation_figure, confirmation_axis = plt.subplots()
        confirmation_axis.imshow(frame_rgb)
        confirmation_axis.plot(
            [first_point[0], second_point[0]],
            [first_point[1], second_point[1]],
            "ro-",
        )
        confirmation_axis.annotate(
            "Point 1",
            first_point,
            color="yellow",
            xytext=(5, 5),
            textcoords="offset points",
        )
        confirmation_axis.annotate(
            "Point 2",
            second_point,
            color="yellow",
            xytext=(5, 5),
            textcoords="offset points",
        )
        confirmation_axis.set_title(
            f"Diameter: {pixel_diameter:.2f} pixels; "
            f"calibration: {calibration_factor:.6f} cm/pixel"
        )
        confirmation_axis.axis("off")
        confirmation_figure.tight_layout()
        plt.show()

        print(f"Point 1: ({first_point[0]:.1f}, {first_point[1]:.1f}) pixels")
        print(f"Point 2: ({second_point[0]:.1f}, {second_point[1]:.1f}) pixels")
        print(f"Measured diameter: {pixel_diameter:.2f} pixels")
        print(f"Physical diameter: {physical_diameter:.3f} cm")
        print(f"Calibration factor: {calibration_factor:.6f} cm/pixel")
        decision = input(
            "Accept this calibration? Type yes to accept, no to repeat, "
            "or cancel to exit: "
        ).strip().lower()
        if decision in ("yes", "y"):
            return pixel_diameter, calibration_factor
        if decision in ("cancel", "c", "quit", "q"):
            return None
        if decision not in ("no", "n"):
            print("Enter yes, no, or cancel.")


def get_spatial_times(duration, fps, frame_count):
    last_frame = int(frame_count) - 1
    while True:
        time_input = input(
            "Enter at least 3 video times in seconds, separated by commas "
            "[10, 60, 180]: "
        ).strip()
        if not time_input:
            time_input = "10, 60, 180"

        try:
            times = [float(value.strip()) for value in time_input.split(",")]
        except ValueError:
            print("Enter valid numbers separated by commas.")
            continue

        if len(times) < 3 or not all(math.isfinite(value) for value in times):
            print("Enter at least 3 finite video times.")
            continue
        if any(time < 0 or time > duration for time in times):
            print(f"Each time must be between 0 and {duration:.2f} seconds.")
            continue

        frame_indices = [
            min(round(time * fps), last_frame)
            for time in times
        ]
        if len(set(frame_indices)) != len(frame_indices):
            print("Choose times that correspond to different video frames.")
            continue
        return times


def show_spatial_rois(frame, strip_roi, reference_roi):
    strip_rgb = cv2.cvtColor(roi_crop(frame, strip_roi), cv2.COLOR_BGR2RGB)
    reference_rgb = cv2.cvtColor(roi_crop(frame, reference_roi), cv2.COLOR_BGR2RGB)

    figure, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(strip_rgb)
    axes[0].set_title("Horizontal measurement strip")
    axes[1].imshow(reference_rgb)
    axes[1].set_title("Clear-water reference ROI")
    for axis in axes:
        axis.axis("off")
    figure.tight_layout()
    plt.show()


def select_spatial_rois(frame):
    while True:
        print("Select a horizontal strip that crosses the ink.")
        strip_roi = select_roi("Select horizontal ink strip", frame)
        if strip_roi is None:
            print("Strip selection was cancelled.")
            return None
        if strip_roi[2] <= strip_roi[3]:
            print("The strip must be wider than it is tall. Please select again.")
            continue

        while True:
            print("Select a separate clear-water reference ROI.")
            reference_roi = select_roi("Select clear-water reference ROI", frame)
            if reference_roi is None:
                print("Reference ROI selection was cancelled.")
                return None
            if not rois_overlap(strip_roi, reference_roi):
                break
            print("The reference ROI overlaps the strip. Select another region.")

        show_spatial_rois(frame, strip_roi, reference_roi)
        decision = input(
            "Use these regions? Type yes to continue, no to reselect, "
            "or cancel to exit: "
        ).strip().lower()
        if decision in ("yes", "y"):
            return strip_roi, reference_roi
        if decision in ("cancel", "c", "quit", "q"):
            return None
        if decision not in ("no", "n"):
            print("Enter yes, no, or cancel.")


def analyze_spatial_video(
    capture,
    fps,
    frame_count,
    times,
    strip_roi,
    reference_roi,
    calibration_factor,
):
    rows = []
    curves = []
    last_frame = int(frame_count) - 1

    for requested_time in times:
        frame_index = min(round(requested_time * fps), last_frame)
        frame = read_frame(capture, frame_index)
        if frame is None:
            print(
                f"Warning: Could not read the frame at "
                f"{requested_time:.3f} seconds; skipping it."
            )
            continue
        if not roi_fits_frame(frame, strip_roi) or not roi_fits_frame(
            frame, reference_roi
        ):
            print(
                f"Warning: A selected region is outside the frame at "
                f"{requested_time:.3f} seconds; skipping it."
            )
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        strip_gray = roi_crop(gray, strip_roi)
        strip_intensities = cv2.reduce(
            strip_gray, 0, cv2.REDUCE_AVG, dtype=cv2.CV_64F
        )[0]
        reference_intensity = cv2.mean(roi_crop(gray, reference_roi))[0]
        actual_time = frame_index / fps
        distances = [
            pixel_offset * calibration_factor
            for pixel_offset in range(strip_roi[2])
        ]

        if reference_intensity == 0:
            print(
                f"Warning: Reference intensity is zero at {actual_time:.3f} s; "
                "concentration values are unavailable for this time."
            )
            concentrations = [None] * len(distances)
        else:
            concentrations = [
                1 - intensity / reference_intensity
                for intensity in strip_intensities
            ]
            curves.append((actual_time, distances, concentrations))

        for distance, intensity, concentration in zip(
            distances, strip_intensities, concentrations
        ):
            rows.append(
                (
                    actual_time,
                    distance,
                    float(intensity),
                    reference_intensity,
                    concentration,
                )
            )

    return rows, curves


def save_spatial_results(rows, curves, experiment, category):
    if not rows:
        print("No readable frames were available; no spatial results were saved.")
        return

    try:
        results_folder = create_results_folder(category)
    except OSError as error:
        print(f"Could not create a unique results folder: {error}")
        return

    csv_path = results_folder / "concentration_vs_distance.csv"
    try:
        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "time_s",
                    "distance_cm",
                    "strip_intensity",
                    "reference_intensity",
                    "relative_concentration",
                ]
            )
            for time, distance, strip_intensity, reference, concentration in rows:
                writer.writerow(
                    [
                        time,
                        distance,
                        strip_intensity,
                        reference,
                        "" if concentration is None else concentration,
                    ]
                )
    except OSError as error:
        print(f"Could not save measurements to {csv_path}: {error}")
        return

    graph_path = results_folder / "concentration_vs_distance.png"
    plt.figure()
    for time, distances, concentrations in curves:
        plt.plot(distances, concentrations, label=f"{time:.2f} s")
    plt.xlabel("Distance (cm)")
    plt.ylabel("Relative concentration (dimensionless)")
    plt.title(f"Relative ink concentration versus distance - {experiment}")
    if curves:
        plt.legend(title="Time")
    plt.grid(True)
    plt.tight_layout()
    try:
        plt.savefig(graph_path)
    except OSError as error:
        print(f"Could not save graph to {graph_path}: {error}")
        plt.close()
        return

    plt.show()
    print(f"Measurements saved to: {csv_path}")
    print(f"Graph saved to: {graph_path}")


def sample_frame_indices(start_time, end_time, interval, fps, frame_count):
    last_frame = int(frame_count) - 1
    frame_indices = []
    sample_number = 0

    while True:
        requested_time = start_time + sample_number * interval
        if requested_time > end_time:
            break
        frame_index = min(round(requested_time * fps), last_frame)
        if not frame_indices or frame_index != frame_indices[-1]:
            frame_indices.append(frame_index)
        sample_number += 1

    return frame_indices


def analyze_video(capture, fps, frame_count, start_time, end_time, interval,
                  measurement_roi, reference_roi):
    measurements = []
    baseline_reference = None
    warned_contamination = False

    frame_indices = sample_frame_indices(
        start_time, end_time, interval, fps, frame_count
    )
    for frame_index in frame_indices:
        frame = read_frame(capture, frame_index)
        if frame is None:
            print(f"Warning: Could not read frame {frame_index}; skipping it.")
            continue

        if not roi_fits_frame(frame, measurement_roi) or not roi_fits_frame(
            frame, reference_roi
        ):
            print(f"Warning: ROI is outside frame {frame_index}; skipping it.")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        measurement_intensity = cv2.mean(roi_crop(gray, measurement_roi))[0]
        reference_intensity = cv2.mean(roi_crop(gray, reference_roi))[0]
        timestamp = frame_index / fps

        if reference_intensity == 0:
            print(
                f"Warning: Reference intensity is zero at {timestamp:.3f} s; "
                "relative concentration is unavailable for this frame."
            )
        elif baseline_reference is None:
            baseline_reference = reference_intensity
        elif (
            not warned_contamination
            and reference_intensity
            <= baseline_reference * (1 - REFERENCE_CONTAMINATION_DROP)
        ):
            print(
                "Warning: Reference ROI intensity has dropped by at least 10% "
                f"at {timestamp:.3f} s. The ROI may be contaminated, or "
                "lighting may have changed."
            )
            warned_contamination = True

        concentration = relative_concentration(
            measurement_intensity, reference_intensity
        )
        measurements.append(
            (
                timestamp,
                measurement_intensity,
                reference_intensity,
                concentration,
            )
        )

    return measurements


def create_results_folder(category):
    results_root = Path(__file__).resolve().parent / "results" / category
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    results_folder = results_root / timestamp
    results_folder.mkdir(parents=True, exist_ok=False)
    return results_folder


def save_results(measurements, experiment, category):
    if not measurements:
        print("No readable sample frames were available; no results were saved.")
        return

    try:
        results_folder = create_results_folder(category)
    except OSError as error:
        print(f"Could not create a unique results folder: {error}")
        return

    csv_path = results_folder / "measurements.csv"
    try:
        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "time_s",
                    "measurement_intensity",
                    "reference_intensity",
                    "relative_concentration",
                ]
            )
            for timestamp, measurement, reference, concentration in measurements:
                writer.writerow(
                    [
                        timestamp,
                        measurement,
                        reference,
                        "" if concentration is None else concentration,
                    ]
                )
    except OSError as error:
        print(f"Could not save measurements to {csv_path}: {error}")
        return

    graph_path = results_folder / "relative_concentration.png"
    valid_measurements = [
        row for row in measurements if row[3] is not None
    ]
    times = [row[0] for row in valid_measurements]
    concentrations = [row[3] for row in valid_measurements]

    plt.figure()
    plt.plot(times, concentrations, marker="o")
    plt.xlabel("Time (s)")
    plt.ylabel("Relative concentration (dimensionless)")
    plt.title(f"Relative ink concentration versus time - {experiment}")
    plt.grid(True)
    plt.tight_layout()
    try:
        plt.savefig(graph_path)
    except OSError as error:
        print(f"Could not save graph to {graph_path}: {error}")
        plt.close()
        return

    plt.show()
    print(f"Measurements saved to: {csv_path}")
    print(f"Graph saved to: {graph_path}")


def run_analysis(choice):
    selection = EXPERIMENTS.get(choice)
    if selection is None:
        print("Invalid choice. Select a video option from the main menu.")
        return
    experiment, category = selection

    root = tk.Tk()
    root.withdraw()
    video_path = filedialog.askopenfilename(
        title=f"Select the original video for {experiment}",
        filetypes=[
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.m4v"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()

    if not video_path:
        print("No video selected. Returning to the main menu.")
        return

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        capture.release()
        print(f"Could not open video: {video_path}")
        return

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    valid_fps = math.isfinite(fps) and fps > 0
    valid_frame_count = math.isfinite(frame_count) and frame_count > 0
    duration = frame_count / fps if valid_fps and valid_frame_count else None

    preview_index = int(10 * fps) if valid_fps else 0
    if valid_frame_count:
        preview_index = min(preview_index, int(frame_count) - 1)
    preview_frame = read_frame(capture, preview_index)
    if preview_frame is None:
        preview_frame = read_frame(capture, 0)
    if preview_frame is None:
        capture.release()
        print(f"Could not read a frame from: {video_path}")
        return

    print(f"\nVideo: {video_path}")
    print(f"FPS: {fps:.2f}" if valid_fps else "FPS: unavailable")
    print(
        f"Duration: {duration:.2f} seconds"
        if duration is not None
        else "Duration: unavailable"
    )
    print(
        f"Frame count: {frame_count:.0f}"
        if math.isfinite(frame_count) and frame_count >= 0
        else "Frame count: unavailable"
    )
    print(f"Resolution: {width} x {height}")

    preview_rgb = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
    plt.imshow(preview_rgb)
    plt.title(f"{experiment} - frame at or near 10 seconds")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    print("\nChoose analysis part:")
    print("1. Part A - Relative concentration versus time")
    print("2. Part B - Relative concentration versus distance")
    part_choice = input("Enter 1 or 2: ").strip()
    if part_choice == "2":
        if duration is None or not valid_fps or not valid_frame_count:
            capture.release()
            print(
                "Cannot analyze concentration versus distance because the "
                "video FPS or duration is unavailable."
            )
            return

        calibration = calibrate_spatial_scale(preview_frame)
        if calibration is None:
            capture.release()
            print("Spatial calibration cancelled. Returning to the main menu.")
            return

        pixel_diameter, calibration_factor = calibration
        print(
            f"Accepted calibration: {pixel_diameter:.2f} pixels = "
            f"{calibration_factor:.6f} cm/pixel."
        )
        times = get_spatial_times(duration, fps, frame_count)
        first_frame_index = min(round(times[0] * fps), int(frame_count) - 1)
        spatial_frame = read_frame(capture, first_frame_index)
        if spatial_frame is None:
            capture.release()
            print(
                f"Could not read the frame at the selected time "
                f"{times[0]:.3f} seconds."
            )
            return

        selected_rois = select_spatial_rois(spatial_frame)
        if selected_rois is None:
            capture.release()
            print(
                "Spatial concentration analysis cancelled. "
                "Returning to the main menu."
            )
            return
        strip_roi, reference_roi = selected_rois

        rows, curves = analyze_spatial_video(
            capture,
            fps,
            frame_count,
            times,
            strip_roi,
            reference_roi,
            calibration_factor,
        )
        capture.release()
        save_spatial_results(rows, curves, experiment, category)
        return
    if part_choice != "1":
        capture.release()
        print("Invalid choice. Enter 1 for Part A or 2 for Part B.")
        return

    if duration is None or not valid_fps:
        capture.release()
        print("Cannot analyze this video because its FPS or duration is unavailable.")
        return

    start_time, end_time, interval = get_analysis_times(duration, fps)
    start_index = min(round(start_time * fps), int(frame_count) - 1)
    start_frame = read_frame(capture, start_index)
    if start_frame is None:
        capture.release()
        print(f"Could not read the selected start frame at {start_time:.3f} seconds.")
        return

    print("Select the measurement ROI containing the ink.")
    measurement_roi = select_roi("Select measurement ROI", start_frame)
    if measurement_roi is None:
        capture.release()
        print("Measurement ROI selection cancelled. Returning to the main menu.")
        return

    while True:
        print("Select the reference ROI containing clear water.")
        reference_roi = select_roi("Select reference ROI", start_frame)
        if reference_roi is None:
            capture.release()
            print("Reference ROI selection cancelled. Returning to the main menu.")
            return
        if not rois_overlap(measurement_roi, reference_roi):
            break
        print("The ROIs overlap. Please select a separate reference region.")

    show_selected_rois(start_frame, measurement_roi, reference_roi)
    confirmation = input(
        "Use these ROIs for analysis? Type yes to continue: "
    ).strip().lower()
    if confirmation != "yes":
        capture.release()
        print("Analysis cancelled. Returning to the main menu.")
        return

    measurements = analyze_video(
        capture,
        fps,
        frame_count,
        start_time,
        end_time,
        interval,
        measurement_roi,
        reference_roi,
    )
    capture.release()
    save_results(measurements, experiment, category)


def main():
    while True:
        print("\nTransport Phenomena Laboratory 2: Diffusion")
        print("Choose an experiment video:")
        for number, (name, _) in EXPERIMENTS.items():
            print(f"{number}. {name}")
        print("0. Exit program")

        choice = input("Enter 1, 2, 3, or 0: ").strip()
        if choice == "0":
            print("Program closed.")
            break

        try:
            run_analysis(choice)
        finally:
            plt.close("all")


if __name__ == "__main__":
    main()
