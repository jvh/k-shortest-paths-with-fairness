import traci
import time

from src.project.code import SumoConnection as sumo
from src.project.code import HelperFunctions as func

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
                    congestion = func.returnCongestionLevelLane(laneID)
                    if congestion > 0.5:
                        func.getLane2DCoordinates(laneID)
                        func.rerouteSelectedVehiclesEdge(edge)

        if i == 600:
            func.endSim(i)

        traci.simulationStep()


    def main(self, i):
        """
        The main programme run during the loop which progresses the simulation at every timestep

        Args:
            i (int): The current timestep of the simulation
        """
        # # Every 100 timesteps
        # if i % 100 == 0 and i >= 1:
        #     for laneID in traci.lane.getIDList():
        #         edge = traci.lane.getEdgeID(laneID)
        #
        #         #   Special edges, i.e. connector or internal edges, have ':' prepended to them, don't consider these
        #         # in rerouting.
        #         #   Additionally, only lanes which have length of at least 25m are considered in re-routing. This is due
        #         # to small errors when using NetConvert (some road segments are still left broken up into extremely
        #         # small sections, and other minor issues - for example, junctions may contain very small edges to
        #         # connect to one another (one car could cause congestion on this entire segment)
        #         #   Furthermore, checks that the edges are not fringe edges (edges which have either no incoming or
        #         # outgoing edges), this is because congestion cannot be managed on these (ultimately both departure
        #         # and arrival point must remain the same)
        #         if laneID[:1] != ":" and traci.lane.getLength(laneID) > 25 and not \
        #                 sumo.net.getEdge(edge).is_fringe():
        #             congestion = func.returnCongestionLevelLane(laneID)
        #             if congestion > 0.5:
        #                 print(func.getLane2DCoordinates(laneID))
        #                 func.rerouteSelectedVehiclesEdge(edge)

        # if i % 100 == 0 and i >= 1:
        #     print("This is the number {}".format(i/100))
        #     for edge in func.edgesNetwork.keys():
        #         if func.edgeLengths[edge] >= 25 and edge not in func.fringeEdges:
        #             congestion = func.returnCongestionLevelEdge(edge)
        #             if congestion > 0.5:
        #                 func.getEdge2DCoordinates(edge)
        #                 func.rerouteSelectedVehiclesEdge(edge)

        if i % 100 == 0 and i >= 1:
            timeTakenStart = time.clock()

            # Processing the lanes existing on edges with multiple outgoing edges
            for lane in func.reroutingLanes:
                congestion = func.returnCongestionLevelLane(lane)
                if congestion >= CONGESTION_THRESHOLD:
                    print("\n***** LANE {} REROUTE ********\n".format(lane))
                    edge = func.lanesNetwork[lane]
                    func.getEdge2DCoordinates(edge)
                    func.rerouteSelectedVehiclesLane(edge, lane)

            timeTakenEnd = time.clock()

            totalTime = timeTakenEnd - timeTakenStart

            # Processing those edges which only have a single outgoing edge (all lanes lead to the same position
            for edge in func.singleOutgoingEdges:
                congestion = func.returnCongestionLevelEdge(edge)
                if congestion >= CONGESTION_THRESHOLD:
                    print("\n***** EDGE {} REROUTE ********\n".format(edge))
                    func.getEdge2DCoordinates(edge)
                    func.rerouteSelectedVehiclesEdge(edge)


                    # # This list stores lanes which still need to be searched for congestion
            # searchLanes = func.lanesNetwork.keys()
            # print("This is the number {}".format(i/100))
            # for lane in searchLanes:
            #     edge = func.lanesNetwork[lane]
            #
            #
            #     if len(func.directedGraphEdges[edge]) == 1:
            #         print(edge)
            #
            #     if func.laneLengths[lane] >= 25 and edge not in func.fringeEdges:
            #         congestion = func.returnCongestionLevelLane(lane)
            #         if congestion > 0.5:
            #             func.getLane2DCoordinates(lane)
            #             func.rerouteSelectedVehiclesLane(edge, lane)

        traci.simulationStep()

class kShortestPaths:
    """
    Reroutes vehicles down a randomly selected path (up to k selections) upon detection congestion
    """

    # 1. Get a set of all of the edges which actually contain vehicles as returned by the recursiveEdges
    # 2. For each edge collect up to k total different paths (find all the ways out)
    # 3. For each vehicle randomly assign one of these

    def main(self, i):
        """
        The main programme run during the loop which progresses the simulation at every timestep

        Args:
            i (int): The current timestep of the simulation
        """

        # Every 100 timesteps
        if i % 100 == 0 and i >= 1:
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
                    congestion = func.returnCongestionLevelLane(laneID)
                    if congestion > 0.5:
                        print(func.getLane2DCoordinates(laneID))
                        func.rerouteSelectedVehiclesEdge(edge)
                        # time.sleep(2)

        traci.simulationStep()


class DynamicReroutingWithFairness:
    """
    Reroutes vehicles upon detecting congestion with fairness as a requirement WITHOUT FUTURE PROOF
    """

    def main(self, i):
        """
        The main programme run during the loop which progresses the simulation at every timestep

        Args:
            i (int): The current timestep of the simulation
        """

        traci.simulationStep()



