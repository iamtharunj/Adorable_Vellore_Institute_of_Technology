"""PrandialTwin: a self-updating physiological digital twin for post-meal hyperglycaemia."""
import os

# The twin works on small arrays; BLAS threads only fight the evaluation's worker processes.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
