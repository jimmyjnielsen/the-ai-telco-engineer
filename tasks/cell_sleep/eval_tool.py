"""EvalTool for the cell sleep scheduling task."""

import shlex
from pathlib import Path

from tool_lib.base import ToolProvider
from tool_lib.workspace import Workspace
from langchain_core.tools import tool, BaseTool


_EVAL_SCRIPT = Path(__file__).parent / "eval/eval.py"
_UTILS_SCRIPT = Path(__file__).parent / "eval/utils.py"


class EvalTool(ToolProvider):
    """Evaluates an agent's cell sleep scheduling policy.

    Copies the simulator harness into the agent workspace, runs
    ``python eval.py draft.py``, and returns a scored result.
    """

    _DEFAULT_SOURCE_FILE = "draft.py"

    def __init__(self, eval_timeout: int = 120):
        self._eval_timeout = eval_timeout
        self._workspace = None
        self.evaluate_sleep_policy = tool(self._evaluate_sleep_policy)

    def _evaluate_sleep_policy(self) -> str:
        """Evaluate the cell sleep scheduling policy in draft.py.

        Runs the policy across three 24-hour traffic scenarios on a 7-cell
        hexagonal network and measures net energy savings after switching costs.

        Before calling this tool the agent must create a file called
        ``draft.py`` in the workspace that defines::

            def sleep_policy(traffic_loads: np.ndarray,
                             neighbor_matrix: np.ndarray,
                             prev_active: np.ndarray) -> np.ndarray:

        Function contract
        ~~~~~~~~~~~~~~~~~
        traffic_loads : np.ndarray, shape (N,)
            Effective PRB utilisation for each of the N cells, including traffic
            offloaded from sleeping neighbours in the previous time step.  Active
            cells carry their own load plus an equal share of each sleeping
            neighbour's load; values may exceed 1.0 under heavy offloading.
        neighbor_matrix : np.ndarray, shape (N, N)
            Binary adjacency matrix — entry [i, j] is 1 if cells i and j
            are neighbours, 0 otherwise.
        prev_active : np.ndarray, shape (N,)
            Active/sleep state at the previous time step (1 = active, 0 = sleep).
            All-ones at t=0 (network starts fully active).

        Returns
        -------
        np.ndarray, shape (N,)
            Binary sleep decisions: 1 = cell stays active, 0 = cell sleeps.

        Constraints (violations → FAILURE)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        * Coverage: every sleeping cell must have at least one active neighbour.
        * Overload: no active cell's effective PRB utilisation (own traffic +
          equal share of each sleeping neighbour's traffic) may exceed 0.8.
          Sleeping a busy cell concentrates its load on active neighbours.

        Metric
        ~~~~~~
        Net energy savings = (sleeping cell-steps − 2 × total transitions) / (N × T) × 100 %.
        Each active↔sleep transition incurs a penalty of SWITCH_COST=2 cell-steps.
        Higher is better.  Reference values:
          0 % — always active baseline
          ~40–50 % — stateless threshold policy (frequent toggling penalised)
          > 65 % — smooth temporal policy (long contiguous sleep periods)
        Use prev_active to avoid unnecessary transitions: keep a sleeping cell asleep
        if load is still low rather than waking and immediately re-sleeping it.
        """
        return self._run(self._DEFAULT_SOURCE_FILE)

    def _run(self, source_file: str) -> str:
        if self._workspace is None:
            raise ValueError("Workspace not set")

        for src, dst in [(_EVAL_SCRIPT, "eval.py"), (_UTILS_SCRIPT, "utils.py")]:
            with open(src) as f:
                self._workspace._write_file(dst, f.read())

        cmd = f"python eval.py {shlex.quote(source_file)}"
        success, output = self._workspace._exec(cmd, timeout=self._eval_timeout)
        result = output if success else f"Error running eval:\n{output}"

        for dst in ["eval.py", "utils.py"]:
            self._workspace._delete(dst)

        return result

    def run_evaluation(self, filename: str) -> str:
        return self._run(filename)

    def get_tools(self) -> list[BaseTool]:
        return [self.evaluate_sleep_policy]

    def set_workspace(self, workspace: Workspace):
        self._workspace = workspace
