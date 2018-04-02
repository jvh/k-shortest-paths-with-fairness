import traci
import sumolib
import os
import datetime
from src.project.code import RoutingAlgorithms as routing


# True if using main computer
COMPUTER = True


# Main computer project configuration location
MAIN_PROJECT = "D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/" \
                  "pycharm_project/src/project/configuration_files/"
# Laptop project location
LAPTOP_PROJECT = "FILL ME"

if COMPUTER:
    SUMO_BINARY = "D:/Program Files/SUMO/bin/sumo-gui.exe"
    # SUMO Configuration files
    OUTPUT_DIRECTORY = "D:/Nina/Documents/google_drive/sumo/sumo_output/"
    SM_CONFIG = MAIN_PROJECT + "small_manhattan/normal/small_manhattan_config.cfg"
    TEST_SM_CONFIG = MAIN_PROJECT + "small_manhattan/testing/small_manhattan_test.cfg"
    NEWARK_CONFIG = MAIN_PROJECT + "newark/normal/newark_config.cfg"
    NET_FILE_SM = MAIN_PROJECT + "small_manhattan/small_manhattan.net.xml"
    NET_FILE_NEWARK = MAIN_PROJECT + "newark/normal/newark.net.xml"
    VEHICLES_FILE = MAIN_PROJECT + "vehicles.xml"
    GUI_SETTINGS = MAIN_PROJECT + "gui.settings.xml"
else:
    SUMO_BINARY = "D:/Program Files/SUMO/bin/sumo-gui.exe"
    # SUMO Configuration files
    NORMAL_CONFIG = LAPTOP_PROJECT + "configuration_files/small_manhattan/normal/config.cfg"
    TEST_SMALL_MANHATTAN = LAPTOP_PROJECT + "configuration_files/small_manhattan/testing/config_test.cfg"
    NET_FILE_NEWARK = LAPTOP_PROJECT + "configuration_files/small_manhattan/normal/newark.net.xml"

# SUMO settings
START_TIME = 0
END_TIME = 10000
ZOOM_FACTOR = 12
STEP_LENGTH = '0.1'

# This specifies the number of incoming edges away (the range) from the original edge to search
MAX_EDGE_RECURSIONS_RANGE = 3

# Specifies the scenario (map)
#   0: Testing (small_manhattan)
#   1: small_manhattan
#   2: newark
SCENARIO = 0
# Specifies output file, true = output generated
#   --summary: Prints out a summary of the information into an .xml file
SUMMARY_OUTPUT = True
# Specifies the rerouting algorithm to be ran
#   0: No rerouting
#   1: Dynamic shortest path (DSP)
ALGORITHM = 1

# Passes the network file into sumolib for analysis and use
net = sumolib.net.readNet(NET_FILE_SM)

@staticmethod
def getSumolibNet():
    return Main.net2

@staticmethod
def getCurrentTime2():
    return traci.simulation.getCurrentTime()

class Main:

    @staticmethod
    def getCurrentTime():
        return traci.simulation.getCurrentTime()

    def configureSumo(self, sumoConfig):
        """
        This allows for the configuration of SUMO to be done based on the scenario picked and additional options
        selected

        Args:
            sumoConfig (str[]): This is the initial list of global arguments shared by all scenarios and any additional
             options
        Return:
            str[]: The new configuration of SUMO based upon the options selected
        """

        net2 = 'meep'

        # Current date-time
        currentDateTime = "{}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # Current date-time in a Windows friendly format
        windowsDateTime = currentDateTime.replace(" ", "_").replace(":", "h-", 1).replace(":", "m", 1)[:-2]

        # Output directories
        summaryOut = OUTPUT_DIRECTORY + '{}/summary/summary_{}.xml'

        # Choosing the scenario
        sumoConfig.insert(1, "-c")
        # Small manhattan test
        if SCENARIO == 0:
            sumoConfig.insert(2, TEST_SM_CONFIG)
            # Outputs
            if SUMMARY_OUTPUT:
                sumoConfig.append("--summary")
                sumoConfig.append(summaryOut.format('small_manhattan/test', windowsDateTime))
        # Small manhattan
        elif SCENARIO == 1:
            sumoConfig.insert(2, SM_CONFIG)
            # Outputs
            if SUMMARY_OUTPUT:
                sumoConfig.append("--summary")
                sumoConfig.append(summaryOut.format('small_manhattan/normal', windowsDateTime))
        # Newark
        else:
            sumoConfig.insert(2, NEWARK_CONFIG)
            # Outputs
            if SUMMARY_OUTPUT:
                sumoConfig.append("--summary")
                sumoConfig.append(summaryOut.format('newark/normal', windowsDateTime))

        return sumoConfig


    def run(self):
        """
        Starts the simulation
        """
        # Defines the command to start SUMO with
        #   --net-file: The SUMO network file to be used (.net.xml)
        #   --step-length: Defines the length of each timestep in seconds
        #   --additional-files: Allows for additional files to be input into the configuration

        #   --routing-algorithm: Defines the routing algorithm used by the vehicles
        #   --gui-settings-file: Allows for the GUI to be manipulated
        #   --device.rerouting.probability: Defines the probability that a vehicle in the simulation will automatically
        # reroute
        sumoConfigInitial = [SUMO_BINARY, '--net-file', NET_FILE_SM, '--step-length', STEP_LENGTH, '--additional-files',
                             VEHICLES_FILE, '--routing-algorithm', 'dijkstra', '--gui-settings-file', GUI_SETTINGS,
                             '--device.rerouting.probability', '1.0']

        sumoConfig = self.configureSumo(sumoConfigInitial)


        sumoWorks = [SUMO_BINARY, '-c', SM_CONFIG, '--step-length', STEP_LENGTH, '--additional-files', VEHICLES_FILE,
                '--routing-algorithm', 'dijkstra', '--gui-settings-file', GUI_SETTINGS,
                '--summary', OUTPUT_DIRECTORY + 'summary_scenario-{}_{}.xml'.format(SCENARIO, 'windowsDateTime')]





        traci.start(sumoConfig)

        test = routing.Testing()
        dsp = routing.DynamicShortestPath()

        if SCENARIO == 0:
            test.beforeLoop()

            for i in range(START_TIME, END_TIME):
                test.duringLoop(i)
        else:
            if ALGORITHM == 0:
                print("no rerouting")
            elif ALGORITHM == 1:
                print("Dsp")

        # Close the Sumo-Traci connection once the simulation has elapsed
        traci.close(False)


# The main method
if __name__ == '__main__':
    print("This is the current working directory: {})".format(os.getcwd()))
    main = Main()
    main.run()


