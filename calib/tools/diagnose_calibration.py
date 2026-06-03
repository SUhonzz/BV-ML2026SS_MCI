"""Diagnose stereo chessboard calibration image consistency."""

from __future__ import annotations

import glob
import os
import pickle

import cv2
import numpy as np


CALIB_DIR = "calib_images"
PARAMS_FILE = "stereo_params.pkl"
BOARD_CANDIDATES = [(5, 8), (8, 5), (6, 9), (9, 6)]


def find_corners(gray: np.ndarray, board_size: tuple[int, int]):
    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, board_size)
        if found:
            return True, corners.astype(np.float32)

    found, corners = cv2.findChessboardCorners(gray, board_size, None)
    if not found:
        return False, None

    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    corners = cv2.cornerSubPix(gray, corners.astype(np.float32), (11, 11), (-1, -1), term)
    return True, corners


def image_variants(gray: np.ndarray):
    return {
        "as_saved": gray,
        "rot180": cv2.rotate(gray, cv2.ROTATE_180),
        "flip_horizontal": cv2.flip(gray, 1),
        "flip_vertical": cv2.flip(gray, 0),
    }


def collect(board_size: tuple[int, int], right_variant: str = "as_saved"):
    objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : board_size[0], 0 : board_size[1]].T.reshape(-1, 2)
    objp[:, :2] *= 5.0

    objpoints = []
    left_points = []
    right_points = []
    valid_names = []
    failures = []
    image_size = None

    for left_path in sorted(glob.glob(os.path.join(CALIB_DIR, "*_L.png"))):
        right_path = left_path.replace("_L.png", "_R.png")
        if not os.path.exists(right_path):
            failures.append((os.path.basename(left_path), "missing right"))
            continue

        left = cv2.imread(left_path, cv2.IMREAD_GRAYSCALE)
        right_raw = cv2.imread(right_path, cv2.IMREAD_GRAYSCALE)
        if left is None or right_raw is None:
            failures.append((os.path.basename(left_path), "read failed"))
            continue

        right = image_variants(right_raw)[right_variant]
        image_size = left.shape[::-1]
        found_l, corners_l = find_corners(left, board_size)
        found_r, corners_r = find_corners(right, board_size)
        if found_l and found_r:
            objpoints.append(objp.copy())
            left_points.append(corners_l)
            right_points.append(corners_r)
            valid_names.append(os.path.basename(left_path).replace("_L.png", ""))
        else:
            failures.append(
                (
                    os.path.basename(left_path),
                    f"L={found_l} R={found_r}",
                )
            )

    return objpoints, left_points, right_points, valid_names, failures, image_size


def calibrate(board_size: tuple[int, int], right_variant: str = "as_saved"):
    objpoints, left_points, right_points, valid_names, failures, image_size = collect(
        board_size, right_variant
    )
    if image_size is None or len(objpoints) < 5:
        return {
            "valid": len(objpoints),
            "failures": failures,
            "error": "not enough valid pairs",
        }

    w, h = image_size
    ret_l, mtx_l, dist_l, _, _ = cv2.calibrateCamera(
        objpoints, left_points, (w, h), None, None
    )
    ret_r, mtx_r, dist_r, _, _ = cv2.calibrateCamera(
        objpoints, right_points, (w, h), None, None
    )
    stereo_rms, _, _, _, _, r, t, _, _ = cv2.stereoCalibrate(
        objpoints,
        left_points,
        right_points,
        mtx_l,
        dist_l,
        mtx_r,
        dist_r,
        (w, h),
        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5),
        flags=cv2.CALIB_FIX_INTRINSIC,
    )

    return {
        "valid": len(objpoints),
        "failures": failures,
        "valid_names": valid_names,
        "mono_left": ret_l,
        "mono_right": ret_r,
        "stereo_rms": stereo_rms,
        "baseline": float(np.linalg.norm(t)),
        "translation": t.reshape(-1),
        "left_principal": (float(mtx_l[0, 2]), float(mtx_l[1, 2])),
        "right_principal": (float(mtx_r[0, 2]), float(mtx_r[1, 2])),
        "max_dist_left": float(np.abs(dist_l).max()),
        "max_dist_right": float(np.abs(dist_r).max()),
    }


def report_saved_params():
    if not os.path.exists(PARAMS_FILE):
        print("No saved stereo_params.pkl")
        return

    with open(PARAMS_FILE, "rb") as handle:
        params = pickle.load(handle)

    print("Saved Params")
    print(f"  board_size={params.get('board_size')}")
    print(f"  square_size={params.get('square_size')}")
    print(f"  image_size={params.get('image_size')}")
    print(f"  mono RMS L/R={params.get('mono_rms_left'):.4f}/{params.get('mono_rms_right'):.4f}")
    print(f"  stereo RMS={params.get('stereo_rms'):.4f}")
    print(f"  T={np.asarray(params.get('T')).reshape(-1)}")
    print(f"  baseline={np.linalg.norm(params.get('T')):.4f}")
    print()


def main():
    print("Detection Counts")
    for board_size in BOARD_CANDIDATES:
        counts = {}
        for variant in image_variants(np.zeros((2, 2), dtype=np.uint8)):
            obj, _, _, _, _, _ = collect(board_size, variant)
            counts[variant] = len(obj)
        print(f"  board_size={board_size}: {counts}")
    print()

    print("Calibration Attempts")
    for board_size in [(5, 8), (8, 5)]:
        for variant in ["as_saved", "rot180"]:
            result = calibrate(board_size, variant)
            print(f"  board_size={board_size}, right={variant}")
            if "error" in result:
                print(f"    valid={result['valid']} error={result['error']}")
                continue
            print(
                "    valid={valid} mono L/R={mono_left:.4f}/{mono_right:.4f} "
                "stereo={stereo_rms:.4f} baseline={baseline:.3f}".format(**result)
            )
            print(f"    T={result['translation']}")
            print(
                f"    principal L/R={result['left_principal']} / {result['right_principal']}"
            )
            print(
                f"    max distortion L/R={result['max_dist_left']:.3f}/{result['max_dist_right']:.3f}"
            )
    print()

    report_saved_params()


if __name__ == "__main__":
    main()
