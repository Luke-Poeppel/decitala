"""
There are a number of doctests in the source, but they cannot be run in the 
standard way as the files have relative imports. As such, we may run them here. 
"""
import doctest
import sys

from decitala import (
	database,
	fragment,
	utils,
	trees,
	search,
	hash_table
)
from decitala.path_finding import (
	dijkstra,
	floyd_warshall,
	path_finding_utils,
	pofp
)
ALL_MODULES = [database, fragment, utils, trees, search, hash_table, dijkstra, floyd_warshall, path_finding_utils]#, pofp]

logger = utils.get_logger(__file__)

def doctest_runner(module=None):
	if module:
		logger.info("Testing: {}".format(module))
		logger.info(doctest.testmod(module))
	else:
		logger.info("Running all doctests...")
		for this_module in ALL_MODULES:
			logger.info("Testing: {}".format(this_module))
			logger.info(doctest.testmod(this_module))

if __name__ == "__main__":
	try:
		arg_in = sys.argv[1]
		if arg_in:
			mod = globals()[arg_in]
			doctest_runner(module=mod)
	except IndexError:
		doctest_runner()