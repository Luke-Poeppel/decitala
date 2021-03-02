"""
There are a number of doctests in the source, but they cannot be run in the 
standard way as the files have relative imports. As such, we may run them here. 
"""
from decitala.utils import get_logger
logger = get_logger(__file__)

if __name__ == "__main__":
	logger.info("Running all doctests...")
	import doctest
	from decitala import (
		database,
		fragment,
		utils,
		trees,
		search
	)
	all_modules = [database, fragment, utils, trees, search]
	for module in all_modules:
		logger.info("Testing: {}".format(module))
		fail_count, test_count = doctest.testmod(module)
		if fail_count != 0:
			raise Exception("{} has doctest failures!".format(module))