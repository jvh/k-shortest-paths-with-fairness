import traci
import time

from src.project.small_manhattan.traci_code import SumoConnection as sumo

TESTING_NUMBER = 1


class Testing:

    def testVehicleSetEffort(self, vehID, edgeID):
        """ Sets the effort of a vehicle for a given edge """
        # Get the current global effort for the edge
        edgeEffortDouble = traci.edge.getEffort(edgeID, sumo.Main.getCurrentTime())
        # Sets the effort to this particular vehicle
        traci.vehicle.setEffort(vehID, edgeID, effort=edgeEffortDouble)

        print("Vehicle effort for {} on edge {} at time {}: {}"
              .format(vehID, edgeID, sumo.Main.getCurrentTime(),
                      traci.vehicle.getEffort(vehID, sumo.Main.getCurrentTime(), edgeID)))

    def getIncomingEdges(self, edgeID):
        """ Returns a list of all of the incoming edges to the specified edge """
        incEdgeList = []
        for edgeInc in sumo.net.getEdge(edgeID).getIncoming():
            incEdgeList.append(edgeInc.getID())
        return incEdgeList

    # def recursiveIncomingEdges(self, edgeID, limit=0, edgeList=[]):
    #     """ Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
    #      away """
    #     # CHECK IF THE EDGE IS AT THE EDGE OF THE MAP (USING SUMOLIB)
    #     # ALSO, USE ++variable RATHER THAN variable += 1
    #     if limit < 2:
    #         edges = self.getIncomingEdges(edgeID)
    #         for edge in edges:
    #
    #     else:
    #         return edgeList

    def recursiveIncomingEdgesNew(self, edgeID, firstTime, limit=0, edgeList=[], eg=["test"], edgeOrderList={}):
        """ Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
         away """
        # CHECK IF THE EDGE IS AT THE EDGE OF THE MAP (USING SUMOLIB)
        # ALSO, USE ++variable RATHER THAN variable += 1
        if eg or limit < 2:
            if eg == ["test"]:
                eg.remove("test")
            if edgeID != "" and limit < 2:



                edges = self.getIncomingEdges(edgeID)
                for edge in edges:
                    print("edge {} and edges {}".format(edge, edges))
                    edgeList.append(edge)
                    eg.append(edge)
            # for e in eg:
            explore = eg.pop()
            if limit < 2:
                limit += 1
                return self.recursiveIncomingEdges(explore, limit, edgeList, eg)
            else:
                return self.recursiveIncomingEdges(explore, 0, eg)
        else:
            return edgeList

    def recursiveIncomingEdges(self, edgeID, firstTime=False, edgeList=[], edgesToSearch=["placeholder"], edgeOrderList={}, finished=False):
        """ Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
         away """
        # CHECK IF THE EDGE IS AT THE EDGE OF THE MAP (USING SUMOLIB)
        # ALSO, USE ++variable RATHER THAN variable += 1
        if (edgesToSearch or edgeOrderList[edgeID] != sumo.EDGE_RECURSIONS) and not finished:
            if firstTime:
                edgeOrderList[edgeID] = 0
                edgesToSearch.remove("placeholder")

            edges = self.getIncomingEdges(edgeID)
            for edge in edges:
                print("edge {} and edges {}".format(edge, edges))
                edgeList.append(edge)
                edgeOrderList[edge] = edgeOrderList[edgeID] + 1
                if edgeOrderList[edge] != sumo.EDGE_RECURSIONS:
                    edgesToSearch.append(edge)

            print("NOW HERE {}".format(edgeOrderList))

            # There are still more edges to search
            if edgesToSearch:
                # Pop
                edgeToTest = edgesToSearch.pop()
                finished = False
            # If there are no more edges to search
            else:
                finished = True
                # Prevent an error as there are no more edges to test
                edgeToTest = edgeID
            return self.recursiveIncomingEdges(edgeToTest, finished=finished, edgeList=edgeList, edgesToSearch=edgesToSearch, edgeOrderList=edgeOrderList)
        else:
            return edgeList

    def getMultiIncomingEdges(self, edgeID):
        """ User friendly approach to getting the number of incoming edges from an edge """
        return self.recursiveIncomingEdges(edgeID, firstTime=True)

    def recursiveIncomingEdgeskajdl(self, edgeID="null", limit=0, edgeList=[], eg=[]):
        """ Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
         away """
        # CHECK IF THE EDGE IS AT THE EDGE OF THE MAP (USING SUMOLIB)
        # ALSO, USE ++variable RATHER THAN variable += 1
        if limit < 2:
            edges = self.getIncomingEdges(edgeID)
            if not eg:
                eg = edges
            for edge in eg:
                print("edge {} and edges {}".format(edge, eg))
                edgeList.append(edge)
                eg.remove(edge)
                limit += 1
                return self.recursiveIncomingEdges(edge, limit, edgeList, eg)
        else:
            if eg:
                return self.recursiveIncomingEdges(limit=0, edgeList=edgeList, edgesToSearch=eg)
            else:
                return edgeList

    def recursiveIncomingEdges4(self, edgeID="null", limit=0, edgeList=[], eg=[]):
        """ Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
         away """
        # CHECK IF THE EDGE IS AT THE EDGE OF THE MAP (USING SUMOLIB)
        # ALSO, USE ++variable RATHER THAN variable += 1
        if limit < 2:
            edges = self.getIncomingEdges(edgeID)
            if not eg:
                eg = edges
            for edge in eg:
                print("edge {} and edges {}".format(edge, eg))
                edgeList.append(edge)
                eg.remove(edge)
                limit += 1
                return self.recursiveIncomingEdges(edge, limit, edgeList, eg)
        else:
            if eg:
                return self.recursiveIncomingEdges(limit=0, edgeList=edgeList, edgesToSearch=eg)
            else:
                return edgeList

        def recursiveIncomingEdges3(self, edgeID, limit=0, edgeList=[]):
            """ Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
             away """
            # CHECK IF THE EDGE IS AT THE EDGE OF THE MAP (USING SUMOLIB)
            # ALSO, USE ++variable RATHER THAN variable += 1
            if limit < 2:
                edges = self.getIncomingEdges(edgeID)
                for edge in edges:
                    print("edge {} and edges {}".format(edge, edges))
                    edgeList.append(edge)
                    limit += 1
                    return self.recursiveIncomingEdges(edge, limit, edgeList)
            else:
                return edgeList

        def recursiveIncomingEdges2(self, edgeID, internalCounter=0, num=0, limit=0, edgeList=[], oldList=[]):
            """ Recurses down the incoming edges of the edge defined to return a list of all of the incoming edges from x edges
             away """
            # CHECK IF THE EDGE IS AT THE EDGE OF THE MAP (USING SUMOLIB)
            # ALSO, USE ++variable RATHER THAN variable += 1
            if limit <= self.NUMBER_OF_RECURSIONS:

                edges = self.getIncomingEdges(edgeID)
                list2 = []
                if not oldList:
                    limit += 1
                    oldList = edges
                    for s in oldList:
                        oldList.remove(s)
                        return self.recursiveIncomingEdges(s, internalCounter, num, limit, edgeList, oldList)
                else:
                    for s in oldList:
                        oldList.remove(s)
                        return self.recursiveIncomingEdges(s, internalCounter, num, limit, edgeList, oldList)

                        # if num == 0:
                        #     numberOfEdges = len(edges)
                        #     num = numberOfEdges
                        # for edge in edges:
                        #     print("edge {} and edges {}".format(edge, edges))
                        #     edgeList.append(edge)
                        #     # if internalCounter <= num:
                        #     if internalCounter <= self.NUMBER_OF_RECURSIONS:
                        #         internalCounter += 1
                        #         return self.recursiveIncomingEdges(edge, internalCounter, num, limit, edgeList, list2)
                        # limit += 1
                        # return self.recursiveIncomingEdges(edge, 0, 0, limit, edgeList)
                        # return self.recursiveIncomingEdges(edge, 0, 0, limit, edgeList)
                        # return
            else:
                return edgeList

    def test1Before(self):
        # Adding vehicle and associated route
        traci.route.add("startNode", ["46538375#5"])
        traci.vehicle.addFull("testVeh", "startNode", typeID="car")

        # GUI tracking vehicle and zoom
        traci.gui.trackVehicle("View #0", "testVeh")
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

            # print("Recursive edges for 196116976#7 are: {}".format(self.recursiveIncomingEdges("196116976#7", firstTime=True)))
            print("Recursive edges for 511924978#1 are: {}".format(self.getMultiIncomingEdges("511924978#1")))


            time.sleep(2)

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
        # Ki/Kjam = Ratio between current number of vehicles on the road over the maximum allowed number of vehicles on that road
        currentNumberOfVehicle = traci.lane.getLastStepVehicleNumber(vehicleLaneID)

            # conn.do_job_get(Edge.getParameter(edge, "speed"));
