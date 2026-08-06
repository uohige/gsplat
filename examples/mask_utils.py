# SPDX-License-Identifier: Apache-2.0
"""Small tensor helpers for mask-aware training and evaluation."""

from __future__ import annotations

from typing import Optional

import torch
from torch import Tensor


def apply_valid_mask(images: Tensor, masks: Optional[Tensor]) -> Tensor:
    if masks is None:
        return images
    return images * masks[..., None]


def masked_psnr(pred: Tensor, target: Tensor, masks: Optional[Tensor]) -> Tensor:
    """PSNR computed only from valid RGB samples."""
    if masks is None:
        mse = torch.square(pred - target).mean()
    elif not torch.any(masks):
        return pred.new_tensor(float("nan"))
    else:
        mse = torch.square(pred[masks] - target[masks]).mean()
    return -10.0 * torch.log10(torch.clamp_min(mse, torch.finfo(mse.dtype).eps))
