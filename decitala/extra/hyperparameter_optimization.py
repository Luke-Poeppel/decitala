import numpy as np

from scipy.optimize import minimize

from decitala.path_finding import path_finding_utils
from decitala.utils import get_logger
from decitala.extra.hyperparameters import (
	test_all_transcriptions_on_single_point,
	test_all_works_on_single_point
)

logger = get_logger(
	__name__,
	print_to_console=True,
	write_to_file="/Users/lukepoeppel/decitala/decitala/extra/hyperparameters_works_and_transcriptions_0.01.txt" # noqa
)

def objective_function(params):
	print(params)
	res = []
	transcription_results = test_all_transcriptions_on_single_point(params)
	res.extend(transcription_results)
	composition_results = test_all_works_on_single_point(params)
	res.extend(composition_results)
	total_accurate = res[0] + res[3]
	total = res[1] + res[4]
	logger.info(f"TOTAL ACCURATE: {total_accurate}")
	logger.info(f"TOTAL: {total}")
	print()

	accuracy = (total_accurate / total) * 100
	return 1 / accuracy

def optimize_results():
	initial_point = np.array([0.825, 0.0875, 0.0875])
	cons = ({"type": "eq", "fun": lambda x: 1 - sum(x)})
	bnds = tuple((0, 1) for x in initial_point)
	res = minimize(
		objective_function,
		initial_point,
		method="SLSQP",
		options={"disp": True},
		bounds=bnds,
		constraints=cons,
	)
	logger.info(res)

# optimize_results()

def test_on_constricted_space():
	for point in path_finding_utils.make_3D_grid(resolution=0.01):
		if point[0] >= 0.75:
			print(point)
			res = []
			transcription_results = test_all_transcriptions_on_single_point(point)
			res.extend(transcription_results)
			composition_results = test_all_works_on_single_point(point)
			res.extend(composition_results)

			total_accurate = res[0] + res[3]
			total = res[1] + res[4]
			res = (point, "->", [total_accurate, total])
			logger.info(res)

# test_on_constricted_space()