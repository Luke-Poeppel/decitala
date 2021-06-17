# import numpy as np

# from scipy.optimize import minimize, basinhopping

# from decitala import search
# from decitala.hash_table import GreekFootHashTable
# from decitala.path_finding.dijkstra import dijkstra_best_source_and_sink
# from decitala.utils import get_logger
# from decitala.path_finding.path_finding_utils import (
# 	CostFunction,
# 	CostFunction3D,
# 	DefaultCostFunction,
# 	sources_and_sinks,
# 	make_3D_grid
# )

# from moiseaux.db import (
# 	get_all_transcriptions,
# 	Transcription
# )

# logger = get_logger(
# 	__name__,
# 	print_to_console=True,
# 	write_to_file="/Users/lukepoeppel/cost3d_01.txt"
# )

# def check_accuracy(training_data, calculated_data, mode):
# 	"""
# 	The `training_data` is the analysis as provided by Messiean. The `input_data`
# 	is the data calculated by Dijkstra path-finding.
# 	NOTE: the data is stored in two different formats, hence the use of `mode`.
# 	"""
# 	accuracy = 0
# 	for this_training_fragment in training_data:
# 		for this_fragment in calculated_data:
# 			if mode == "Compositions":
# 				if (this_training_fragment["fragment"] == this_fragment.fragment) and (tuple(this_training_fragment["onset_range"]) == this_fragment.onset_range): # noqa
# 					accuracy += 1
# 			elif mode == "Transcriptions":
# 				if (this_training_fragment[0] == this_fragment.fragment) and (tuple(this_training_fragment[1]) == this_fragment.onset_range): # noqa
# 					accuracy += 1

# 	return accuracy, len(training_data)

# def objective_function(params):
# 	cf = CostFunction3D(*params)
# 	res = []
# 	for transcription in get_all_transcriptions():
# 		if transcription.name == "Ex114":
# 			continue
# 		if transcription.analysis:
# 			logger.info(transcription)
# 			path = search.path_finder(
# 				filepath=transcription.filepath,
# 				part_num=0,
# 				table=GreekFootHashTable(),
# 				allow_subdivision=True,
# 				cost_function_class=cf
# 			)
# 			analysis = transcription.analysis
# 			accurate, total = check_accuracy(
# 				training_data=analysis,
# 				calculated_data=path,
# 				mode="Transcriptions"
# 			)
# 			res.append((accurate, total))

# 	total_accurate = sum([x[0] for x in res])
# 	total = sum([x[1] for x in res])
# 	logger.info(f"TOTAL ACCURATE: {total_accurate}")
# 	logger.info(f"TOTAL: {total}")
# 	return (total_accurate / total) * 100 # Multiply by -1 if optimizing with scipy optimize.

# for point in make_3D_grid(resolution=0.1):
# 	logger.info(f"POINT: {point}")
# 	logger.info(objective_function(point))

# params = np.array([0.7, 0.3, 0.08, 1.84])
# res = basinhopping(
# 	objective_function,
# 	params,
# 	niter=10,
# 	stepsize=0.5
# )
# print(res)
# history = []
# def callback(params):
#     fobj = objective_function(params)
#     history.append(fobj)

# # Should optimize this
# params = np.array([0.7, 0.3, 0.08, 1.84])
# res = minimize(
# 	objective_function,
# 	params,
# 	method='nelder-mead',
# 	options={'xatol': 1e-8, 'disp': True, "maxiter": 50},
# 	callback=callback,
# )
# print(res)
# print(history)


# def rosen(x):
# 	return sum(100.0*(x[1:]-x[:-1]**2.0)**2.0 + (1-x[:-1])**2.0)

# x0 = np.array([1.3, 0.7, 0.8, 1.9, 1.2])
# res = minimize(rosen, x0, method='nelder-mead',
# 			   options={'xatol': 1e-8, 'disp': True})
# print(res)