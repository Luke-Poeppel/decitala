# -*- coding: utf-8 -*-
####################################################################################################
# File:     remake_analysis_files.py
# Purpose:  File for remaking the analysis (and later database) files from copyrighted compositions.
#
# Author:   Luke Poeppel
#
# Location: Kent, CT, 2021
####################################################################################################
import json

from decitala.fragment import (
	Decitala,
	FragmentEncoder
)

sh_00_training = [
	(Decitala("Vijaya"), (0.0, 4.0)),
	(Decitala("Sama"), (4.0, 5.75)),
	(Decitala("Simhavikrama"), (5.75, 13.25)),
	(Decitala("Sama"), (13.25, 15.0)),
	(Decitala("Vijaya"), (15.0, 19.0)),
	(Decitala("Gajajhampa"), (19.0, 20.875)),
	(Decitala("Sama"), (20.875, 22.625)),
	(Decitala("Candrakala"), (22.625, 30.625)),
	(Decitala("Gajajhampa"), (30.625, 32.5)),
	(Decitala("Lakskmica"), (32.5, 34.625)),
	(Decitala("Sama"), (34.625, 36.375)),
	(Decitala("Sama"), (36.375, 38.125)),
	(Decitala("Gajajhampa"), (38.125, 40.0)),
	(Decitala("Sama"), (40.0, 41.75)),
	(Decitala("Vijaya"), (41.75, 45.75)),
	(Decitala("Gajajhampa"), (45.75, 47.625)),
	(Decitala("Sama"), (47.625, 49.375)),
	(Decitala("Simhavikrama"), (49.375, 56.875)),
	(Decitala("Sama"), (56.875, 58.625)),
	(Decitala("Vijaya"), (58.625, 62.625)),
	(Decitala("Sama"), (62.625, 64.375))
]

sh_01_training = [
	(Decitala("Sama"), (0.0, 1.75)),
	(Decitala("Vijaya"), (1.75, 5.75)),
	(Decitala("Sama"), (5.75, 7.5)),
	(Decitala("Simhavikrama"), (7.5, 15.0)),
	(Decitala("Sama"), (15.0, 16.75)),
	(Decitala("Gajajhampa"), (16.75, 18.625)),
	(Decitala("Vijaya"), (18.625, 22.625)),
	(Decitala("Sama"), (22.625, 24.375)),
	(Decitala("Gajajhampa"), (24.375, 26.25)),
	(Decitala("Sama"), (26.25, 28.0)),
	(Decitala("Sama"), (28.0, 29.75)),
	(Decitala("Lakskmica"), (29.75, 31.875)),
	(Decitala("Gajajhampa"), (31.875, 33.75)),
	(Decitala("Candrakala"), (33.75, 41.75)),
	(Decitala("Sama"), (41.75, 43.5)),
	(Decitala("Gajajhampa"), (43.5, 45.375)),
	(Decitala("Vijaya"), (45.375, 49.375)),
	(Decitala("Sama"), (49.375, 51.125)),
	(Decitala("Simhavikrama"), (51.125, 58.625)),
	(Decitala("Sama"), (58.625, 60.375)),
	(Decitala("Vijaya"), (60.375, 64.375))
]

lit_3_4_training = [
	(Decitala("Ragavardhana"), (2.0, 6.75)),
	(Decitala("Candrakala"), (6.75, 10.75)),
	(Decitala("Lakskmica"), (10.75, 15.0)),
	(Decitala("Ragavardhana"), (15.0, 19.75)),
	(Decitala("Candrakala"), (19.75, 23.75)),
	(Decitala("Lakskmica"), (23.75, 28.0)),
	(Decitala("Ragavardhana"), (28.0, 32.75)),
	(Decitala("Candrakala"), (32.75, 36.75)),
	(Decitala("Lakskmica"), (36.75, 41.0)),
	(Decitala("Ragavardhana"), (41.0, 45.75)),
	(Decitala("Candrakala"), (45.75, 49.75)),
	(Decitala("Lakskmica"), (49.75, 54.0)),
	(Decitala("Ragavardhana"), (54.0, 58.75)),
	(Decitala("Candrakala"), (58.75, 62.75)),
	(Decitala("Lakskmica"), (62.75, 67.0)),
	(Decitala("Ragavardhana"), (67.0, 71.75)),
	(Decitala("Candrakala"), (71.75, 75.75)),
	(Decitala("Lakskmica"), (75.75, 80.0)),
	(Decitala("Ragavardhana"), (80.0, 84.75)),
	(Decitala("Candrakala"), (84.75, 88.75)),
	(Decitala("Lakskmica"), (88.75, 93.0)),
	(Decitala("Ragavardhana"), (93.0, 97.75)),
	(Decitala("Candrakala"), (97.75, 101.75)),
	(Decitala("Lakskmica"), (101.75, 106.0)),
	(Decitala("Ragavardhana"), (106.0, 110.75)),
	(Decitala("Candrakala"), (110.75, 114.75)),
	(Decitala("Lakskmica"), (114.75, 119.0)),
	(Decitala("Ragavardhana"), (119.0, 123.75)),
	(Decitala("Candrakala"), (123.75, 127.75))
]

ld_00_training = [
	(Decitala("Laya"), (0.0, 9.25)),
	(Decitala("Bhagna"), (9.25, 10.625)),
	(Decitala("Niccanka"), (10.625, 20.125)),
	(Decitala("Rangapradipaka"), (21.875, 28.125)),
	(Decitala("Caccari"), (28.125, 31.125)),
	(Decitala("Sama"), (31.125, 32.875)),
	(Decitala("Rangapradipaka"), (32.875, 38.5)),
	(Decitala("Sama"), (38.5, 40.25)),
	(Decitala("Caccari"), (40.25, 45.25)),
	(Decitala("Caccari"), (45.25, 52.25)),
	(Decitala("Sama"), (52.25, 54.0)),
	(Decitala("Rangapradipaka"), (54.0, 59.0)),
	(Decitala("Caccari"), (59.0, 68.0)),
	(Decitala("Rangapradipaka"), (68.0, 72.375)),
	(Decitala("Sama"), (72.375, 74.125)),
	(Decitala("Sama"), (74.125, 75.875)),
	(Decitala("Caccari"), (75.875, 86.875)),
	(Decitala("Rangapradipaka"), (86.875, 90.625)),
	(Decitala("Sama"), (90.625, 92.375)),
	(Decitala("Rangapradipaka"), (92.375, 95.5)),
	(Decitala("Caccari"), (95.5, 108.5)),
	(Decitala("Rangapradipaka"), (108.5, 111.625)),
	(Decitala("Sama"), (111.625, 113.375)),
	(Decitala("Rangapradipaka"), (113.375, 117.125)),
	(Decitala("Caccari"), (117.125, 128.125)),
	(Decitala("Sama"), (128.125, 129.875)),
	(Decitala("Sama"), (129.875, 131.625)),
	(Decitala("Rangapradipaka"), (131.625, 136.0)),
	(Decitala("Caccari"), (136.0, 145.0)),
	(Decitala("Rangapradipaka"), (145.0, 150.0)),
	(Decitala("Sama"), (150.0, 151.75)),
	(Decitala("Caccari"), (151.75, 158.75)),
	(Decitala("Caccari"), (158.75, 163.75)),
	(Decitala("Sama"), (163.75, 165.5)),
	(Decitala("Rangapradipaka"), (165.5, 171.125)),
	(Decitala("Sama"), (171.125, 172.875)),
	(Decitala("Caccari"), (172.875, 175.875)),
	(Decitala("Rangapradipaka"), (175.875, 182.125)),
	(Decitala("Caccari"), (182.125, 185.125)),
	(Decitala("Sama"), (185.125, 186.875)),
	(Decitala("Rangapradipaka"), (186.875, 192.5)),
	(Decitala("Sama"), (192.5, 194.25)),
	(Decitala("Caccari"), (194.25, 199.25)),
	(Decitala("Caccari"), (199.25, 206.25)),
	(Decitala("Sama"), (206.25, 208.0)),
	(Decitala("Rangapradipaka"), (208.0, 213.0)),
	(Decitala("Caccari"), (213.0, 222.0)),
	(Decitala("Rangapradipaka"), (222.0, 226.375)),
	(Decitala("Sama"), (226.375, 228.125)),
	(Decitala("Sama"), (228.125, 229.875)),
]

ld_01_training = [
	(Decitala("Laya"), (20.125, 38.125)),
	(Decitala("Niccanka"), (38.125, 46.625)),
	(Decitala("Bhagna"), (46.625, 48.0)),
	(Decitala("Bhagna"), (48.0, 49.375)),
	(Decitala("Niccanka"), (49.375, 56.875)),
	(Decitala("Laya"), (56.875, 83.625)),
	(Decitala("Bhagna"), (83.625, 85.0)),
	(Decitala("Laya"), (85.0, 120.5)),
	(Decitala("Niccanka"), (120.5, 127.0)),
	(Decitala("Niccanka"), (127.0, 132.5)),
	(Decitala("Bhagna"), (132.5, 133.875)),
	(Decitala("Laya"), (133.875, 178.125)),
	(Decitala("Niccanka"), (178.125, 182.625)),
	(Decitala("Laya"), (182.625, 235.625)),
	(Decitala("Bhagna"), (235.625, 237.0))
]

__ALL__ = {
	"/Users/lukepoeppel/decitala/databases/analyses/sept_haïkaï_0_analysis.json": sh_00_training,
	"/Users/lukepoeppel/decitala/databases/analyses/sept_haïkaï_1_analysis.json": sh_01_training,
	"/Users/lukepoeppel/decitala/databases/analyses/liturgie_3-4_analysis.json": lit_3_4_training,
	"/Users/lukepoeppel/decitala/databases/analyses/livre_dorgue_0_analysis.json": ld_00_training,
	"/Users/lukepoeppel/decitala/databases/analyses/livre_dorgue_1_analysis.json": ld_01_training,
}

if __name__ == "__main__":
	analyses_directory = "/Users/lukepoeppel/decitala/databases/analyses"
	for filename, data in __ALL__.items():
		formatted_data = []
		for fragment_onsets in data:
			fragment_dict = {"fragment": fragment_onsets[0], "onset_range": fragment_onsets[1]}
			formatted_data.append(fragment_dict)
		with open(filename, "w") as output:
			json.dump(obj=formatted_data, fp=output, cls=FragmentEncoder, ensure_ascii=False, indent=4)