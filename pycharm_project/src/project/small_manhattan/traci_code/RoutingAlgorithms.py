import traci
import time

from src.project.small_manhattan.traci_code import SumoConnection as sumo

TESTING_NUMBER = 1


class Testing:

    def returnCongestionLevel(self, laneID):
        """
        Gives the congestion level of the road, laneID

        Args:
            laneID (str): The ID of the lane (road)
         Return:
             float: The occupancy (congestion) of the road, in percentage
        """
        return traci.lane.getLastStepOccupancy(laneID)

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

    def getIncomingEdges(self, edgeID):
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


    def recursiveIncomingEdges(self, edgeID, firstTime=False, edgeList=[], edgesToSearch=["placeholder"],
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
                edgeOrderList[edgeID] = 0
                # Remove the placeholder value from the edgesToSearch stack
                edgesToSearch.remove("placeholder")

            # Gets the immediate incoming edges for edgeID
            edges = self.getIncomingEdges(edgeID)
            for edge in edges:
                edgeList.append(edge)
                # The new edge has range of edgeOrderList[edgeID] + 1 away from the original edge
                edgeOrderList[edge] = edgeOrderList[edgeID] + 1
                # If the range of the edge isn't the maximum range
                if edgeOrderList[edge] != sumo.MAX_EDGE_RECURSIONS_RANGE:
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
            return self.recursiveIncomingEdges(edgeToTest, finished=finished, edgeList=edgeList,
                                               edgesToSearch=edgesToSearch, edgeOrderList=edgeOrderList)
        else:
            return edgeList

    def getMultiIncomingEdges(self, edgeID):
        """
        User friendly approach to getting the number of incoming edges from an edge (the recursiveIncomingEdge()
        function)

        Args:
            edgeID (str): The initial edge
        Returns:
            str[]: The edges incoming to the initial edge up to MAX_EDGE_RECURSION_RANGE
        """
        return self.recursiveIncomingEdges(edgeID, firstTime=True)

    def test1Before(self):
        # Adding vehicle and associated route
        traci.route.add("startNode", ["46538375#5"])
        traci.vehicle.addFull("testVeh", "startNode", typeID="car")

        # GUI tracking vehicle and zoom
        # traci.gui.trackVehicle("View #0", "testVeh")
        traci.gui.setZoom("View #0", traci.gui.getZoom() * sumo.ZOOM_FACTOR)

        # Changing the target of the vehicle to another edge
        traci.vehicle.changeTarget("testVeh", "569345537#2")

        # Set global efforts for the edges
        traci.edge.setEffort("46538375#8", 1)
        traci.edge.setEffort("196116976#7", 2)

    def test1During(self, i):
        if i == 10:
            self.testVehicleSetEffort("testVeh", "46538375#8")
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
            print(sumo.net.getEdge('46538375#5').getToNode().getID())

            # Testing if route exists in all vehicle routes
            for veh in traci.vehicle.getIDList():
                vehicleEdges = traci.vehicle.getRoute(veh)
                if "46538375#12" in vehicleEdges:
                    print("Edge 46538375#12 is in {}'s route".format(veh))

            # Prints the incoming edges for 46538375#5
            print(self.getIncomingEdges("46538375#5"))
            # Prints the incoming edges for 196116976#7
            print(self.getIncomingEdges("196116976#7"))

            print("Recursive edges for 511924978#1 are: {}".format(self.getMultiIncomingEdges("511924978#1")))

            print("The current congestion for lane {} is {}".format(lane, self.returnCongestionLevel(lane)))

            # time.sleep(2)

        print("i({}) % {} = {}".format(i, 10, i%10))


        if i % 100 == 0 and i>=1:
            print("hello")
            for laneID in traci.lane.getIDList():
                congestion = self.returnCongestionLevel(laneID)
                if congestion > 0.5 and congestion < 0.9:
                    edge = traci.lane.getEdgeID(laneID)
                    # Removing the first character from edge (from the left) because for some reason .getEdgeID()
                    # returns the edge with a ':' prepended
                    edgeReFormat = edge[1:]
                    print("Edge {}".format(edge))
                    # Getting one of the nodes associated with that edge
                    node = sumo.net.getEdge(edge).getFromNode().getID()
                    # Getting the 2D coordinates for that node
                    x,y = sumo.net.getNode(node).getCoord()
                    print("Position {}, {}".format(x, y))
                    traci.gui.setOffset("View #0", x, y)
                    print("Lane {} has congestion level {}".format(laneID, self.returnCongestionLevel(laneID)))
                    time.sleep(20)


        traci.simulationStep()

    def test2Before(self):
        pass

    def test2During(self):
        return

    def beforeLoop(self):
        if TESTING_NUMBER == 1:
            self.test1Before()
        elif TESTING_NUMBER == 2:
            self.test2Before()

    def duringLoop(self):
        if TESTING_NUMBER == 1:
            self.test1During()
        elif TESTING_NUMBER == 2:
            self.test2During()


class DynamicShortestPath:

    # Greenshield's model to estimate the road speed of the current lane based on current traffic conditions
    def greenshieldsEstimatedRoadSpeed(self, vehID, edgeID):
        # Vf - Free flow speed
        vehicleLaneID = traci.vehicle.getLaneID(vehID)
        laneMaxSpeed = traci.lane.getMaxSpeed(vehicleLaneID)
        # Ki/Kjam = Ratio between current number of vehicles on the road over the maximum allowed number of vehicles
        # on that road
        currentNumberOfVehicle = traci.lane.getLastStepVehicleNumber(vehicleLaneID)

            # conn.do_job_get(Edge.getParameter(edge, "speed"));
