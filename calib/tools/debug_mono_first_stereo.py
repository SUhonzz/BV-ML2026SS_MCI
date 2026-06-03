"""Debug mono-first stereo calibration failures."""

from __future__ import annotations

import glob
import os
import pickle

import cv2
import numpy as np


BOARD_SIZE = (5, 8)
SQUARE_SIZE = 5.0
MONO_PARAMS_FILE = "mono_camera_params.pkl"
STEREO_DIR = "stereo_calib_images"


def make_object_points():
    objp = np.zeros((BOARD_SIZE[0] * BOARD_SIZE[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : BOARD_SIZE[0], 0 : BOARD_SIZE[1]].T.reshape(-1, 2)
    objp[:, :2] *= SQUARE_SIZE
    return objp


def find_corners(gray):
    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, BOARD_SIZE)
        if found:
            return corners.astype(np.float32)

    found, corners = cv2.findChessboardCorners(gray, BOARD_SIZE, None)
    if not found:
        return None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    return cv2.cornerSubPix(gray, corners.astype(np.float32), (11, 11), (-1, -1), criteria)


def right_variant(gray, variant):
    if variant == "as_saved":
        return gray
    if variant == "rot180":
        return cv2.rotate(gray, cv2.ROTATE_180)
    if variant == "flip_horizontal":
        return cv2.flip(gray, 1)
    if variant == "flip_vertical":
        return cv2.flip(gray, 0)
    raise ValueError(variant)


def collect(variant="as_saved", reverse_right=False):
    objp = make_object_points()
    objpoints = []
    left_points = []
    right_points = []
    names = []
    rejected = []
    image_size = None

    for left_path in sorted(glob.glob(os.path.join(STEREO_DIR, "*_L.png"))):
        right_path = left_path.replace("_L.png", "_R.png")
        if not os.path.exists(right_path):
            rejected.append((os.path.basename(left_path), "missing right"))
            continue
        left = cv2.imread(left_path, cv2.IMREAD_GRAYSCALE)
        right = cv2.imread(right_path, cv2.IMREAD_GRAYSCALE)
        if left is None or right is None:
            rejected.append((os.path.basename(left_path), "read failed"))
            continue
        right = right_variant(right, variant)
        if left.shape != right.shape:
            rejected.append((os.path.basename(left_path), "shape mismatch"))
            continue
        image_size = tuple(int(v) for v in left.shape[::-1])
        corners_l = find_corners(left)
        corners_r = find_corners(right)
        if corners_l is None or corners_r is None:
            rejected.append((os.path.basename(left_path), f"L={corners_l is not None} R={corners_r is not None}"))
            continue
        if reverse_right:
            corners_r = corners_r[::-1].copy()
        objpoints.append(objp.copy())
        left_points.append(corners_l)
        right_points.append(corners_r)
        names.append(os.path.basename(left_path).replace("_L.png", ""))

    return objpoints, left_points, right_points, names, rejected, image_size


def solve(objpoints, left_points, right_points, image_size, params, swapped=False):
    lkey, rkey = ("right", "left") if swapped else ("left", "right")
    mtx_l = np.asarray(params[lkey]["camera_matrix"], dtype=np.float64)
    dist_l = np.asarray(params[lkey]["distortion"], dtype=np.float64)
    mtx_r = np.asarray(params[rkey]["camera_matrix"], dtype=np.float64)
    dist_r = np.asarray(params[rkey]["distortion"], dtype=np.float64)
    return cv2.stereoCalibrate(
        objpoints,
        left_points,
        right_points,
        mtx_l,
        dist_l,
        mtx_r,
        dist_r,
        image_size,
        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5),
        flags=cv2.CALIB_FIX_INTRINSIC,
    )


def main():
    print("OpenCV:", cv2.__version__)
    with open(MONO_PARAMS_FILE, "rb") as handle:
        params = pickle.load(handle)

    print("Mono params")
    print("  image_size:", params["image_size"])
    print("  mono RMS left/right:", params["left"]["rms"], params["right"]["rms"])
    print("  principal left:", params["left"]["camera_matrix"][0, 2], params["left"]["camera_matrix"][1, 2])
    print("  principal right:", params["right"]["camera_matrix"][0, 2], params["right"]["camera_matrix"][1, 2])
    print("  max |dist| left/right:", np.abs(params["left"]["distortion"]).max(), np.abs(params["right"]["distortion"]).max())
    print()

    rows = []
    for variant in ["as_saved", "rot180", "flip_horizontal", "flip_vertical"]:
        for reverse in [False, True]:
            objpoints, lp, rp, names, rejected, image_size = collect(variant, reverse)
            for swapped in [False, True]:
                label = f"right={variant}, reverse={reverse}, swapped_intrinsics={swapped}"
                if len(objpoints) < 5:
                    rows.append((np.inf, label, len(objpoints), None, "not enough points"))
                    continue
                try:
                    rms, _, _, _, _, _, t, _, _ = solve(objpoints, lp, rp, image_size, params, swapped)
                    rows.append((float(rms), label, len(objpoints), float(np.linalg.norm(t)), "ok"))
                except Exception as exc:
                    rows.append((np.inf, label, len(objpoints), None, str(exc).splitlines()[0]))

    print("Variant summary")
    for rank, (rms, label, count, baseline, status) in enumerate(sorted(rows, key=lambda x: x[0]), 1):
        rms_text = "inf" if not np.isfinite(rms) else f"{rms:.4f}"
        base_text = "-" if baseline is None else f"{baseline:.3f}"
        print(f"{rank:2d}. rms={rms_text:>12} baseline={base_text:>10} pairs={count:2d} {label} [{status}]")


if __name__ == "__main__":
    main()
