###################################################################################################################
# Concerned with the configuration of SUMO and the connection with TraCI. This initialises SUMO with the settings #
# input and reverts control back to TraCI to allow modification during runtime of the simulation and collection   #
# of simulation states.                                                                                           #
#                                                                                                                 #
# Author: Jonathan Harper                                                                                         #
###################################################################################################################

__author__ = "Jonathan Harper"

###############
# WORKSTATION #
###############

# True if using main computer (allows for easy switching between laptop and main home computer)
COMPUTER = True
MAIN_COMP = True

#############
# IMPORTING #
#############

import sys
import os

if not COMPUTER:
    # Inserts SUMO tools into the PATH (or PYTHONPATH)
    sys.path.insert(1, '/Users/jonathan/Documents/comp3200/sumo/tools')
    # This sets the environment variable 'SUMO_HOME'
    os.environ["SUMO_HOME"] = "/Users/jonathan/Documents/comp3200/sumo"

import traci
import sumolib
import datetime

import src.code.Testing
from src.code import RoutingAlgorithms as routing
from src.code import InitialMapHelperFunctions as initialFunc
from src.code import Database as db

########################
# USER-DEFINED OPTIONS #
########################

SUMO_GUI = False
# This enables major print statements for diagnostic purposes
PRINT = False
# Prints out the lanes/edges which have been rerouted for that period
PRINT_ROAD_REROUTED = True
# True if the camera should snap to the congested zone
SNAP_TO_CONGESTION = True

# This is the unique reference for the simulation in progress
SIMULATION_REFERENCE = ""

# Specifies the scenario (map)
#   0: Testing (small_manhattan)
#   1: small_manhattan
#   2: newark
#   3: Testing (newark)
#   4: Southampton
SCENARIO = 4
# Specifies the rerouting algorithm to be ran
#   0: No rerouting
#   1: Dynamic shortest path (DSP)
#   2: k-Shortest Path
#   3: Dynamic Rerouting with Fairness
#   4: k-Shortest Path with fairness
ALGORITHM = 4
# Whether or not to calculate the A* distances for this map
A_STAR_DISTANCES = True

#################
# SUMO SETTINGS #
#################

START_TIME = 0
END_TIME = 3000
ZOOM_FACTOR = 12
# Each step is 1 second
STEP_LENGTH = '1.0'

###########
# OUTPUTS #
###########

# Specifies output file (.xml), True = output generated
# An easy way to turn off all outputs, False = No outputs generated
OUTPUTS = True
#   --summary: Prints out a summary of the information
SUMMARY_OUTPUT = True
#   --full-output: Builds a file containing the full dump of various information regarding the positioning of vehicles
VEHICLE_FULL_OUTPUT = False
#   --vtk-output: Builds a VTK output which can be interpreted by tools such as Paraview
VTK_OUTPUT = False
#   --fcd-output: Floating car data, outputs information about the vehicle, similar to a GPS output
FLOATING_CAR_DATA_OUTPUT = False
#   --tripinfo-output: Generates information about the vehicle trips
TRIPS_OUTPUT = True

########
# TODO #
########

"""
Remove the edges which are the insertions of the map to only facilitate at most one edge (so that vehicles don't pack 
up on that single edge

The simulation itself always runs on a single core. However, routing in SUMO or DUAROUTER can be parallelized by setting
the option --device.rerouting.threads <INT> and --routing-threads <INT> respectively.

The python TraCI library allows controlling multiple simulations from a single script either by calling traci.connect 
and storing the returned connection object or by calling traci.start(label=...) and retrieving the connection object 
with traci.getConnection(label).

Change from dijkstras to a*

Think about subscriptions

Add in 'tau' into the vehicles.xml (driver's reaction time)

Edges might not be the best solution when choosing where congestion occurs because an edge can contain a number of 
lanes which go to certain intersections, for example a left edge may invite a left turn, whereas a right edge may 
Invite a right turn. This means that a single lane on an edge may be congested whereas the other lane may not be.

See img1.png for a good representation of this exact thing

Write about using sets over lists for some things (NOT OWN WORDS BELOW)
    1) since the in operator is O(n) on a list but O(1) on a set
    2) Sets are significantly faster when it comes to determining if an object is present in the set (as in x in s), 
    but are slower than lists when it comes to iterating over their contents.

departSpeed = 'random' in the routes file for each of the vehicle definitions
    e.g. <vehicle type="car" departSpeed="random" id="1" depart="0.00">

The fairness should be measured against a more generic fairness measure which is to simply reroute only X% vehicles 
coming up to a congested area

Maybe do this thing where you start with a base value of maybe 1 for edge recursions, however, if you go down the
incoming lanes/edges and you also find congestion then you should go down +1 further edges given that the congestion
may take a while to disperse

Keep a list of vehicles which if they are in the set of vehicles which have already undergone some kind of rerouting,
they should not be considered further as this may mean they are consistently rerouted in a single turn

Include the ability for not full adherence to the fairness thing
"""

####################
# PROJECT SETTINGS #
####################

# These are the times between the simulation start and end, delay MUST be set at 0ms for this to be comparable to other
# results
timerStart = 0
timerEnd = 0

# Settings main working directory
if COMPUTER:
    if MAIN_COMP:
        # Main computer project configuration location
        MAIN_PROJECT = "D:/Users/Jonathan/Desktop/Work/sumo/ReroutingWithFairness/src/configuration_files/"
        if SUMO_GUI:
            SUMO_BINARY = "D:/Program Files/SUMO/bin/sumo-gui.exe"
        else:
            SUMO_BINARY = "D:/Program Files/SUMO/bin/sumo.exe"
        OUTPUT_DIRECTORY = "D:/Users/Jonathan/Desktop/Work/sumo/sumo_output/"
        DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database.sqlite"
else:
    MAIN_PROJECT = "/Users/jonathan/Documents/comp3200/ReroutingWithFairness/src/configuration_files/"
    if SUMO_GUI:
        SUMO_BINARY = "/Users/jonathan/Documents/comp3200/sumo/bin/sumo-gui"
    else:
        SUMO_BINARY = "/Users/jonathan/Documents/comp3200/sumo/bin/sumo"
    OUTPUT_DIRECTORY = "/Users/jonathan/Documents/comp3200/sumo_output/"
    DATABASE_LOCATION = "/Users/jonathan/Documents/comp3200/database/output_database.sqlite"

# SUMO Configuration files
SM_CONFIG = MAIN_PROJECT + "small_manhattan/normal/small_manhattan_config.cfg"
TEST_SM_CONFIG = MAIN_PROJECT + "small_manhattan/testing/small_manhattan_test.cfg"
NEWARK_CONFIG = MAIN_PROJECT + "newark/normal/newark_config.cfg"
TEST_NEWARK_CONFIG = MAIN_PROJECT + "newark/testing/newark_test_config.cfg"
SOUTHAMPTON_CONFIG = MAIN_PROJECT + "new_stuff/southampton/southampton.cfg"
NET_FILE_SM = MAIN_PROJECT + "small_manhattan/small_manhattan.net.xml"
NET_FILE_NEWARK = MAIN_PROJECT + "newark/newark_square.net.xml"
NET_FILE_SOUTHAMPTON = MAIN_PROJECT + "new_stuff/southampton/southampton.net.xml"
VEHICLES_FILE = MAIN_PROJECT + "vehicles.xml"
GUI_SETTINGS = MAIN_PROJECT + "gui.settings.xml"
SOUTHAMPTON_DIRECTORY = MAIN_PROJECT + 'new_stuff/southampton/'


try:
    # Small manhattan
    if SCENARIO == 0 or SCENARIO == 1:
        # Passes the network file into sumolib for analysis and use
        net = sumolib.net.readNet(NET_FILE_SM)
    # Newark
    elif SCENARIO == 2 or SCENARIO == 3:
        net = sumolib.net.readNet(NET_FILE_NEWARK)
    elif SCENARIO == 4:
        net = sumolib.net.readNet(NET_FILE_SOUTHAMPTON)
        SCENARIO_DIRECTORY = SOUTHAMPTON_DIRECTORY
    else:
        sys.exit("Please enter a valid SCENARIO number")
except TypeError:
    sys.exit("Ensure that you have the COMPUTER boolean set correctly, currently {}".format(COMPUTER))


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
        return int(traci.simulation.getCurrentTime() / 1000)

    @staticmethod
    def configureSumo(sumoConfig):
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
        if (SCENARIO == 1 or SCENARIO == 2 or SCENARIO == 4) and not (0 <= ALGORITHM <= 4):
            sys.exit("Please enter a valid ALGORITHM number.")

        # Current date-time
        currentDateTime = "{}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # Current date-time in a Windows friendly format
        windowsDateTime = currentDateTime.replace(" ", "_").replace(":", "h-", 1).replace(":", "m", 1)[:-2]

        # Output directories
        summaryOut = OUTPUT_DIRECTORY + '{}/summary/summary_{}.xml'
        vehicleFullOut = OUTPUT_DIRECTORY + '{}/vehicle_full_output/vehicle_full_{}.xml'
        vtkOut = OUTPUT_DIRECTORY + '{}/vtk_output/vtk_{}'
        floatingCarData = OUTPUT_DIRECTORY + '{}/floating_car_data/fcd_{}.xml'
        tripInfo = OUTPUT_DIRECTORY + '{}/trips_info/trip_info_{}.xml'

        # Choosing the scenario
        if SCENARIO == 4:
            sumoConfig.insert(1, '--net-file')
        else:
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
                    sumoConfig.append(vehicleFullOut.format('small_manhattan/test', windowsDateTime))
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
                    sumoConfig.append(vehicleFullOut.format('small_manhattan/normal', windowsDateTime))
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
                    sumoConfig.append(vehicleFullOut.format('newark/normal', windowsDateTime))
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
                    sumoConfig.append(vehicleFullOut.format('newark/test', windowsDateTime))
                if VTK_OUTPUT:
                    sumoConfig.append("--vtk-output")
                    sumoConfig.append(vtkOut.format('newark/test', windowsDateTime))
                if FLOATING_CAR_DATA_OUTPUT:
                    sumoConfig.append("--fcd-output")
                    sumoConfig.append(floatingCarData.format('newark/test', windowsDateTime))
                if TRIPS_OUTPUT:
                    sumoConfig.append("--tripinfo-output")
                    sumoConfig.append(tripInfo.format('newark/test', windowsDateTime))

        # Southampton
        elif SCENARIO == 4:
            sumoConfig.insert(2, NET_FILE_SOUTHAMPTON)

            # Outputs
            if OUTPUTS:
                if SUMMARY_OUTPUT:
                    sumoConfig.append("--summary")
                    sumoConfig.append(summaryOut.format('southampton', windowsDateTime))
                if VEHICLE_FULL_OUTPUT:
                    sumoConfig.append("--full-output")
                    sumoConfig.append(vehicleFullOut.format('southampton', windowsDateTime))
                if VTK_OUTPUT:
                    sumoConfig.append("--vtk-output")
                    sumoConfig.append(vtkOut.format('southampton', windowsDateTime))
                if FLOATING_CAR_DATA_OUTPUT:
                    sumoConfig.append("--fcd-output")
                    sumoConfig.append(floatingCarData.format('southampton', windowsDateTime))
                if TRIPS_OUTPUT:
                    sumoConfig.append("--tripinfo-output")
                    sumoConfig.append(tripInfo.format('southampton', windowsDateTime))

        return sumoConfig

    def run(self, testCase=False, instantStart=False, quitOnEnd=False, routeFile="", functionName=""):
        """
        Starts the simulation and Traci

        Args:
            testCase (bool): True if test cases are being ran, closing traci only when prompted
            instantStart (bool): True if the simulation is required to be instantly started
            quitOnEnd (bool): True if the GUI should quit at the end of the simulation
            routeFile (str): The route file to use for execution
            functionName (str): This is the name of the function which called the main method
        """

        """
        Defines the configuration to start SUMO with
           --net-file: The SUMO network file to be used (.net.xml)
           --step-length: Defines the length of each timestep in seconds
           --additional-files: Allows for additional files to be input into the configuration

           --routing-algorithm: Defines the routing algorithm used by the vehicles
           --gui-settings-file: Allows for the GUI to be manipulated
           --device.rerouting.probability: Defines the probability that a vehicle in the simulation will automatically
             reroute
           --device.rerouting.threads: The number of threads used for rerouting purposes
           --depart
        """
        sumoConfigInitial = [SUMO_BINARY, '--step-length', STEP_LENGTH, '--additional-files',
                             VEHICLES_FILE, '--routing-algorithm', 'astar', '--gui-settings-file', GUI_SETTINGS,
                             '--device.rerouting.probability', '1.0', '--device.rerouting.threads', '3']

        # Additional SUMO config options
        if instantStart:
            sumoConfigInitial.append('--start')

        if quitOnEnd:
            sumoConfigInitial.extend(['--quit-on-end', 'True'])

        if routeFile != "":
            sumoConfigInitial.extend(['-r', routeFile])

        sumoConfig = self.configureSumo(sumoConfigInitial)

        traci.start(sumoConfig)

        test = src.code.Testing.Testing()
        reroutingAlgorithm = routing.ReroutingAlgorithms()
        # Initialise data regarding the map into memory for quick real-time access
        initialFunc.initialisation()

        algorithm = ''
        if ALGORITHM == 0:
            algorithm = 'No Rerouting'
        elif ALGORITHM == 1:
            algorithm = 'Dynamic Shortest Path'
        elif ALGORITHM == 2:
            algorithm = 'k-Shortest Paths'
        elif ALGORITHM == 3:
            algorithm = 'Dynamic Shortest Path with Fairness'
        elif ALGORITHM == 4:
            algorithm = 'k-Shortest Paths with Fairness'

        print("Running with algorithm {}.".format(algorithm))

        if SCENARIO == 0 or SCENARIO == 3:
            test.beforeLoop(functionName)

            for i in range(START_TIME, END_TIME):
                test.duringLoop(i+1)
        else:
            # No rerouting
            if ALGORITHM == 0:
                for i in range(START_TIME, END_TIME):
                    traci.simulationStep()
            else:
                # Initialising the database
                database = db.Database()
                for i in range(START_TIME, END_TIME):
                    reroutingAlgorithm.main(i+1, database)

        # If not running test cases close when the END_TIME is reached
        if not testCase:
            # Close the Sumo-Traci connection once the simulation has elapsed
            traci.close(False)


if __name__ == '__main__':
    """
    The main method for all running
    """
    # main = Main()
    # main.run(instantStart=True)

    import src.code.SumoConnection as sumo
    import time
    import src.code.RoutingFunctions as func

    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database1.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.2
    func.K_MAX = 4

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=4,K_MAX=1.2_{}_".format(i+1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i+1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database2.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.4

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=4,K_MAX=1.4_{}_".format(i+1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i+1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database3.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.6

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=4,K_MAX=1.6_{}_".format(i+1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i+1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database4.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.8

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=4,K_MAX=1.8_{}_".format(i+1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i+1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database5.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 2.0

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=4,K_MAX=2.0_{}_".format(i+1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i+1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(120)

    #############
    # K_MAX = 5 #
    #############

    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database6.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.2
    func.K_MAX = 5

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=5,K_MAX=1.2_{}_".format(i + 1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i + 1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database7.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.4

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=5,K_MAX=1.4_{}_".format(i + 1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i + 1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database8.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.6

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=5,K_MAX=1.6_{}_".format(i + 1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i + 1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database9.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 1.8

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=5,K_MAX=1.8_{}_".format(i + 1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i + 1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

    time.sleep(60)
    sumo.DATABASE_LOCATION = "D:/Users/Jonathan/Desktop/Work/sumo/database/output_database10.sqlite"
    func.KPATH_MAX_ALLOWED_TIME = 2.0

    for i in range(10):
        sumo.SIMULATION_REFERENCE = "k=5,K_MAX=2.0_{}_".format(i + 1)
        print("\n\n{} with KPATH_MAX_ALLOWED={} and K_MAX={}\n\n".format(sumo.SIMULATION_REFERENCE,
                                                                         func.KPATH_MAX_ALLOWED_TIME, func.K_MAX))
        main = Main()
        main.run(routeFile='{}routes_southampton_20mins_{}.xml'.format(SCENARIO_DIRECTORY, i + 1),
                 instantStart=True, quitOnEnd=True)
        time.sleep(10)

