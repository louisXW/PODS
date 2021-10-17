"""
.. module:: controller
   :synopsis: Basic controller classes for asynchronous optimization.
.. moduleauthor:: David Bindel <bindel@cornell.edu>
"""

import logging
import time


# Get module-level logger
logger = logging.getLogger(__name__)


class MultiproController(object):
    """Multiprocessing-based sychronous controller for simple master-slave parallelization framework.

    Attributes:
        strategy: Strategy for choosing optimization actions.
        fbest: The best solution found so far
    """

    def __init__(self):
        "Initialize the Multiprocontroller."
        logger.debug("Initialize controller")
        self.strategy = None

    def _run(self, merit=None, filter=filter):
        "Run the optimization and return the best value."
        # proposal = self.strategy.propose_action()
        while True:
            current_time = time.time()
            if self.strategy.numeval >= self.strategy.maxeval or (current_time - self.strategy.start_time) >= self.strategy.time_budget:
                return "Optimization finished", "Best solution found: %s@%s" %(self.strategy.fbest_global, self.strategy.xbest_global)
                break

            else:
                self.strategy.iteration = self.strategy.iteration + 1
                self.strategy.start_batch()
                self.strategy.numeval_old = self.strategy.numeval  # modified 2017 0918

    def run(self, merit=None, filter=None):
        """Run the optimization and return the best value.

        Args:
            merit: Function to minimize (default is r.value)
            filter: Predicate to use for filtering candidates

        Returns:
            Record minimizing merit() and satisfying filter();
            or None if nothing satisfies the filter
        """
        try:
            return self._run(merit=merit, filter=filter)
        finally:
            print ("finihsed optimization")



