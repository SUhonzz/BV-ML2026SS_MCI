"""Sweep ArUco dictionaries and ChArUco settings on captured calibration images."""

from __future__ import annotations

import glob
from pathlib import Path

import cv2
import numpy as np


IMAGE_GLOBS = [
    "mono_calib_left/*.png",
    "mono_calib_right/*.png",
]
SQUARES = (11, 8)
SQUARE_SIZE = 10.0
MARKER_SIZE = 7.0
LEGACY_PATTERN = True
DICT_NAMES = [
    "DICT_4X4_50",
    "DICT_4X4_100",
    "DICT_4X4_250",
    "DICT_4X4_1000",
]


def get_dictionary(name: str):
    dictionary_id = getattr(cv2.aruco, name)
    if hasattr(cv2.aruco, "getPredefinedDictionary"):
        return cv2.aruco.getPredefinedDictionary(dictionary_id)
    return cv2.aruco.Dictionary_get(dictionary_id)


def get_board(dictionary):
    if hasattr(cv2.aruco, "CharucoBoard"):
        board = cv2.aruco.CharucoBoard(SQUARES, SQUARE_SIZE, MARKER_SIZE, dictionary)
    else:
        board = cv2.aruco.CharucoBoard_create(
            SQUARES[0],
            SQUARES[1],
            SQUARE_SIZE,
            MARKER_SIZE,
            dictionary,
        )
    if hasattr(board, "setLegacyPattern"):
        board.setLegacyPattern(LEGACY_PATTERN)
    return board


def detect(gray, dictionary, board):
    marker_corners = []
    marker_ids = None
    if hasattr(cv2.aruco, "CharucoDetector"):
        detector = cv2.aruco.CharucoDetector(board)
        charuco_corners, charuco_ids, marker_corners, marker_ids = detector.detectBoard(gray)
        return (
            0 if marker_ids is None else len(marker_ids),
            0 if charuco_ids is None else len(charuco_ids),
        )

    if hasattr(cv2.aruco, "ArucoDetector"):
        detector = cv2.aruco.ArucoDetector(dictionary)
        marker_corners, marker_ids, _ = detector.detectMarkers(gray)
    else:
        marker_corners, marker_ids, _ = cv2.aruco.detectMarkers(gray, dictionary)

    if marker_ids is None:
        return 0, 0
    if not hasattr(cv2.aruco, "interpolateCornersCharuco"):
        return len(marker_ids), -1
    count, _corners, ids = cv2.aruco.interpolateCornersCharuco(
        marker_corners,
        marker_ids,
        gray,
        board,
    )
    return len(marker_ids), 0 if ids is None else len(ids)


def main() -> int:
    print("OpenCV:", cv2.__version__)
    print("has cv2.aruco:", hasattr(cv2, "aruco"))
    if not hasattr(cv2, "aruco"):
        return 1
    print("has CharucoDetector:", hasattr(cv2.aruco, "CharucoDetector"))
    print("has interpolateCornersCharuco:", hasattr(cv2.aruco, "interpolateCornersCharuco"))
    print()

    paths: list[Path] = []
    for pattern in IMAGE_GLOBS:
        paths.extend(Path(p) for p in sorted(glob.glob(pattern)))
    if not paths:
        print("No input images found")
        return 1

    sample_indices = np.linspace(0, len(paths) - 1, min(12, len(paths)), dtype=int)
    sample_paths = [paths[int(i)] for i in sample_indices]
    print("Sample images:", len(sample_paths), "of", len(paths))
    for path in sample_paths:
        print(" ", path)
    print()

    for dict_name in DICT_NAMES:
        dictionary = get_dictionary(dict_name)
        board = get_board(dictionary)
        marker_counts = []
        charuco_counts = []
        print(dict_name)
        for path in sample_paths:
            gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                print(f"  {path.name}: read failed")
                continue
            marker_count, charuco_count = detect(gray, dictionary, board)
            marker_counts.append(marker_count)
            charuco_counts.append(charuco_count)
            print(f"  {path.name}: markers={marker_count:2d}, charuco={charuco_count:2d}")
        if marker_counts:
            print(
                "  summary: "
                f"markers median/max={np.median(marker_counts):.1f}/{max(marker_counts)}, "
                f"charuco median/max={np.median(charuco_counts):.1f}/{max(charuco_counts)}"
            )
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
