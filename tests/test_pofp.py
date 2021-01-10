import pytest

from decitala.pofp import (
    check_break_point,
    get_break_points,
    get_pareto_optimal_longest_paths
)
from decitala.fragment import (
	GeneralFragment,
	GreekFoot
)

# TODO (old format)
@pytest.fixture
def data():
	sh_data = [
		(('info_0',), (0.0, 4.0)), (('info_1',), (2.5, 4.75)), (('info_2',), (4.0, 5.25)), 
		(('info_3',), (4.0, 5.75)), (('info_4',), (5.75, 9.75)), (('info_5',), (5.75, 13.25)), 
		(('info_6',), (8.25, 11.25)), (('info_7',), (8.25, 13.25)), (('info_8',), (9.75, 12.25)), 
		(('info_9',), (10.25, 13.25)), (('info_10',), (13.25, 14.5)), (('info_11',), (13.25, 15.0)), 
		(('info_12',), (15.0, 19.0)), (('info_13',), (19.0, 19.875)), (('info_14',), (19.0, 20.875)), 
		(('info_15',), (19.375, 20.875)), (('info_16',), (20.875, 22.125)), (('info_17',), (20.875, 22.625)), 
		(('info_18',), (21.625, 23.125)), (('info_19',), (22.625, 30.625)), (('info_20',), (23.125, 27.625)), 
		(('info_21',), (24.625, 29.625)), (('info_22',), (26.125, 29.625)), (('info_23',), (26.125, 30.625)), 
		(('info_24',), (27.625, 30.625)), (('info_25',), (30.625, 31.5)), (('info_26',), (30.625, 32.5)), 
		(('info_27',), (31.0, 32.5)), (('info_28',), (31.0, 33.5)), (('info_29',), (31.5, 34.0)), 
		(('info_30',), (32.5, 34.625)), (('info_31',), (34.0, 35.0)), (('info_32',), (34.625, 35.875)), 
		(('info_33',), (34.625, 36.375)), (('info_34',), (35.375, 37.125)), (('info_35',), (35.875, 37.125)), 
		(('info_36',), (36.375, 37.625)), (('info_37',), (36.375, 38.125)), (('info_38',), (38.125, 39.0)), 
		(('info_39',), (38.125, 40.0)), (('info_40',), (38.5, 40.0)), (('info_41',), (40.0, 41.25)), 
		(('info_42',), (40.0, 41.75)), (('info_43',), (41.75, 45.75)), (('info_44',), (45.75, 46.625)), 
		(('info_45',), (45.75, 47.625)), (('info_46',), (46.125, 47.625)), (('info_47',), (47.625, 48.875)), 
		(('info_48',), (47.625, 49.375)), (('info_49',), (49.375, 53.375)), (('info_50',), (49.375, 56.875)), 
		(('info_51',), (51.875, 54.875)), (('info_52',), (51.875, 56.875)), (('info_53',), (53.375, 55.875)), 
		(('info_54',), (53.875, 56.875)), (('info_55',), (56.875, 58.125)), (('info_56',), (56.875, 58.625)), 
		(('info_57',), (58.625, 62.625)), (('info_58',), (61.125, 63.375)), (('info_59',), (62.625, 63.875)), 
		(('info_60',), (62.625, 64.375))
	]
	return sh_data

class _TestSeptHaikaiData:
	def _test_check_break_point(self, data):
		assert check_break_point(data, 10) == True # checks info_10 starts new section.
	
	def _test_get_break_points(self, data):
		break_points = [4, 10, 12, 13, 16, 25, 38, 41, 43, 44, 47, 49, 55, 57]
		assert break_points == get_break_points(data)
	
	def _test_get_pareto_optimal_longest_paths(self, data):
		random_start = 23
		random_stop = 29
		data_excerpt = data[random_start:random_stop + 1]
		paths = get_pareto_optimal_longest_paths(data_excerpt)

		assert paths[0] == [[('info_23',), (26.125, 30.625)], [('info_25',), (30.625, 31.5)], [('info_29',), (31.5, 34.0)]]