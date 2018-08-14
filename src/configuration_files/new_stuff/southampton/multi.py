if __name__ == '__main__':
	# 0: Southampton
	# 1: Luton
	# 2: Bournemouth
	SCENARIO = 0

	RECURSION_NUM = 30

	if SCENARIO == 0:
		NET = 'southampton.net.xml'
		NAME = 'southampton'
		PERIOD = '0.205'
	elif SCENARIO == 1:
		NET = 'luton.net.xml'
		NAME = 'luton'
		PERIOD = '0.28'
	elif SCENARIO == 2:
		NET = 'bournemouth.net.xml'
		NAME = 'bournemouth'
		PERIOD = '0.4'

	import glob, subprocess, os
	# Getting current directory
	dir_path = os.path.dirname(os.path.realpath(__file__))
	# Walks through subdirectories from the current directory

	for x in range(RECURSION_NUM):
		subprocess.call(['/Users/jonathan/Documents/comp3200/sumo/tools/randomTrips.py', 
			'-n', NET,
			'-e', '7200',
			'--fringe-factor', '1',
			'--period', PERIOD,
			'--binomial', '30',
			'--min-distance', '1000',
			'--route-file', 'routes_{}_2hours_{}.xml'.format(NAME, x+1)])
	

