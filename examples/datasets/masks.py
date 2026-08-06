# SPDX-License-Identifier: Apache-2.0
"""External per-image masks used by the COLMAP example dataset."""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import List, Literal, Optional, Sequence

import cv2
import imageio.v2 as imageio
import numpy as np
from typing_extensions import assert_never

MaskMode = Literal["exclude", "valid"]
MissingMaskPolicy = Literal["error", "warn", "valid"]


def _get_rel_paths(path_dir: str) -> List[str]:
    paths: List[str] = []
    for directory, _, filenames in os.walk(path_dir):
        for filename in filenames:
            paths.append(os.path.relpath(os.path.join(directory, filename), path_dir))
    return paths


def _relative_stem(path: str) -> str:
    return Path(path).with_suffix("").as_posix()


def resolve_mask_dir(
    data_dir: str, factor: int, mask_dir: Optional[str]
) -> Optional[str]:
    """Resolve an explicit mask directory or the ``auto`` convention."""
    if mask_dir is None:
        return None
    if mask_dir != "auto":
        resolved = (
            mask_dir if os.path.isabs(mask_dir) else os.path.join(data_dir, mask_dir)
        )
        if not os.path.isdir(resolved):
            raise ValueError(f"Mask directory does not exist: {resolved}")
        return resolved

    candidates = []
    if factor > 1:
        candidates.append(os.path.join(data_dir, f"masks_{factor}"))
    candidates.extend(
        os.path.join(data_dir, name) for name in ("masks", "dynamic_masks", "sam_masks")
    )
    for candidate in candidates:
        if os.path.isdir(candidate):
            return candidate
    raise ValueError(
        "--colmap_mask_dir auto was requested, but no masks_<factor>, masks, "
        "dynamic_masks, or sam_masks directory was found."
    )


def load_valid_mask(path: str, mode: MaskMode, threshold: int) -> np.ndarray:
    """Load a mask and convert it to the convention ``True = keep``."""
    mask = imageio.imread(path)
    if mask.ndim == 3:
        mask = mask[..., :3].max(axis=-1)
    if mask.ndim != 2:
        raise ValueError(
            f"Mask must be a 2D image after loading, got {mask.shape}: {path}"
        )
    foreground = mask > threshold
    if mode == "exclude":
        return ~foreground
    if mode == "valid":
        return foreground
    assert_never(mode)


def resize_valid_mask(mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Resize a boolean mask to ``(height, width)`` without interpolation."""
    if mask.shape == shape:
        return mask.astype(bool, copy=False)
    height, width = shape
    return cv2.resize(
        mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST
    ).astype(bool)


def sample_valid_mask(
    mask: np.ndarray,
    xy: Sequence[float],
    source_size: tuple[int, int],
) -> bool:
    """Sample a possibly downscaled mask at coordinates from the source image."""
    source_width, source_height = source_size
    x, y = float(xy[0]), float(xy[1])
    if x < 0 or y < 0 or x >= source_width or y >= source_height:
        return False
    mask_x = min(int(x * mask.shape[1] / source_width), mask.shape[1] - 1)
    mask_y = min(int(y * mask.shape[0] / source_height), mask.shape[0] - 1)
    return bool(mask[mask_y, mask_x])


def keep_sfm_point(
    valid_observations: int,
    masked_observations: int,
    min_valid_observations: int,
) -> bool:
    """Return whether an SfM point has enough observations in valid regions."""
    if masked_observations == 0:
        return True
    return valid_observations >= min_valid_observations


class ImageMaskProvider:
    """Resolve and lazily load masks matching COLMAP image paths."""

    def __init__(
        self,
        data_dir: str,
        factor: int,
        image_names: Sequence[str],
        image_rel_paths: Sequence[str],
        mask_dir: Optional[str],
        mode: MaskMode = "exclude",
        threshold: int = 0,
        missing: MissingMaskPolicy = "error",
    ) -> None:
        self.directory = resolve_mask_dir(data_dir, factor, mask_dir)
        self.mode = mode
        self.threshold = threshold
        self.missing = missing
        self._cache: dict[int, np.ndarray] = {}
        self.paths: List[Optional[str]] = [None] * len(image_names)
        if self.directory is None:
            return

        mask_index = {
            _relative_stem(rel_path): os.path.join(self.directory, rel_path)
            for rel_path in sorted(_get_rel_paths(self.directory))
        }
        for index, (image_name, image_rel_path) in enumerate(
            zip(image_names, image_rel_paths)
        ):
            for key in (_relative_stem(image_rel_path), _relative_stem(image_name)):
                if key in mask_index:
                    self.paths[index] = mask_index[key]
                    break

        missing_names = [
            name for name, path in zip(image_names, self.paths) if path is None
        ]
        if missing_names:
            message = (
                f"Missing masks for {len(missing_names)}/{len(image_names)} images in "
                f"{self.directory}; examples: {missing_names[:3]}"
            )
            if missing == "error":
                raise ValueError(message)
            if missing == "warn":
                warnings.warn(message + "; missing masks will be treated as valid.")
            elif missing != "valid":
                assert_never(missing)

    @property
    def enabled(self) -> bool:
        return self.directory is not None

    def load(self, index: int) -> Optional[np.ndarray]:
        path = self.paths[index]
        if path is None:
            return None
        if index not in self._cache:
            self._cache[index] = load_valid_mask(path, self.mode, self.threshold)
        return self._cache[index]
