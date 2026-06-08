# Stereo Camera Calibration And Point Cloud Reconstruction

This project contains a Basler stereo-camera workflow for camera calibration, stereo rectification, disparity estimation, and point-cloud reconstruction.

The current setup uses a ChArUco calibration board and a mono-first calibration workflow: each camera is calibrated separately, then the stereo relation is estimated with the mono intrinsics fixed.

The project was created with the support of AI, all code and functionality have been checked and debugged by the author. The notebooks are intended to be run sequentially, but they can be adapted for other calibration and reconstruction workflows.

## Repository Structure

- `calib/mono_then_stereo_calibration.ipynb`  
  Calibration notebook for mono calibration, stereo calibration, rectification checks, and scene-placement checks.

- `scene_pointcloud_from_stereo.ipynb`  
  Reconstruction notebook. It captures or loads a stereo scene pair, optionally runs YOLO object detection on the raw camera images, rectifies the pair, computes disparity, and exports a colored point cloud.

- `calib/stereo_params_mono_first.pkl`  
  Saved stereo calibration parameters used by the reconstruction notebook.

- `calib/mono_camera_params.pkl`  
  Saved mono calibration parameters for both cameras.

- `calib/tools/`  
  Small diagnostic scripts used during calibration development.

Generated image captures, point clouds, virtual environments, and notebook checkpoints are ignored by git.

## Setup

The project uses PDM for dependency management.

```powershell
pdm install
```

Install optional notebook and visualization dependencies when needed:

```powershell
pdm install -G notebook -G widgets -G mesh
```

If the Basler cameras are used from Python, the Basler runtime and `pypylon` must be available in the active environment.

## Calibration Workflow

Open:

```text
calib/mono_then_stereo_calibration.ipynb
```

Use the notebook in this order:

1. Check the board and camera settings in the configuration cell.
2. Capture mono calibration images for the left camera.
3. Capture mono calibration images for the right camera.
4. Run mono calibration and save `calib/mono_camera_params.pkl`.
5. Capture stereo calibration pairs without changing the camera setup.
6. Run stereo calibration with fixed mono intrinsics.
7. Save `calib/stereo_params_mono_first.pkl`.
8. Check rectification and placement overlays.

The current board settings are:

- ChArUco board
- 11 x 8 squares
- 10 mm square size
- 7 mm marker size
- ArUco dictionary `DICT_4X4_50`
- legacy ChArUco pattern enabled

Keep camera order, exposure, gain, focus, resolution, mounting, and board settings unchanged during a calibration session.

## Reconstruction Workflow

Open:

```text
scene_pointcloud_from_stereo.ipynb
```

Use the notebook in this order:

1. Load `calib/stereo_params_mono_first.pkl`.
2. Capture a new stereo scene pair, or reuse the newest pair in `captures/`.
3. Optionally run YOLO object detection on the raw left/right camera images.
4. Optionally apply histogram equalization.
5. Rectify the stereo pair.
6. Compute disparity with StereoSGBM.
7. Inspect the valid disparity mask.
8. Reproject valid disparity pixels to 3D with the saved `Q` matrix.
9. Export a colored `.ply` point cloud to `pointclouds/`.

If the disparity output is mostly at the maximum value, increase `SGBM_NUM_DISPARITIES` or move the object farther away. A saturated disparity map cannot produce a reliable point cloud.

## Generated Files

These folders are intentionally ignored:

- `captures/`
- `pointclouds/`
- `detections/`
- `calib/mono_calib_left/`
- `calib/mono_calib_right/`
- `calib/stereo_calib_images/`

The calibration parameter files are kept in the repository so reconstruction can run without committing all calibration images.

## Notes

- Calibration units are millimeters because the ChArUco board dimensions are configured in millimeters.
- The reconstruction quality depends strongly on rectification quality, image texture, exposure consistency, and the selected disparity range.
- Clear notebook outputs before committing large visual results.
