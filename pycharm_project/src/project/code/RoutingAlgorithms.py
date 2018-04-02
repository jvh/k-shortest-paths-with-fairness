import traci
import time
import collections

from src.project.code import SumoConnection as sumo


def returnCongestionLevel(laneID):
    """
    Gives the congestion level of the road, laneID

    Args:
        laneID (str): The ID of the lane (road)
     Return:
         float: The occupancy (congestion) of the road, in percentage
    """
    return traci.lane.getLastStepOccupancy(laneID)

def getIncomingEdges(edgeID):
    """
    Returns a list of all of the incoming edges to the specified edge

    Args:
        edgeID (str): The identification of the edge to collect incoming edges
    Returns:
        incEdgeList (str[]): The edges incoming to edgeID
    """
    incEdgeList = []
    for edgeInc in sumo.net.getEdge(edgeID).getIncoming():
        incEdgeList.append(edgeInc.getID())
    return incEdgeList


def getIncomingLanes(laneID):
    """
    INCOMPLETE
    Returns a list of all of the incoming lanes to the specified lane

    Args:
        laneID (str): The identification of the edge to collect incoming edges
    Returns:
        incEdgeList (str[]): The edges incoming to edgeID
    """
    incEdgeList = []
    for edgeInc in sumo.net.getLane(laneID).getIncoming():
        incEdgeList.append(edgeInc.getID())
    return incEdgeList


def recursiveIncomingEdges(edgeID, firstTime=False, edgeList=[], edgesToSearch=["placeholder"],
                           edgeOrderList={}, finished=False):
    """
    Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
    away

    Args:
        edgeID (str): The edge in which to find the incoming edges
        firstTime (bool): If this is the first time running the module
        edgeList (str[]): The list holding all of the incoming edges from the original node up to
            MAX_EDGE_RECURSION_RANGE
        edgesToSearch (str[]): The list specifying the edges which are to be searched for incoming edges
        finished (bool): Specifies if the function has finished (all edges searched)
    Returns:
        str[]: The edges incoming to the initial edge up to MAX_EDGE_RECURSION_RANGE
    """
    if (edgesToSearch or edgeOrderList[edgeID] != sumo.MAX_EDGE_RECURSIONS_RANGE) and not finished:
        if firstTime:
            edgeOrderList = {}
            edgeList = []
            edgesToSearch = ["placeholder"]
            edgeOrderList[edgeID] = 0
            # Remove the placeholder value from the edgesToSearch stack
            edgesToSearch.remove("placeholder")

        # Gets the immediate incoming edges for edgeID
        edges = getIncomingEdges(edgeID)
        for edge in edges:
            edgeList.append(edge)
            # The new edge has range of edgeOrderList[edgeID] + 1 away from the original edge
            edgeOrderList[edge] = edgeOrderList[edgeID] + 1
            # If the range of the edge is below the maximum range then continue searching down that edge
            if edgeOrderList[edge] < sumo.MAX_EDGE_RECURSIONS_RANGE:
                edgesToSearch.append(edge)

        # There are still more edges to search
        if edgesToSearch:
            # Pop from the stack the edge to search
            edgeToTest = edgesToSearch.pop()
            finished = False
        # If there are no more edges to search
        else:
            finished = True
            # Prevent an error as there are no more edges to test
            edgeToTest = edgeID
        # Recursively call with the new edge
        return recursiveIncomingEdges(edgeToTest, finished=finished, edgeList=edgeList,
                                           edgesToSearch=edgesToSearch, edgeOrderList=edgeOrderList)
    else:
        return edgeList


def getMultiIncomingEdges(edgeID):
    """
    User friendly approach to getting the number of incoming edges from an edge (the recursiveIncomingEdge()
    function)

    Args:
        edgeID (str): The initial edge
    Returns:
        str[]: The edges incoming to the initial edge up to MAX_EDGE_RECURSION_RANGE
    """
    return recursiveIncomingEdges(edgeID, firstTime=True)


def getLane2DCoordinates(laneID):
    """
    Gets the 2D coordinates of the 'from' node which connects to the lane

    Args:
        laneID (str): The lane
    Returns:
        (str, str): Returns the tuple (x, y)
            Individual elements can be accessed by tuple.x and tuple.y
    """
    edge = traci.lane.getEdgeID(laneID)
    # Getting them 'from' node associated with that edge
    node = sumo.net.getEdge(edge).getFromNode().getID()
    # Getting the 2D coordinates (x, y) for that node
    x, y = sumo.net.getNode(node).getCoord()
    # Changes the GUI offset to the coordinates of the node
    traci.gui.setOffset("View #0", x, y)
    print("Lane {} has congestion level {}".format(laneID, returnCongestionLevel(laneID)))

    # Creating a named tuple to store (x, y) information
    coord = collections.namedtuple('coord', ['x', 'y'])
    c = coord(x=x, y=y)
    return c


class DynamicShortestPath:
    """
    Implementation of the algorithm for Dynamic Shortest Path (DSP).

    When congestion is detected in a period, vehicles are rerouted based on current estimated travel times in an attempt
    to reduce the global average travel time.
    """


    def rerouteSelectedVehicles(self, edgeID):
        """
        Selects the vehicles to be rerouted from edgeID (the edge which is currently congested) and reroutes them based
        on current estimated travel times

        Args:
            edgeID (str): The edge in which the congestion is occurring
        Returns:
            str[]: The list of vehicles to be rerouted
        """
        # The list of vehicles existing on the edges
        vehiclesList = []
        # Going through the incoming edges and identifying vehicles on them
        for edge in getMultiIncomingEdges(edgeID):
            # Appending the list of vehicles from edge onto vehiclesList
            vehiclesList.extend(traci.edge.getLastStepVehicleIDs(edge))

        # traci.edge.adaptTraveltime(edgeID, 100)

        # What vehicles have the edgeID
        for vehicle in vehiclesList:
            # The old/current path of the vehicle
            oldPath = traci.vehicle.getRoute(vehicle)
            # If the edgeID exists in the vehicles current route then reroute them
            if edgeID in traci.vehicle.getRoute(vehicle):
                # Reroute vehicles based on current travel times
                traci.vehicle.rerouteTraveltime(vehicle)
                # print("Vehicle {} heading towards edge {} has been rerouted.\n"
                #       "     Old route: {}\n"
                #       "     New route: {}".format(vehicle, edgeID, oldPath, traci.vehicle.getRoute(vehicle)))



                if edgeID not in traci.vehicle.getRoute(vehicle):
                    print("Vehicle {} heading towards edge {} has been rerouted.\n"
                          "     Old route: {}\n"
                          "     New route: {}".format(vehicle, edgeID, oldPath, traci.vehicle.getRoute(vehicle)))

        return vehiclesList

    def main(self, i):
        """
        The main programme run during the loop which progresses the simulation at every timestep

        Args:
            i (int): The current timestep of the simulation
        """
        # print("TEST LANE {}".format(getIncomingLanes("397795463_0")))
        # for lanes in sumo.net.getEdge("397795463").getLanes():
        #     print("TEST EDGE LANE {}".format(lanes.getID()))
        # print("NEIGBOURS {}".format(sumo.net.getLane("397795463_0").getNeigh()))

        # if i == 1500:
        #     print("These are the recursive edges for {}: {}".format("46538375#3", getMultiIncomingEdges("46538375#3")))
        #     print("These are the vehicles which are on and are close to edge {}: {}".format("46538375#3", self.rerouteSelectedVehicles("46538375#3")))
        #     # time.sleep(50)

        # Every 1000 timesteps
        if i % 1000 == 0 and i >= 1:
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
                    congestion = returnCongestionLevel(laneID)
                    if congestion > 0.5:
                        print(getLane2DCoordinates(laneID))
                        self.rerouteSelectedVehicles(edge)
                        # time.sleep(2)

        traci.simulationStep()

    # Greenshield's model to estimate the road speed of the current lane based on current traffic conditions
    def greenshieldsEstimatedRoadSpeed(self, vehID, edgeID):
        # Vf - Free flow speed
        vehicleLaneID = traci.vehicle.getLaneID(vehID)
        laneMaxSpeed = traci.lane.getMaxSpeed(vehicleLaneID)
        # Ki/Kjam = Ratio between current number of vehicles on the road over the maximum allowed number of vehicles
        # on that road
        currentNumberOfVehicle = traci.lane.getLastStepVehicleNumber(vehicleLaneID)

            # conn.do_job_get(Edge.getParameter(edge, "speed"));


class Testing:
    """
    Functionality is tested in this class, with various measures to check that correct output is givne
    """

    # Specifies the test which shall be performed. E.g. '1' would perform 'test1Before', 'test1During', and
    # 'test1After' PENDING
    TESTING_NUMBER = 1

    def testVehicleSetEffort(self, vehID, edgeID):
        """
        Sets the effort of a vehicle for a given edge

        Args:
            vehID (str): The ID of the vehicle
            edgeID (str): The ID of the edge
        """
        # Get the current global effort for the edge
        edgeEffortDouble = traci.edge.getEffort(edgeID, sumo.Main.getCurrentTime())
        # Sets the effort to this particular vehicle
        traci.vehicle.setEffort(vehID, edgeID, effort=edgeEffortDouble)

        print("Vehicle effort for {} on edge {} at time {}: {}"
              .format(vehID, edgeID, sumo.Main.getCurrentTime(),
                      traci.vehicle.getEffort(vehID, sumo.Main.getCurrentTime(), edgeID)))

    def test1Before(self):
        # Adding vehicle and associated route
        traci.route.add("startNode", ["46538375#5"])
        traci.vehicle.addFull("testVeh", "startNode", typeID="car")

        # GUI tracking vehicle and zoom
        traci.gui.trackVehicle("View #0", "testVeh")
        traci.gui.setZoom("View #0", traci.gui.getZoom() * sumo.ZOOM_FACTOR)

        # Changing the target of the vehicle to another edge
        traci.vehicle.changeTarget("testVeh", "569345537#2")

        # Set global efforts for the edges (across and down respectively)
        traci.edge.setEffort("46538375#7", 1)
        traci.edge.setEffort("196116976#7", 2)

    def test1During(self, i):
        if i == 10:
            self.testVehicleSetEffort("testVeh", "46538375#7")
            # Reroute based on effort
            traci.vehicle.rerouteEffort("testVeh")

            # Gets the lane in which the test vehicle is currently on
            lane = traci.vehicle.getLaneID("testVeh")
            print("{} is on lane {} which is on edge {}".format("testVeh", lane, traci.lane.getEdgeID(lane)))
            # Maximum speed allowed on the lane
            maxSpeed = traci.lane.getMaxSpeed(lane)
            print("The max speed of lane {} is {}".format(lane, maxSpeed))
            # Getting the average travel time of that lane
            meanSpeed = traci.lane.getLastStepMeanSpeed(lane)
            print("Mean speed for lane {} is {}".format(lane, meanSpeed))
            # Getting the estimated travel time for that lane
            estimatedTravelTime = traci.lane.getTraveltime(lane)
            print("Estimated travel time for lane {} is {}".format(lane, estimatedTravelTime))
            # Using sumolib to get the successive node of the edge
            print(sumo.net.getEdge('46538375#7').getToNode().getID())

            # Testing if route exists in all vehicle routes
            for veh in traci.vehicle.getIDList():
                vehicleEdges = traci.vehicle.getRoute(veh)
                if "46538375#12" in vehicleEdges:
                    print("Edge 46538375#12 is in {}'s route".format(veh))

            # Prints the incoming edges for 46538375#5
            print(getIncomingEdges("46538375#5"))
            # Prints the incoming edges for 196116976#7
            print(getIncomingEdges("196116976#7"))

            print("Recursive edges for 511924978#1 are: {}".format(getMultiIncomingEdges("511924978#1")))

            print("The current congestion for lane {} is {}".format(lane, returnCongestionLevel(lane)))

        traci.simulationStep()

    def test2Before(self):
        pass

    def test2During(self, i):
        pass

    def beforeLoop(self):
        if self.TESTING_NUMBER == 1:
            self.test1Before()
        elif self.TESTING_NUMBER == 2:
            self.test2Before()

    def duringLoop(self, i):
        if self.TESTING_NUMBER == 1:
            self.test1During(i)
        elif self.TESTING_NUMBER == 2:
            self.test2During(i)



