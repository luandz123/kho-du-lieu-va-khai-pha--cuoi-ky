"""
Smoke tests for P2 isolated environment.
Verifies Python runtime, required packages, and core ML/Matrix computation routines.
"""
import sys
import numpy as np
import pandas as pd
import scipy
import scipy.sparse as sp
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity


def test_python_version():
    """Verify Python runtime is 3.12+."""
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 12, f"Expected Python >= 3.12, got {sys.version}"


def test_core_libraries_imported():
    """Verify essential packages are installed and report versions."""
    assert np.__version__ is not None
    assert pd.__version__ is not None
    assert scipy.__version__ is not None


def test_sparse_matrix_and_similarity():
    """Verify sparse matrix manipulation and cosine similarity (foundation for Item-based CF)."""
    # Create small mock user-item sparse matrix (5 users, 4 items)
    data = np.array([5.0, 4.0, 3.0, 1.0, 2.0, 5.0])
    row = np.array([0, 0, 1, 1, 2, 3])
    col = np.array([0, 1, 1, 2, 2, 3])
    user_item = sp.csr_matrix((data, (row, col)), shape=(5, 4))

    # Item-item similarity (items as rows)
    item_user = user_item.T
    sim = cosine_similarity(item_user, dense_output=True)

    assert sim.shape == (4, 4)
    # Self-similarity should be 1.0
    for i in range(4):
        assert np.isclose(sim[i, i], 1.0) or sim[i, i] == 0.0


def test_kmeans_execution():
    """Verify KMeans algorithm works (foundation for Q1 User Clustering)."""
    # Mock user-genre preference data (10 users, 3 genres)
    rng = np.random.RandomState(42)
    mock_profiles = rng.rand(10, 3)
    # Normalize row sums to 1.0
    mock_profiles = mock_profiles / mock_profiles.sum(axis=1, keepdims=True)

    kmeans = KMeans(n_clusters=2, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(mock_profiles)

    assert len(labels) == 10
    assert set(np.unique(labels)).issubset({0, 1})
    assert kmeans.cluster_centers_.shape == (2, 3)
