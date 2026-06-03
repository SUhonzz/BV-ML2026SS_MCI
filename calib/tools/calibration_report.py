"""Report calibration image coverage and saved stereo parameter sanity."""

from __future__ import annotations

import argparse
import glob
import os
import pickle
from collections import Counter
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Detection:
    left_path: str
    right_path: str
    corners_left: np.ndarray
    corners_right: np.ndarray
    image_size: tuple[int, int]


def parse_board_size(value: str) -> tuple[int, int]:
    normalized = value.lower().replace(",", "x").replace(" ", "")
    parts = normalized.split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("board size must look like 5x8")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("board size must contain integers") from exc


def find_corners(gray: np.ndarray, board_size: tuple[int, int]) -> tuple[bool, np.ndarray | None]:
    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, board_size)
        if found:
            return True, corners.astype(np.float32)
    found, corners = cv2.findChessboardCorners(gray, board_size, None)
    if not found:
        return False, None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    corners = cv2.cornerSubPix(gray, corners.astype(np.float32), (11, 11), (-1, -1), criteria)
    return True, corners


def collect_detections(
    calib_dir: str,
    board_size: tuple[int, int],
) -> tuple[list[Detection], list[str], int, int, Counter[tuple[int, int]]]:
    detections: list[Detection] = []
    invalid: list[str] = []
    missing_right = 0
    valid_with_right_rotated = 0
    image_sizes: Counter[tuple[int, int]] = Counter()

    for left_path in sorted(glob.glob(os.path.join(calib_dir, "*_L.png"))):
        right_path = left_path.replace("_L.png", "_R.png")
        if not os.path.exists(right_path):
            missing_right += 1
            continue

        gray_left = cv2.imread(left_path, cv2.IMREAD_GRAYSCALE)
        gray_right = cv2.imread(right_path, cv2.IMREAD_GRAYSCALE)
        if gray_left is None or gray_right is None:
            invalid.append(os.path.basename(left_path))
            continue

        image_size = tuple(int(v) for v in gray_left.shape[::-1])
        image_sizes[image_size] += 1

        found_left, corners_left = find_corners(gray_left, board_size)
        found_right, corners_right = find_corners(gray_right, board_size)
        found_right_rotated, _ = find_corners(cv2.rotate(gray_right, cv2.ROTATE_180), board_size)

        if found_left and found_right:
            detections.append(
                Detection(
                    left_path=left_path,
                    right_path=right_path,
                    corners_left=corners_left,
                    corners_right=corners_right,
                    image_size=image_size,
                )
            )
        else:
            invalid.append(os.path.basename(left_path))

        if found_left and found_right_rotated:
            valid_with_right_rotated += 1

    return detections, invalid, missing_right, valid_with_right_rotated, image_sizes


def report_image_coverage(detections: list[Detection]) -> list[str]:
    if not detections:
        return ["No valid chessboard detections found."]

    image_width, image_height = detections[0].image_size
    boxes = []
    for detection in detections:
        points = detection.corners_left[:, 0, :]
        boxes.append(
            (
                float(points[:, 0].min()),
                float(points[:, 1].min()),
                float(points[:, 0].max()),
                float(points[:, 1].max()),
            )
        )

    box_array = np.asarray(boxes)
    centers = np.column_stack(
        (
            (box_array[:, 0] + box_array[:, 2]) / 2.0,
            (box_array[:, 1] + box_array[:, 3]) / 2.0,
        )
    )
    areas = (box_array[:, 2] - box_array[:, 0]) * (box_array[:, 3] - box_array[:, 1])
    avg_area_percent = 100.0 * float(areas.mean()) / float(image_width * image_height)

    lines = [
        f"Left board center x range: {centers[:, 0].min():.1f}..{centers[:, 0].max():.1f}",
        f"Left board center y range: {centers[:, 1].min():.1f}..{centers[:, 1].max():.1f}",
        f"Left board bbox area range: {areas.min():.0f}..{areas.max():.0f} px^2",
        f"Left board average bbox area: {areas.mean():.0f} px^2 ({avg_area_percent:.1f}% of image)",
    ]

    if centers[:, 1].min() > image_height * 0.25:
        lines.append("Warning: board positions do not reach the upper quarter of the image.")
    if centers[:, 0].min() > image_width * 0.20 or centers[:, 0].max() < image_width * 0.80:
        lines.append("Warning: board positions do not cover the full left/right spread.")
    if avg_area_percent < 15.0:
        lines.append("Warning: average board size is small; include closer/larger board views.")

    return lines


def rectification_error_lines(params: dict, detections: list[Detection]) -> list[str]:
    if not detections:
        return []

    errors = []
    for detection in detections:
        points_left = cv2.undistortPoints(
            detection.corners_left,
            params["mtxL"],
            params["distL"],
            R=params["R1"],
            P=params["P1"],
        )
        points_right = cv2.undistortPoints(
            detection.corners_right,
            params["mtxR"],
            params["distR"],
            R=params["R2"],
            P=params["P2"],
        )
        errors.extend((points_left[:, 0, 1] - points_right[:, 0, 1]).tolist())

    error_array = np.asarray(errors, dtype=np.float64)
    return [
        "Rectified y residuals: "
        f"median_abs={np.median(np.abs(error_array)):.3f}px, "
        f"p95_abs={np.percentile(np.abs(error_array), 95):.3f}px, "
        f"max_abs={np.max(np.abs(error_array)):.3f}px"
    ]


def report_params(params_path: str, detections: list[Detection]) -> list[str]:
    if not os.path.exists(params_path):
        return [f"No stereo parameter file found at {params_path}."]

    with open(params_path, "rb") as handle:
        params = pickle.load(handle)

    width, height = params["image_size"]
    matrix_left = np.asarray(params["mtxL"])
    matrix_right = np.asarray(params["mtxR"])
    dist_left = np.asarray(params["distL"])
    dist_right = np.asarray(params["distR"])
    translation = np.asarray(params["T"]).reshape(-1)

    lines = [
        f"Parameter image size: {params['image_size']}",
        f"Parameter board size: {params.get('board_size')}",
        f"Parameter square size: {params.get('square_size')}",
        f"Mono RMS left/right: {params.get('mono_rms_left'):.4f} / {params.get('mono_rms_right'):.4f}",
        f"Stereo RMS: {params.get('stereo_rms'):.4f}",
        f"Baseline norm: {np.linalg.norm(translation):.3f}",
        f"Translation T: {translation}",
        f"Principal point left: ({matrix_left[0, 2]:.1f}, {matrix_left[1, 2]:.1f})",
        f"Principal point right: ({matrix_right[0, 2]:.1f}, {matrix_right[1, 2]:.1f})",
        f"Max abs distortion left/right: {np.abs(dist_left).max():.3f} / {np.abs(dist_right).max():.3f}",
        f"P1[0,3], P2[0,3]: {params['P1'][0, 3]:.3f}, {params['P2'][0, 3]:.3f}",
    ]

    warnings = []
    if params.get("stereo_rms", 0.0) > 1.0:
        warnings.append("Warning: stereo RMS is above 1 px.")
    if np.abs(dist_left).max() > 10.0 or np.abs(dist_right).max() > 10.0:
        warnings.append("Warning: very large distortion coefficient detected.")
    if abs(matrix_left[0, 2] - width / 2) > width * 0.20:
        warnings.append("Warning: left principal point is far from image center.")
    if abs(matrix_right[0, 2] - width / 2) > width * 0.20:
        warnings.append("Warning: right principal point is far from image center.")
    if abs(translation[2]) > max(abs(translation[0]), 1e-6) * 0.25:
        warnings.append("Warning: translation has a large forward component relative to baseline.")

    return lines + rectification_error_lines(params, detections) + warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calib-dir", default="calib_images")
    parser.add_argument("--params", default="stereo_params.pkl")
    parser.add_argument("--board-size", type=parse_board_size, default=(5, 8))
    args = parser.parse_args()

    detections, invalid, missing_right, valid_rotated, image_sizes = collect_detections(
        args.calib_dir,
        args.board_size,
    )
    left_count = len(glob.glob(os.path.join(args.calib_dir, "*_L.png")))

    print("Calibration Images")
    print(f"  Left images: {left_count}")
    print(f"  Valid pairs as saved: {len(detections)}")
    print(f"  Valid pairs if right image were rotated 180 first: {valid_rotated}")
    print(f"  Missing right images: {missing_right}")
    print(f"  Invalid pairs: {len(invalid)}")
    print(f"  Image sizes: {dict(image_sizes)}")
    if invalid:
        print("  First invalid pairs:", ", ".join(invalid[:8]))

    print()
    print("Image Coverage")
    for line in report_image_coverage(detections):
        print(f"  {line}")

    print()
    print("Saved Parameters")
    for line in report_params(args.params, detections):
        print(f"  {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
