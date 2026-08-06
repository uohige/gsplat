# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pytest
import torch

from examples.datasets.masks import (
    ImageMaskProvider,
    keep_sfm_point,
    resize_valid_mask,
    sample_valid_mask,
)
from examples.mask_utils import apply_valid_mask, masked_psnr


def _write_mask(path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(path, values.astype(np.uint8))


def _write_colmap_fixture(root: Path) -> None:
    """Write one image with one dynamic and one static COLMAP point."""
    (root / "images").mkdir(parents=True)
    (root / "sparse" / "0").mkdir(parents=True)
    imageio.imwrite(root / "images" / "frame.png", np.zeros((4, 4, 3), np.uint8))
    _write_mask(
        root / "dynamic_masks" / "frame.png",
        np.array(
            [[0, 0, 0, 0], [0, 255, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            dtype=np.uint8,
        ),
    )
    (root / "sparse" / "0" / "cameras.txt").write_text(
        "1 PINHOLE 4 4 2 2 2 2\n", encoding="utf-8"
    )
    (root / "sparse" / "0" / "images.txt").write_text(
        "1 1 0 0 0 0 0 0 1 frame.png\n1 1 1 2 2 2\n", encoding="utf-8"
    )
    (root / "sparse" / "0" / "points3D.txt").write_text(
        "1 0 0 2 255 0 0 0 1 0\n2 0 0 3 0 255 0 0 1 1\n",
        encoding="utf-8",
    )


def test_provider_matches_relative_stem_and_excludes_foreground(tmp_path):
    _write_mask(
        tmp_path / "dynamic_masks" / "nested" / "frame.png",
        np.array([[0, 255], [0, 0]], dtype=np.uint8),
    )
    provider = ImageMaskProvider(
        data_dir=str(tmp_path),
        factor=1,
        image_names=["nested/frame.jpg"],
        image_rel_paths=["nested/frame.jpg"],
        mask_dir="dynamic_masks",
        mode="exclude",
    )

    np.testing.assert_array_equal(
        provider.load(0), np.array([[True, False], [True, True]])
    )


def test_provider_auto_and_valid_mode(tmp_path):
    _write_mask(tmp_path / "masks_4" / "frame.png", np.array([[0, 8]]))
    provider = ImageMaskProvider(
        data_dir=str(tmp_path),
        factor=4,
        image_names=["frame.jpg"],
        image_rel_paths=["frame.png"],
        mask_dir="auto",
        mode="valid",
        threshold=4,
    )
    np.testing.assert_array_equal(provider.load(0), np.array([[False, True]]))


def test_provider_missing_masks_is_strict_by_default(tmp_path):
    (tmp_path / "masks").mkdir()
    with pytest.raises(ValueError, match="Missing masks"):
        ImageMaskProvider(
            data_dir=str(tmp_path),
            factor=1,
            image_names=["frame.jpg"],
            image_rel_paths=["frame.jpg"],
            mask_dir="masks",
        )


def test_provider_can_warn_and_treat_missing_mask_as_valid(tmp_path):
    (tmp_path / "masks").mkdir()
    with warnings.catch_warnings(record=True) as caught:
        provider = ImageMaskProvider(
            data_dir=str(tmp_path),
            factor=1,
            image_names=["frame.jpg"],
            image_rel_paths=["frame.jpg"],
            mask_dir="masks",
            missing="warn",
        )
    assert caught
    assert provider.load(0) is None


def test_mask_resize_and_source_coordinate_sampling():
    mask = np.array([[True, False], [False, True]])
    resized = resize_valid_mask(mask, (4, 4))
    assert resized.shape == (4, 4)
    assert sample_valid_mask(mask, (0.0, 0.0), (4, 4))
    assert not sample_valid_mask(mask, (3.0, 0.0), (4, 4))
    assert sample_valid_mask(mask, (3.0, 3.0), (4, 4))
    assert not sample_valid_mask(mask, (4.0, 0.0), (4, 4))


def test_sfm_point_requires_configured_number_of_valid_observations():
    assert keep_sfm_point(0, 0, 1)
    assert keep_sfm_point(1, 3, 1)
    assert not keep_sfm_point(1, 3, 2)


def test_colmap_parser_filters_dynamic_initialization_point(tmp_path):
    pytest.importorskip("pycolmap")
    _write_colmap_fixture(tmp_path)
    examples_dir = Path(__file__).resolve().parent.parent / "examples"
    sys.path.insert(0, str(examples_dir))
    try:
        from datasets.colmap import Dataset, Parser

        parser = Parser(
            data_dir=str(tmp_path),
            mask_dir="dynamic_masks",
            load_exposure=False,
            normalize=False,
        )
        dataset = Dataset(parser, split="val", load_depths=True)
        sample = dataset[0]
    finally:
        sys.path.remove(str(examples_dir))

    assert parser.points.shape == (1, 3)
    np.testing.assert_array_equal(parser.points_rgb, np.array([[0, 255, 0]]))
    assert sample["mask"].shape == (4, 4)
    assert not sample["mask"][1, 1]
    assert sample["mask"][2, 2]


def test_masked_psnr_ignores_invalid_pixels():
    pred = torch.tensor([[[[0.5], [1.0]]]])
    target = torch.zeros_like(pred)
    mask = torch.tensor([[[True, False]]])
    assert masked_psnr(pred, target, mask).item() == pytest.approx(6.0206, rel=1e-4)
    np.testing.assert_array_equal(
        apply_valid_mask(pred, mask).numpy(), np.array([[[[0.5], [0.0]]]])
    )
