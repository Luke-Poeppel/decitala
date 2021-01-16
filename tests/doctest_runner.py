"""
There are a number of doctests in the source, but they cannot be run in the 
standard way as the files have relative imports. As such, we may run them here. 
"""
from progress.bar import Bar

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
	logging.info("Running all doctests...")
	import doctest
	from decitala import (
		database,
		fragment,
		utils,
		trees,
		pofp,
	)
	all_modules = [database, fragment, utils, trees, pofp]
	with Bar("Running doctests", max=len(all_modules)) as bar:
		for module in all_modules:
			doctest.testmod(module)
			bar.next()