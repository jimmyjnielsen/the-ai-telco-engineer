"""Cell topology and traffic generation utilities for the cell sleep task."""

import numpy as np

# PRB overhead for offloaded traffic.  Users served by a neighbouring BS
# experience higher path loss and lower SINR, requiring a lower MCS and
# therefore more PRBs to carry the same data rate.  A factor of 2.0 is
# consistent with typical 3GPP macro-cell system-level assumptions (path loss
# exponent ~3.5, inter-site distance ~500 m).
OFFLOAD_OVERHEAD = 2.0


def make_hex_topology():
    """Return (positions, neighbor_matrix) for a 7-cell hexagonal layout.

    Cell 0 is the centre; cells 1-6 form the surrounding ring, evenly spaced
    at unit distance.  Two cells are neighbours iff their distance is < 1.1.
    """
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]
    positions = np.vstack([[0.0, 0.0], np.column_stack([np.cos(angles), np.sin(angles)])])

    N = len(positions)
    dists = np.linalg.norm(positions[:, None] - positions[None, :], axis=-1)
    neighbor_matrix = ((dists < 1.1) & (dists > 0)).astype(int)
    return positions, neighbor_matrix


def compute_effective_loads(own_loads: np.ndarray,
                            active: np.ndarray,
                            neighbor_matrix: np.ndarray) -> np.ndarray:
    """Compute effective PRB utilisation including offloaded traffic.

    When a cell sleeps, its users are handed off to active neighbours.
    Because the neighbours are farther away, the link quality is worse and
    the same traffic requires OFFLOAD_OVERHEAD times as many PRBs.  The
    offloaded share is split equally across all active neighbours.

    Parameters
    ----------
    own_loads : np.ndarray, shape (N,)
        Raw PRB utilisation of each cell (before offloading).
    active : np.ndarray, shape (N,)
        Binary active/sleep state (1 = active, 0 = sleeping).
    neighbor_matrix : np.ndarray, shape (N, N)
        Binary adjacency matrix.

    Returns
    -------
    np.ndarray, shape (N,)
        Effective PRB utilisation.  Values may exceed 1.0 when a cell is
        overloaded by concentrated offloaded traffic.
    """
    N = len(own_loads)
    effective = own_loads.astype(float).copy()
    for i in range(N):
        if active[i] == 0:  # sleeping — offload its traffic
            active_nbrs = np.where((neighbor_matrix[i] == 1) & (active == 1))[0]
            if len(active_nbrs) > 0:
                share = own_loads[i] * OFFLOAD_OVERHEAD / len(active_nbrs)
                effective[active_nbrs] += share
    return effective


def generate_traffic(N: int, T: int, seed: int = 42) -> np.ndarray:
    """Generate synthetic PRB utilisation traces for N cells over T steps.

    Each cell gets a sinusoidal daily pattern (period = T) with a random
    phase and amplitude, plus small Gaussian noise.  Values are clipped to
    [0, 1].

    Parameters
    ----------
    N : int
        Number of cells.
    T : int
        Number of time steps (e.g. 288 for 5-min intervals over 24 h).
    seed : int
        RNG seed for reproducibility.

    Returns
    -------
    np.ndarray, shape (T, N)
        PRB utilisation in [0, 1] for each cell at each time step.
    """
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, T)
    traffic = np.zeros((T, N))

    # AR(1) noise parameters: ρ=0.9 gives ~10-step (50 min) correlation time,
    # matching realistic traffic fluctuation timescales.
    rho = 0.9
    sigma_eps = 0.02  # steady-state std ≈ 0.02 / sqrt(1 - 0.81) ≈ 0.046

    for i in range(N):
        phase = rng.uniform(0, 2 * np.pi)
        amplitude = rng.uniform(0.25, 0.55)
        offset = rng.uniform(0.15, 0.45)
        eps = rng.normal(0, sigma_eps, T)
        noise = np.zeros(T)
        for k in range(1, T):
            noise[k] = rho * noise[k - 1] + eps[k]
        traffic[:, i] = np.clip(amplitude * np.sin(t + phase) + offset + noise, 0.0, 1.0)
    return traffic
