"""Compare stereo calibration with saved and swapped left/right ordering."""

from __future__ import annotations

import glob
import os

import cv2
import numpy as np


BOARD_SIZE = (5, 8)
SQUARE_SIZE = 5.0
CALIB_DIR = "calib_images"


def find_corners(gray: np.ndarray):
    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, BOARD_SIZE)
        if found:
            return corners.astype(np.float32)

    found, corners = cv2.findChessboardCorners(gray, BOARD_SIZE, None)
    if not found:
        return None
    term = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    return cv2.cornerSubPix(gray, corners.astype(np.float32), (11, 11), (-1, -1), term)


def load_points():
    objp = np.zeros((BOARD_SIZE[0] * BOARD_SIZE[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : BOARD_SIZE[0], 0 : BOARD_SIZE[1]].T.reshape(-1, 2)
    objp[:, :2] *= SQUARE_SIZE

    objpoints = []
    left_points = []
    right_points = []
    names = []
    image_size = None

    for left_path in sorted(glob.glob(os.path.join(CALIB_DIR, "*_L.png"))):
        right_path = left_path.replace("_L.png", "_R.png")
        if not os.path.exists(right_path):
            continue
        left = cv2.imread(left_path, cv2.IMREAD_GRAYSCALE)
        right = cv2.imread(right_path, cv2.IMREAD_GRAYSCALE)
        corners_l = find_corners(left)
        corners_r = find_corners(right)
        if corners_l is None or corners_r is None:
            continue
        image_size = left.shape[::-1]
        objpoints.append(objp.copy())
        left_points.append(corners_l)
        right_points.append(corners_r)
        names.append(os.path.basename(left_path).replace("_L.png", ""))

    return objpoints, left_points, right_points, image_size, names


def solve(label: str, objpoints, points_l, points_r, image_size):
    w, h = image_size
    ret_l, mtx_l, dist_l, _, _ = cv2.calibrateCamera(
        objpoints, points_l, (w, h), None, None
    )
    ret_r, mtx_r, dist_r, _, _ = cv2.calibrateCamera(
        objpoints, points_r, (w, h), None, None
    )
    stereo_rms, _, _, _, _, _, t, _, _ = cv2.stereoCalibrate(
        objpoints,
        points_l,
        points_r,
        mtx_l,
        dist_l,
        mtx_r,
        dist_r,
        (w, h),
        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5),
        flags=cv2.CALIB_FIX_INTRINSIC,
    )
    print(label)
    print(f"  mono RMS L/R: {ret_l:.4f} / {ret_r:.4f}")
    print(f"  stereo RMS:   {stereo_rms:.4f}")
    print(f"  T:            {t.reshape(-1)}")
    print(f"  baseline:     {np.linalg.norm(t):.3f}")
    print(f"  principal L:  {mtx_l[0, 2]:.1f}, {mtx_l[1, 2]:.1f}")
    print(f"  principal R:  {mtx_r[0, 2]:.1f}, {mtx_r[1, 2]:.1f}")
    print(f"  max |dist|:   {np.abs(dist_l).max():.3f} / {np.abs(dist_r).max():.3f}")


def main():
    objpoints, left_points, right_points, image_size, names = load_points()
    print(f"valid pairs: {len(objpoints)}")
    print(f"image_size: {image_size}")
    print()
    solve("as saved L/R", objpoints, left_points, right_points, image_size)
    print()
    solve("swapped R/L", objpoints, right_points, left_points, image_size)


if __name__ == "__main__":
    main()
