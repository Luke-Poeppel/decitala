"""
There are a number of doctests in the source, but they cannot be run in the 
standard way as the files have relative imports. As such, we may run them here. 
"""
import doctest

from decitala.utils import get_logger
logger = get_logger(__file__)

def doctest_runner():
	logger.info("Running all doctests...")
	from decitala import (
		database,
		fragment,
		utils,
		trees,
		search,
		hash_table
	)
	all_modules = [hash_table]#, database, utils, hash_table, trees, fragment, search]
	for module in all_modules:
		logger.info("Testing: {}".format(module))
		fail_count, test_count = doctest.testmod(module)
		if fail_count != 0:
			logger.info("{} has doctest failures!".format(module))
			return False
		else:
			continue

if __name__ == "__main__":
	doctest_runner()