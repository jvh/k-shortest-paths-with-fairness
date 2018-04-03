import traci
import sumolib
import os
import datetime
from src.project.code import RoutingAlgorithms as routing

# True if using main computer (allows for easy switching between laptop and main home computer)
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
END_TIME = 2000
ZOOM_FACTOR = 12
# Each step is 1 seconds
STEP_LENGTH = '1.0'

# This specifies the number of incoming edges away (the range) from the original edge to search
MAX_EDGE_RECURSIONS_RANGE = 3

# Specifies the scenario (map)
#   0: Testing (small_manhattan)
#   1: small_manhattan
#   2: newark
SCENARIO = 1
# Specifies the rerouting algorithm to be ran
#   0: No rerouting
#   1: Dynamic shortest path (DSP)
ALGORITHM = 0

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
else:
    net = sumolib.net.readNet(NET_FILE_NEWARK)

class Main:
    """
    The class in which most of the SUMO configuration occurs, along with Traci configuration to communicate with SUMO
    at runtime
    """

    @staticmethod
    def getCurrentTime():
        """
        Returns the current simulation time
        Return:
            int: The current timestep of the simulation
        """
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
        else:
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

        return sumoConfig

    def run(self):
        """
        Starts the simulation and Traci
        """
        # Defines the command to start SUMO with
        #   --net-file: The SUMO network file to be used (.net.xml)
        #   --step-length: Defines the length of each timestep in seconds
        #   --additional-files: Allows for additional files to be input into the configuration

        #   --routing-algorithm: Defines the routing algorithm used by the vehicles
        #   --gui-settings-file: Allows for the GUI to be manipulated
        #   --device.rerouting.probability: Defines the probability that a vehicle in the simulation will automatically
        # reroute
        sumoConfigInitial = [SUMO_BINARY, '--step-length', STEP_LENGTH, '--additional-files',
                             VEHICLES_FILE, '--routing-algorithm', 'dijkstra', '--gui-settings-file', GUI_SETTINGS,
                             '--device.rerouting.probability', '1.0']

        sumoConfig = self.configureSumo(sumoConfigInitial)

        print("SUMOCONFIG {}".format("['D:/Program Files/SUMO/bin/sumo-gui.exe', '-c', 'D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/pycharm_project/src/project/configuration_files/newark/normal/newark_config.cfg', '--net-file', 'D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/pycharm_project/src/project/configuration_files/newark/normal/newark.net.xml', '--step-length', '1.0', '--additional-files', 'D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/pycharm_project/src/project/configuration_files/vehicles.xml', '--routing-algorithm', 'dijkstra', '--gui-settings-file', 'D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/pycharm_project/src/project/configuration_files/gui.settings.xml', '--device.rerouting.probability', '1.0']"))


        print("SUMOCONFIE {}".format(sumoConfig))

        traci.start(sumoConfig)

        test = routing.Testing()
        dsp = routing.DynamicShortestPath()

        if SCENARIO == 0:
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

        # Close the Sumo-Traci connection once the simulation has elapsed
        traci.close(False)


if __name__ == '__main__':
    """
    The main method for all running
    """
    print("This is the current working directory: {})".format(os.getcwd()))
    main = Main()
    main.run()


