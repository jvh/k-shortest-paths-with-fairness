import traci
import sumolib
import os
from src.project.small_manhattan.traci_code import RoutingAlgorithms as routing

# Configuration files
NORMAL_CONFIG = "project/small_manhattan/configuration_files/normal/config.cfg"
TEST_CONFIG = "project/small_manhattan/configuration_files/testing/config_test.cfg"
NET_FILE_TESTING = "D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/" \
                  "pycharm_project/src/project/small_manhattan/configuration_files/testing/small_manhattan.net.xml"
SUMO_BINARY = "D:/Program Files/SUMO/bin/sumo-gui.exe"

# SUMO settings
START_TIME = 0
END_TIME = 10000
ZOOM_FACTOR = 12

# This specifies the number of incoming edges away (the range) from the original edge to search
MAX_EDGE_RECURSIONS_RANGE = 3

# Specifies if testing should take place
TESTING = True

# Passes the network file into sumolib for analysis and use
net = sumolib.net.readNet(NET_FILE_TESTING)

@staticmethod
def getCurrentTime2():
    return traci.simulation.getCurrentTime()

class Main:

    @staticmethod
    def getCurrentTime():
        return traci.simulation.getCurrentTime()

    def run(self):
        """ Starts the simulation """

        # Defines the command to start SUMO with
        sumo = [SUMO_BINARY, '-c', TEST_CONFIG, '--step-length', '0.1']
        # Establish the Traci connection and run SUMO command
        traci.start(sumo)

        test = routing.Testing()
        test.test1Before()

        for i in range(START_TIME, END_TIME):
            test.test1During(i)
            # print(traci.simulation.getCurrentTime())

        # Close the Sumo-Traci connection once the simulation has elapsed
        traci.close(False)


# The main method
if __name__ == '__main__':
    print(os.getcwd())
    main = Main()
    main.run()


