Fit a COLMAP Capture
========================================

.. currentmodule:: gsplat

The :code:`examples/simple_trainer.py default` script allows you train a 
`3D Gaussian Splatting <https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/>`_ 
model for novel view synthesis, on a COLMAP processed capture. This script follows the
exact same logic with the `official implementation 
<https://github.com/graphdeco-inria/gaussian-splatting>`_ and we have verified it to be 
able to reproduce the metrics in the paper, with much better training speed and memory 
footprint. See :doc:`../tests/eval` for more details on the comparison.

Simply run the script under `examples/`:

.. code-block:: bash

    CUDA_VISIBLE_DEVICES=0 python simple_trainer.py default \
        --data_dir data/360_v2/garden/ --data_factor 4 \
        --result_dir ./results/garden

Training a static scene with dynamic-object masks
--------------------------------------------------

An optional mask can exclude moving objects, people, vehicles, or the capture rig
from both the photometric loss and the COLMAP points used to initialize Gaussians.
The on-disk mask is converted to the internal convention ``True = keep``.

Place one mask next to every source image using the same relative path stem. File
extensions may differ. For example:

.. code-block:: text

    capture/
    ├── images/
    │   ├── camera_a/0001.jpg
    │   └── camera_a/0002.jpg
    ├── dynamic_masks/
    │   ├── camera_a/0001.png
    │   └── camera_a/0002.png
    └── sparse/0/...

With the default ``exclude`` mode, non-zero mask pixels are dynamic and are
discarded:

.. code-block:: bash

    CUDA_VISIBLE_DEVICES=0 python simple_trainer.py default \
        --data-dir capture --data-factor 1 \
        --colmap-mask-dir dynamic_masks \
        --colmap-mask-mode exclude \
        --result-dir results/static-capture

Use ``--colmap-mask-dir auto`` to search ``masks_<factor>``, ``masks``,
``dynamic_masks``, then ``sam_masks``. An explicit directory is safer for
repeatable runs. ``--colmap-mask-mode valid`` reverses the convention so non-zero
pixels are retained. ``--colmap-mask-threshold`` controls binarization.

All masks are required by default. This prevents a missing file from silently
allowing a dynamic object into the reconstruction. ``--colmap-mask-missing warn``
or ``valid`` opts into treating missing masks as fully valid.

When masks are enabled, COLMAP points are retained only when at least one tracked
2D observation lies in a valid mask region. Increase
``--colmap-mask-min-valid-observations`` for more conservative filtering, or set
``--no-colmap-mask-filter-sfm-points`` to disable point filtering. Filtering
the reconstructed point cloud does not change camera poses that COLMAP already
estimated; for captures dominated by moving objects, also apply masks during
COLMAP feature extraction and reconstruction.

Masks are resized with nearest-neighbor interpolation and follow image
undistortion, fisheye ROI cropping, and random training crops. L1 and PSNR are
reduced over valid pixels only. SSIM and LPIPS use identically zeroed invalid
regions, so values near mask boundaries should be treated as approximate.

It also supports a browser based viewer for real-time rendering, powered by 
`Viser <https://github.com/nerfstudio-project/viser>`_ and 
`nerfview <https://github.com/hangg7/nerfview>`_.

.. raw:: html

    <video class="video" autoplay="" loop="" muted="" playsinline="", width="100%", height="auto">
        <source src="../_static/viewer_garden_480p.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
