import numpy as np

from scipy.optimize import minimize

from decitala.utils import get_logger

from decitala.extra.hyperparameters import (
	test_all_transcriptions_on_single_point,
	test_all_works_on_single_point
)

logger = get_logger(
	__name__,
	print_to_console=True,
	write_to_file="/Users/lukepoeppel/decitala/decitala/extra/hp_optimization.txt"
)

def objective_function(params):
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

# print(objective_function([0.8, 0.1, 0.1]))

def run_nelder_meade():
	history = []

	def callback(params):
		fobj = objective_function(params)
		history.append(fobj)

	# Should optimize this.
	initial_point = np.array([0.8, 0.1, 0.1])
	res = minimize(
		objective_function,
		initial_point,
		method="nelder-mead",
		options={"xatol": 1e-8, "disp": True, "maxiter": 2},
		callback=callback,
	)
	logger.info(res)
	logger.info(history)