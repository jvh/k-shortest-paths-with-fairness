import traci
import sumolib
import os
import datetime
import sys

import src.project.code.Testing
from src.project.code import RoutingAlgorithms as routing
from src.project.code import HelperFunctions as func

# True if using main computer (allows for easy switching between laptop and main home computer)
COMPUTER = True

# These are the times between the simulation start and end, delay MUST be set at 0ms for this to be comparable to other
# results
timerStart = 0
timerEnd = 0

# Settings main working directory
if COMPUTER:
    # Main computer project configuration location
    MAIN_PROJECT = "D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/" \
                   "pycharm_project/src/project/configuration_files/"
    SUMO_BINARY = "D:/Program Files/SUMO/bin/sumo-gui.exe"
else:
    # Laptop project configuration location
    MAIN_PROJECT = "FILL ME"
    SUMO_BINARY = "FILL ME"

# TODO
# Remove the edges which are the insertions of the map to only facilitate at most one edge (so that vehicles don't pack
#   up on that single edge
# The simulation itself always runs on a single core. However, routing in SUMO or DUAROUTER can be parallelized by
#   setting the option --device.rerouting.threads <INT> and --routing-threads <INT> respectively.
# The python TraCI library allows controlling multiple simulations from a single script either by calling traci.connect
#   and storing the returned connection object or by calling traci.start(label=...) and retrieving the connection object
#   with traci.getConnection(label).
# Change from dijkstras to a*
# Think about subscriptions
# Add in 'tau' into the vehicles.xml (driver's reaction time)
# Edges might not be the best solution when choosing where congestion occurs because an edge can contain a number of
# lanes which go to certain intersections, for example a left edge may invite a left turn, whereas a right edge may
# invite a right turn. This means that a single lane on an edge may be congested whereas the other lane may not be. See
# img1.png for a good representation of this exact thing
# Write about using sets over lists for some things (NOT OWN WORDS BELOW)
#           * since the in operator is O(n) on a list but O(1) on a set
#           * Sets are significantly faster when it comes to determining if an object is present in the set (as in x in
#             s), but are slower than lists when it comes to iterating over their contents.

# SUMO Configuration files
OUTPUT_DIRECTORY = "D:/Nina/Documents/google_drive/sumo/sumo_output/"
SM_CONFIG = MAIN_PROJECT + "small_manhattan/normal/small_manhattan_config.cfg"
TEST_SM_CONFIG = MAIN_PROJECT + "small_manhattan/testing/small_manhattan_test.cfg"
NEWARK_CONFIG = MAIN_PROJECT + "newark/normal/newark_config.cfg"
TEST_NEWARK_CONFIG = MAIN_PROJECT + "newark/testing/newark_test_config.cfg"
NET_FILE_SM = MAIN_PROJECT + "small_manhattan/small_manhattan.net.xml"
NET_FILE_NEWARK = MAIN_PROJECT + "newark/newark.net.xml"
VEHICLES_FILE = MAIN_PROJECT + "vehicles.xml"
GUI_SETTINGS = MAIN_PROJECT + "gui.settings.xml"

# Whether or not to calculate the A* distances for this map
A_STAR_DISTANCES = True

# SUMO settings
START_TIME = 0
END_TIME = 1000000
ZOOM_FACTOR = 12
# Each step is 1 second
STEP_LENGTH = '1.0'

# This specifies the number of incoming edges away (the range) from the original edge to search
MAX_EDGE_RECURSIONS_RANGE = 3
# Specifies the number of up to k alternative routes
K_MAX = 3

# Specifies the scenario (map)
#   0: Testing (small_manhattan)
#   1: small_manhattan
#   2: newark
#   3: Testing (newark)
SCENARIO = 0
# Specifies the rerouting algorithm to be ran
#   0: No rerouting
#   1: Dynamic shortest path (DSP)
#   2: k-Shortest Path
#   3: Dynamic Rerouting with Fairness
ALGORITHM = 1

# Specifies output file (.xml), True = output generated
# An easy way to turn off all outputs, False = No outputs generated
OUTPUTS = False
#   --summary: Prints out a summary of the information
SUMMARY_OUTPUT = True
#   --full-output: Builds a file containing the full dump of various information regarding the positioning of vehicles
VEHICLE_FULL_OUTPUT = False
#   --vtk-output: Builds a VTK output which can be interpreted by tools such as Paraview
VTK_OUTPUT = False
#   --fcd-output: Floating car data, outputs information about the vehicle, similar to a GPS output
FLOATING_CAR_DATA_OUTPUT = True
#   --tripinfo-output: Generates information about the vehicle trips
TRIPS_OUTPUT = True

# Small manhattan
if SCENARIO == 0 or SCENARIO == 1:
    # Passes the network file into sumolib for analysis and use
    net = sumolib.net.readNet(NET_FILE_SM)
# Newark
elif SCENARIO == 2 or SCENARIO == 3:
    net = sumolib.net.readNet(NET_FILE_NEWARK)
else:
    sys.exit("Please enter a valid SCENARIO number")


class Main:
    """
    The class in which most of the SUMO configuration occurs, along with Traci configuration to communicate with SUMO
    at runtime
    """

    @staticmethod
    def getCurrentTime():
        """
        Returns the current simulation time (also convert from ms to seconds)
        Return:
            int: The current time of the simulation in seconds
        """
        return int(traci.simulation.getCurrentTime()/1000)

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
        # Input validation
        if (SCENARIO == 1 or SCENARIO == 2) and not (0 <= ALGORITHM <= 3):
            sys.exit("Please enter a valid ALGORITHM number.")

        # Current date-time
        currentDateTime = "{}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # Current date-time in a Windows friendly format
        windowsDateTime = currentDateTime.replace(" ", "_").replace(":", "h-", 1).replace(":", "m", 1)[:-2]

        # Output directories
        summaryOut = OUTPUT_DIRECTORY + '{}/summary/summary_{}.xml'
        vehiclefullOut = OUTPUT_DIRECTORY + '{}/vehicle_full_output/vehicle_full_{}.xml'
        vtkOut = OUTPUT_DIRECTORY + '{}/vtk_output/vtk_{}'
        floatingCarData = OUTPUT_DIRECTORY + '{}/floating_car_data/fcd_{}.xml'
        tripInfo = OUTPUT_DIRECTORY + '{}/trips_info/trip_info_{}.xml'

        # Choosing the scenario
        sumoConfig.insert(1, "-c")
        sumoConfig.insert(2, '--net-file')
        # Small manhattan test
        if SCENARIO == 0:
            sumoConfig.insert(2, TEST_SM_CONFIG)
            sumoConfig.insert(4, NET_FILE_SM)

            # Outputs
            if OUTPUTS:
                if SUMMARY_OUTPUT:
                    sumoConfig.append("--summary")
                    sumoConfig.append(summaryOut.format('small_manhattan/test', windowsDateTime))
                if VEHICLE_FULL_OUTPUT:
                    sumoConfig.append("--full-output")
                    sumoConfig.append(vehiclefullOut.format('small_manhattan/test', windowsDateTime))
                if VTK_OUTPUT:
                    sumoConfig.append("--vtk-output")
                    sumoConfig.append(vtkOut.format('small_manhattan/test', windowsDateTime))
                if FLOATING_CAR_DATA_OUTPUT:
                    sumoConfig.append("--fcd-output")
                    sumoConfig.append(floatingCarData.format('small_manhattan/test', windowsDateTime))
                if TRIPS_OUTPUT:
                    sumoConfig.append("--tripinfo-output")
                    sumoConfig.append(tripInfo.format('small_manhattan/test', windowsDateTime))

        # Small manhattan
        elif SCENARIO == 1:
            sumoConfig.insert(2, SM_CONFIG)
            sumoConfig.insert(4, NET_FILE_SM)

            # Outputs
            if OUTPUTS:
                if SUMMARY_OUTPUT:
                    sumoConfig.append("--summary")
                    sumoConfig.append(summaryOut.format('small_manhattan/normal', windowsDateTime))
                if VEHICLE_FULL_OUTPUT:
                    sumoConfig.append("--full-output")
                    sumoConfig.append(vehiclefullOut.format('small_manhattan/normal', windowsDateTime))
                if VTK_OUTPUT:
                    sumoConfig.append("--vtk-output")
                    sumoConfig.append(vtkOut.format('small_manhattan/normal', windowsDateTime))
                if FLOATING_CAR_DATA_OUTPUT:
                    sumoConfig.append("--fcd-output")
                    sumoConfig.append(floatingCarData.format('small_manhattan/normal', windowsDateTime))
                if TRIPS_OUTPUT:
                    sumoConfig.append("--tripinfo-output")
                    sumoConfig.append(tripInfo.format('small_manhattan/normal', windowsDateTime))

        # Newark
        elif SCENARIO == 2:
            sumoConfig.insert(2, NEWARK_CONFIG)
            sumoConfig.insert(4, NET_FILE_NEWARK)

            # Outputs
            if OUTPUTS:
                if SUMMARY_OUTPUT:
                    sumoConfig.append("--summary")
                    sumoConfig.append(summaryOut.format('newark/normal', windowsDateTime))
                if VEHICLE_FULL_OUTPUT:
                    sumoConfig.append("--full-output")
                    sumoConfig.append(vehiclefullOut.format('newark/normal', windowsDateTime))
                if VTK_OUTPUT:
                    sumoConfig.append("--vtk-output")
                    sumoConfig.append(vtkOut.format('newark/normal', windowsDateTime))
                if FLOATING_CAR_DATA_OUTPUT:
                    sumoConfig.append("--fcd-output")
                    sumoConfig.append(floatingCarData.format('newark/normal', windowsDateTime))
                if TRIPS_OUTPUT:
                    sumoConfig.append("--tripinfo-output")
                    sumoConfig.append(tripInfo.format('newark/normal', windowsDateTime))

        # Newark test
        elif SCENARIO == 3:
            sumoConfig.insert(2, TEST_NEWARK_CONFIG)
            sumoConfig.insert(4, NET_FILE_NEWARK)

            # Outputs
            if OUTPUTS:
                if SUMMARY_OUTPUT:
                    sumoConfig.append("--summary")
                    sumoConfig.append(summaryOut.format('newark/test', windowsDateTime))
                if VEHICLE_FULL_OUTPUT:
                    sumoConfig.append("--full-output")
                    sumoConfig.append(vehiclefullOut.format('newark/test', windowsDateTime))
                if VTK_OUTPUT:
                    sumoConfig.append("--vtk-output")
                    sumoConfig.append(vtkOut.format('newark/test', windowsDateTime))
                if FLOATING_CAR_DATA_OUTPUT:
                    sumoConfig.append("--fcd-output")
                    sumoConfig.append(floatingCarData.format('newark/test', windowsDateTime))
                if TRIPS_OUTPUT:
                    sumoConfig.append("--tripinfo-output")
                    sumoConfig.append(tripInfo.format('newark/test', windowsDateTime))

        return sumoConfig

    def run(self, testCase, instantStart, quitOnEnd):
        """
        Starts the simulation and Traci

        Args:
            testCase (bool): True if test cases are being ran, closing traci only when prompted
            instantStart (bool): True if the simulation is required to be instantly started
            quitOnEnd (bool): True if the GUI should quit at the end of the simulation
        """
        # Defines the command to start SUMO with
        #   --net-file: The SUMO network file to be used (.net.xml)
        #   --step-length: Defines the length of each timestep in seconds
        #   --additional-files: Allows for additional files to be input into the configuration

        #   --routing-algorithm: Defines the routing algorithm used by the vehicles
        #   --gui-settings-file: Allows for the GUI to be manipulated
        #   --device.rerouting.probability: Defines the probability that a vehicle in the simulation will automatically
        # reroute
        #   --device.rerouting.threads: The number of threads used for rerouting purposes
        sumoConfigInitial = [SUMO_BINARY, '--step-length', STEP_LENGTH, '--additional-files',
                             VEHICLES_FILE, '--routing-algorithm', 'dijkstra', '--gui-settings-file', GUI_SETTINGS,
                             '--device.rerouting.probability', '1.0', '--device.rerouting.threads', '3']

        if instantStart:
            sumoConfigInitial.append('--start')

        if quitOnEnd:
            sumoConfigInitial.extend(['--quit-on-end', 'True'])

        sumoConfig = self.configureSumo(sumoConfigInitial)

        traci.start(sumoConfig)

        test = src.project.code.Testing.Testing()
        dsp = routing.DynamicShortestPath()
        drwf = routing.DynamicReroutingWithFairness()
        ksp = routing.kShortestPaths()

        func.initialisation()

        if SCENARIO == 0 or SCENARIO == 3:
            test.beforeLoop()

            for i in range(START_TIME, END_TIME):
                test.duringLoop(i)
        else:
            # No rerouting
            if ALGORITHM == 0:
                for i in range(START_TIME, END_TIME):
                    traci.simulationStep()
            # Dynamic shortest path
            elif ALGORITHM == 1:
                for i in range(START_TIME, END_TIME):
                    dsp.main(i)
            # k-shortest paths
            elif ALGORITHM == 2:
                for i in range(START_TIME, END_TIME):
                    ksp.main(i)
            # Dynamic Rerouting with Fairness
            elif ALGORITHM == 3:
                for i in range(START_TIME, END_TIME):
                    drwf.main(i)

        # If not running test cases close when the END_TIME is reached
        if not testCase:
            # Close the Sumo-Traci connection once the simulation has elapsed
            traci.close(False)


if __name__ == '__main__':
    """
    The main method for all running
    """
    print("This is the current working directory: {})".format(os.getcwd()))
    main = Main()
    main.run(False, False, False)


