import traci
import sumolib
from src.project.small_manhattan.traci_code import RoutingAlgorithms as routing

NORMAL_CONFIG = "project/small_manhattan/configuration_files/normal/config.cfg"
TEST_CONFIG = "project/small_manhattan/configuration_files/testing/config_test.cfg"
NET_FILE_TESTING = "project/small_manhattan/configuration_files/testing/small_manhattan.net.xml"
SUMO_BINARY = "D:/Program Files/SUMO/bin/sumo-gui.exe"

START_TIME = 0
END_TIME = 10000
ZOOM_FACTOR = 12

TESTING = True

net = sumolib.net.readNet(NET_FILE_TESTING)

@staticmethod
def getCurrentTime2():
    return traci.simulation.getCurrentTime()

class Main:

    @staticmethod
    def getCurrentTime():
        return traci.simulation.getCurrentTime()

    def run(self):
        # Defines the command to start SUMO with
        sumo = [SUMO_BINARY, '-c', TEST_CONFIG, '--step-length', '0.1']
        # Establish the Traci connection and run sumo cmd
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
    main = Main()
    main.run()


