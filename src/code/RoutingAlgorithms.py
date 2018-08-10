###################################################################################################################
# These are the various routing algorithms used within the rerouting of vehicles.                                 #
#                                                                                                                 #
# Author: Jonathan Harper                                                                                         #
###################################################################################################################

__author__ = "Jonathan Harper"

###########
# IMPORTS #
###########

from src.code import SumoConnection as sumo
import sys
import os
import datetime

if not sumo.COMPUTER:
    sys.path.insert(1, '/Users/jonathan/Documents/comp3200/sumo/tools')
    os.environ["SUMO_HOME"] = "/Users/jonathan/Documents/comp3200/sumo"

import traci

from src.code import RoutingFunctions as func
from src.code import InitialMapHelperFunctions as initialFunc
from src.code import SimulationFunctions as sim


class ReroutingAlgorithms:
    """
    These are the algorithms for rerouting; selecting a different ALGORITHM in SumoConnection will determine which
    algorithm shall be executed.

    DSP: Dynamic Shortest Path. Vehicles which face congestion simply go through the shortest path available to them.
    k-Paths: k-Shortest Pats. Vehicles who face congestion choose up to k of the shortest paths available to them.
    Fairness: Vehicles are rerouted based on how fairly they have been treated during the simulation and each subsequent
    simulation.
    """

    def selectReroutingAlgorithm(self, road):
        """
        Selects rerouting algorithm to be performed based on the ALGORITHM selected in SumoConnection.

        :param road: The road segment which is being considered.
        """
        # DSP
        if sumo.ALGORITHM == 1:
            func.rerouteSelectedVehicles(road, kPathsBool=False, fairness=False)
        # k-Paths
        elif sumo.ALGORITHM == 2:
            func.rerouteSelectedVehicles(road, kPathsBool=True, fairness=False)
        # DSP with Fairness
        elif sumo.ALGORITHM == 3:
            func.rerouteSelectedVehicles(road, kPathsBool=False, fairness=True)
        # k-Paths with Fairness
        elif sumo.ALGORITHM == 4:
            func.rerouteSelectedVehicles(road, kPathsBool=True, fairness=True)

    def determineReroutingBasedOnCongestion(self, road, roadBool, congestionBool, congestionLevel):
        """
        This takes the current road and, based on the congestion levels of the road, checks whether or not the vehicles
        on that road should be eligible for rerouting.

        :param road: The road segment which is being considered.
        :param roadBool: True if lane, False if edge.
        :param congestionBool: True if road congested
        :param congestionLevel: This holds the {edge: congestion} for the road network
        """
        congBool = congestionBool

        if roadBool:
            congestion = sim.returnCongestionLevelLane(road)
        else:
            congestion = sim.returnCongestionLevelEdge(road)

        sim.roadCongestion[road] = congestion

        if congestion >= func.CONGESTION_THRESHOLD:
            if not congBool:
                # Getting the edge weights of the entire scenario for the current time step
                sim.getGlobalEdgeWeights()
                congBool = True

            if sumo.PRINT_ROAD_REROUTED:
                if roadBool:
                    print("***** LANE {} REROUTE ********".format(road))
                else:
                    print("***** EDGE {} REROUTE ********".format(road))

            # Only snaps to congestion given that the GUI is enabled and the SNAP_TO_CONGESTION option is also enabled
            if sumo.SNAP_TO_CONGESTION and sumo.SUMO_GUI:
                if roadBool:
                    edge = initialFunc.lanesNetwork[road]
                    sim.getEdge2DCoordinates(edge)
                else:
                    sim.getEdge2DCoordinates(road)

            self.selectReroutingAlgorithm(road)

        return congBool

    def main(self, i, database):
        """
        The main programme run during the loop which progresses the simulation at every timestep

        Args:
            i (int): The current timestep of the simulation
            database (Database): This is the database in which the information is stored
        """
        traci.simulationStep()
        # Checks for vehicle departure and arrival into the simulation
        sim.vehiclesDepartedAndArrived(i)

        # Every REROUTING_PERIOD
        if i % func.REROUTING_PERIOD == 0 and i >= 1:
            print("\n***** REROUTING PERIOD {} ********\n".format(i / func.REROUTING_PERIOD))

            # This is the updating of the time spent in the system for each vehicle
            sim.updateVehicleTotalEstimatedTimeSpentInSystem(func.REROUTING_PERIOD)

            """ Selecting and rerouting vehicles at points of congestion """

            # Resets the congestion level for each road segment
            sim.roadCongestion = {}
            # Resets the set of vehicles which have undergone rerouting for the previous rerouting period
            func.reroutedVehicles = set()
            # True when any congestion is detected
            congestionBool = False

            startTime = datetime.datetime.now()

            # Processing the lanes existing on edges with multiple outgoing edges
            for lane in initialFunc.reroutingLanes:
                congestionBool = self.determineReroutingBasedOnCongestion(lane, True, congestionBool,
                                                                          sim.roadCongestion)

            if congestionBool: print()

            # Processing those edges which only have a single outgoing edge (all lanes lead to the same position)
            for edge in initialFunc.singleOutgoingEdges:
                congestionBool = self.determineReroutingBasedOnCongestion(edge, False, congestionBool,
                                                                          sim.roadCongestion)

            # Only work out time taken if rerouting has taken place
            if congestionBool:
                endTime = datetime.datetime.now()
                sim.getTimeTaken(startTime, endTime)

            # Working out fairness index + standard deviation of QOE values
            fairnessIndex, standardDeviation = sim.fairnessIndex()

            # Update the database with the up-to-date values
            database.populateDBSimulationTable(i, fairnessIndex, standardDeviation, sumo.SIMULATION_REFERENCE,
                                               sim.calculateAverageRoadCongestion())
            database.populateDBVehicleTable()

            # Reset
            sim.vehiclesInNetwork = []

        # After 3 hours have elapsed
        if i == sumo.END_TIME:
            initialFunc.endSim(i)
