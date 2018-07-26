###################################################################################################################
# These are the various routing algorithms used within the rerouting of vehicles.                                 #
#                                                                                                                 #
# Author: Jonathan Harper                                                                                         #
###################################################################################################################

import traci

from src.code import SumoConnection as sumo
from src.code import RoutingFunctions as func
from src.code import InitialMapHelperFunctions as initialFunc
from src.code import SimulationFunctions as sim

__author__ = "Jonathan Harper"

# This is the period in seconds in which rerouting happens
ROUTE_PERIOD = 200
# The threshold in which congestion is considered to have occurred
CONGESTION_THRESHOLD = 0.5


class DynamicShortestPath:
    """
    Implementation of the algorithm for Dynamic Shortest Path (DSP).

    When congestion is detected in a period, vehicles are rerouted based on current estimated travel times in an attempt
    to reduce the global average travel time.
    """

    # noinspection PyMethodMayBeStatic
    def mainB(self, i):
        """
        The main programme run during the loop which progresses the simulation at every timestep

        Args:
            i (int): The current timestep of the simulation
        """

        # Every 100 timesteps
        if i % 100 == 0 and i >= 1:
            print("Number of times rerouting algorithm has ran {}".format(i/100))
            for laneID in traci.lane.getIDList():
                edge = traci.lane.getEdgeID(laneID)

                #   Special edges, i.e. connector or internal edges, have ':' prepended to them, don't consider these
                # in rerouting.
                #   Additionally, only lanes which have length of at least 25m are considered in re-routing. This is due
                # to small errors when using NetConvert (some road segments are still left broken up into extremely
                # small sections, and other minor issues - for example, junctions may contain very small edges to
                # connect to one another (one car could cause congestion on this entire segment)
                #   Furthermore, checks that the edges are not fringe edges (edges which have either no incoming or
                # outgoing edges), this is because congestion cannot be managed on these (ultimately both departure
                # and arrival point must remain the same)
                if laneID[:1] != ":" and traci.lane.getLength(laneID) > 25 and not \
                        sumo.net.getEdge(edge).is_fringe():
                    congestion = sim.returnCongestionLevelLane(laneID)
                    if congestion > 0.5:
                        func.rerouteSelectedVehiclesEdge(edge)

        if i == 600:
            initialFunc.endSim(i)

        traci.simulationStep()

    # noinspection PyMethodMayBeStatic
    def main(self, i):
        """
        The main programme run during the loop which progresses the simulation at every timestep

        Args:
            i (int): The current timestep of the simulation
        """

        if i % func.REROUTING_PERIOD == 0 and i >= 1:
            # Resets the set of vehicles which have undergone rerouting for the previous rerouting period
            func.reroutedVehicles = set()

            # Processing the lanes existing on edges with multiple outgoing edges
            for lane in initialFunc.reroutingLanes:
                congestion = sim.returnCongestionLevelLane(lane)
                if congestion >= CONGESTION_THRESHOLD:
                    print("\n***** LANE {} REROUTE ********\n".format(lane))
                    edge = initialFunc.lanesNetwork[lane]
                    sim.getEdge2DCoordinates(edge)
                    func.rerouteSelectedVehiclesLane(lane)

            # Processing those edges which only have a single outgoing edge (all lanes lead to the same position
            for edge in initialFunc.singleOutgoingEdges:
                congestion = sim.returnCongestionLevelEdge(edge)
                if congestion >= CONGESTION_THRESHOLD:
                    print("\n***** EDGE {} REROUTE ********\n".format(edge))
                    sim.getEdge2DCoordinates(edge)
                    func.rerouteSelectedVehiclesEdge(edge)

        traci.simulationStep()


class kShortestPaths:
    """
    Reroutes vehicles down a randomly selected path (up to k selections) upon detection congestion
    """

    # 1. Get a set of all of the edges which actually contain vehicles as returned by the recursiveEdges
    # 2. For each edge collect up to k total different paths (find all the ways out)
    # 3. For each vehicle randomly assign one of these

    # noinspection PyMethodMayBeStatic
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

        # After 30 minutes have elapsed
        if i == 1800:
            initialFunc.endSim(i)

        # Every REROUTING_PERIOD
        if i % func.REROUTING_PERIOD == 0 and i >= 1:
            print("***** REROUTING PERIOD {} ********".format(i / func.REROUTING_PERIOD))

            # This is the updating of the time spent in the system for each vehicle
            sim.updateVehicleTotalEstimatedTimeSpentInSystem(func.REROUTING_PERIOD)

            """ Selecting and rerouting vehicles at points of congestion """

            # Resets the set of vehicles which have undergone rerouting for the previous rerouting period
            func.reroutedVehicles = set()
            # True when any congestion is detected
            congestionBool = False

            # Processing the lanes existing on edges with multiple outgoing edges
            for lane in initialFunc.reroutingLanes:
                congestion = sim.returnCongestionLevelLane(lane)
                if congestion >= CONGESTION_THRESHOLD:
                    if not congestionBool:
                        # Getting the edge weights of the entire scenario for the current time step
                        sim.getGlobalEdgeWeights()
                        congestionBool = True
                    print("\n***** LANE {} REROUTE ********\n".format(lane))
                    edge = initialFunc.lanesNetwork[lane]
                    sim.getEdge2DCoordinates(edge)

                    func.rerouteSelectedVehicles(lane, kPathsBool=True, fairness=False)

            # Processing those edges which only have a single outgoing edge (all lanes lead to the same position
            for edge in initialFunc.singleOutgoingEdges:
                congestion = sim.returnCongestionLevelEdge(edge)
                if congestion >= CONGESTION_THRESHOLD:
                    # If current road conditions haven't yet been calculated
                    if not congestionBool:
                        sim.getGlobalEdgeWeights()
                        congestionBool = True
                    print("\n***** EDGE {} REROUTE ********\n".format(edge))
                    sim.getEdge2DCoordinates(edge)

                    func.rerouteSelectedVehicles(edge, kPathsBool=True, fairness=False)

            # Working out fairness index + standard deviation of QOE values
            fairnessIndex, standardDeviation = sim.fairnessIndex()

            # Update the database with the up-to-date values
            database.populateDBSimulationTable(i, fairnessIndex, standardDeviation, sumo.SIMULATION_REFERENCE)
            database.populateDBVehicleTable()

            # Reset
            sim.vehiclesInNetwork = []


class kShortestPathsFairness:
    """
    Reroutes vehicles down a randomly selected path (up to k selections) upon detection congestion
    """

    # 1. Get a set of all of the edges which actually contain vehicles as returned by the recursiveEdges
    # 2. For each edge collect up to k total different paths (find all the ways out)
    # 3. For each vehicle randomly assign one of these

    # noinspection PyMethodMayBeStatic
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

        # After 20 minutes have elapsed
        if i == 1800:
            initialFunc.endSim(i)

        # Every REROUTING_PERIOD
        if i % func.REROUTING_PERIOD == 0 and i >= 1:
            print("***** REROUTING PERIOD {} ********".format(i / func.REROUTING_PERIOD))

            # This is the updating of the time spent in the system for each vehicle
            sim.updateVehicleTotalEstimatedTimeSpentInSystem(func.REROUTING_PERIOD)

            """ Selecting and rerouting vehicles at points of congestion """

            # Resets the set of vehicles which have undergone rerouting for the previous rerouting period
            func.reroutedVehicles = set()
            # True when any congestion is detected
            congestionBool = False

            # Processing the lanes existing on edges with multiple outgoing edges
            for lane in initialFunc.reroutingLanes:
                congestion = sim.returnCongestionLevelLane(lane)
                if congestion >= CONGESTION_THRESHOLD:
                    if not congestionBool:
                        # Getting the edge weights of the entire scenario for the current time step
                        sim.getGlobalEdgeWeights()
                        congestionBool = True
                    print("\n***** LANE {} REROUTE ********\n".format(lane))
                    edge = initialFunc.lanesNetwork[lane]
                    sim.getEdge2DCoordinates(edge)

                    func.rerouteSelectedVehicles(lane, kPathsBool=True, fairness=True)

            # Processing those edges which only have a single outgoing edge (all lanes lead to the same position
            for edge in initialFunc.singleOutgoingEdges:
                congestion = sim.returnCongestionLevelEdge(edge)
                if congestion >= CONGESTION_THRESHOLD:
                    # If current road conditions haven't yet been calculated
                    if not congestionBool:
                        sim.getGlobalEdgeWeights()
                        congestionBool = True
                    print("\n***** EDGE {} REROUTE ********\n".format(edge))
                    sim.getEdge2DCoordinates(edge)

                    func.rerouteSelectedVehicles(edge, kPathsBool=True, fairness=True)

            # Working out fairness index + standard deviation of QOE values
            fairnessIndex, standardDeviation = sim.fairnessIndex()

            # Update the database with the up-to-date values
            database.populateDBSimulationTable(i, fairnessIndex, standardDeviation, sumo.SIMULATION_REFERENCE)
            database.populateDBVehicleTable()

            # Reset
            sim.vehiclesInNetwork = []


class DynamicReroutingWithFairness:
    """
    Reroutes vehicles upon detecting congestion with fairness as a requirement WITHOUT FUTURE PROOF
    """

    # noinspection PyMethodMayBeStatic
    def main(self):
        """
        The main programme run during the loop which progresses the simulation at every timestep
        """
        traci.simulationStep()
