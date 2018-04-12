import sys

import traci
import time

from src.project.code import SumoConnection as sumo
from src.project.code import HelperFunctions as func

# Specifies the test which shall be performed. E.g. '1' would perform 'test1BeforeX' and 'test1DuringX'
TESTING_NUMBER = 1

class Testing:
    """
    Functionality is tested in this class, with various measures to check that correct output is given
    """

    def setupGenericCarSM(self):
        """
        Sets up a generic vehicle on the road network with a route (only to be used on small manhattan)
        """
        # Adding vehicle and associated route
        traci.route.add("startNode", ["46538375#5"])
        traci.vehicle.addFull("testVeh", "startNode", typeID="car")

        # GUI tracking vehicle and zoom
        traci.gui.trackVehicle("View #0", "testVeh")
        traci.gui.setZoom("View #0", traci.gui.getZoom() * sumo.ZOOM_FACTOR)

        # Changing the target of the vehicle to another edge
        traci.vehicle.changeTarget("testVeh", "569345537#2")

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

    ###### SMALL_SOUTHAMPTON ######

    def test1BeforeSM(self):
        self.setupGenericCarSM()

        # Set global efforts for the edges (across and down respectively)
        traci.edge.setEffort("46538375#7", 1)
        traci.edge.setEffort("196116976#7", 2)

    def test1DuringSM(self, i):
        if i == 10:
            self.testVehicleSetEffort("testVeh", "46538375#7")
            # Reroute based on effort
            # traci.vehicle.rerouteTraveltime("testVeh")
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
            print(func.getIncomingEdges("46538375#5"))
            # Prints the incoming edges for 196116976#7
            print(func.getIncomingEdges("196116976#7"))

            print("Recursive edges for 511924978#1 are: {}".format(
                func.getMultiIncomingEdges("511924978#1")))

            print("The current congestion for lane {} is {}".format(lane, func.returnCongestionLevelLane(lane)))

        traci.simulationStep()

    def test2BeforeSM(self):
        self.setupGenericCarSM()

        traci.vehicle.rerouteTraveltime("testVeh")

        edge = "46538375#5"
        outgoingEdges = func.getOutgoingEdges(edge)
        print("These are the outgoing edges for edge {}: {}".format(edge, outgoingEdges))

        print("Estimated route path time: {}".format(func.getRoutePathTime("testVeh")))
        routes = traci.vehicle.getRoute("testVeh")
        print("This is the route: {}".format(routes))
        func.penalisePathTime("testVeh", routes)
        print("This is the adjusted route time {}".format(func.getRoutePathTime("testVeh")))

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        print("This is the route {}".format(traci.vehicle.getRoute("testVeh")))
        print("This is the route after rerouting {}".format(
            func.getRoutePathTime("testVeh")))

    def test2DuringSM(self, i):
        if i == 4:
            print("************** STARTING LOOP **************")
            print("EDGE 46538375#6 OKKKK {}".format(traci.vehicle.getAdaptedTraveltime("testVeh",
                                                                                       time=sumo.Main.getCurrentTime(),
                                                                                       edgeID="46538375#6")))

            print("This is the current time {}".format(sumo.Main.getCurrentTime()))
            print("EDGE 46538375#6 LOOP {}".format(traci.vehicle.getAdaptedTraveltime("testVeh",
                                                                                      time=sumo.Main.getCurrentTime(),
                                                                                      edgeID="46538375#6")))
            traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)

            print("meeeppp")
            print("This is the route {}".format(traci.vehicle.getRoute("testVeh")))
            print("This is the route after rerouting {}".format(
                func.getRoutePathTime("testVeh")))

        traci.simulationStep()

    def test3BeforeSM(self):
        self.setupGenericCarSM()
        # func.loadMap()
        print(func.edgesNetwork)

        # Testing to ensure fringeEdges() only returns edges which actually exist on the fringe
        for edge in func.fringeEdges:
            if not sumo.net.getEdge(edge).is_fringe():
                print("NOT FRINGE")
        print("These are the lane lengths {}".format(func.laneLengths))
        print("These are the edge lengths {}".format(func.edgeLengths))

    def test3DuringSM(self, i):


        if i == 2:
            func.kPaths("testVeh")

        if i == 20:
            func.endSim(i)

        traci.simulationStep()

    ###### NEWARK ######

    def test1BeforeNW(self):
        print("-11622114#5 are: ['-11618400#1', '-11622114#4', '11618400#2', '11622114#5']")

        # Adding vehicle and associated route
        traci.route.add("startNode", ["-11622114#5"])
        traci.vehicle.addFull("testVeh", "startNode", typeID="car")

        # GUI tracking vehicle and zoom
        traci.gui.trackVehicle("View #0", "testVeh")
        traci.gui.setZoom("View #0", traci.gui.getZoom() * sumo.ZOOM_FACTOR)

        # Changing the target of the vehicle to another edge
        traci.vehicle.changeTarget("testVeh", "-11618400#1")

    def test1DuringNW(self, i):
        traci.simulationStep()

    def test2BeforeNW(self):
        print("This is the entire road network {}".format(func.edgesNetwork))
        print("These are all of the lanes {}".format(func.lanesNetwork))
        print()
        print("This is the directed lane graph {}".format(func.directedGraphLanes))
        print()

        print(sumo.net.getLane(""))

        #
        # for edgeOut in sumo.net.getEdge("-11613734#0").getOutgoing():
        #     print(edgeOut)
        #
        # print()

        for laneOut in sumo.net.getLane("277181763#0_1").getOutgoing():
            print(laneOut.getToLane().getID())

    def test2DuringNW(self, i):
        pass
        # traci.simulationStep()

    def beforeLoop(self):
        """
        This is the testing stage which is ran before the main loop of the program begins
        """
        # Input validation
        if not 0 <= TESTING_NUMBER <= 3:
            sys.exit("Please enter a valid TESTING_NUMBER")

        if sumo.SCENARIO == 0:
            if TESTING_NUMBER == 0:
                print("******* TEST CASES BEING RAN ON SMALL_MANHATTAN *******")
            elif TESTING_NUMBER == 1:
                print("******* TEST 1 RUNNING ON SMALL_MANHATTAN *******")
                self.test1BeforeSM()
            elif TESTING_NUMBER == 2:
                print("******* TEST 2 RUNNING ON SMALL_MANHATTAN *******")
                self.test2BeforeSM()
            elif TESTING_NUMBER == 3:
                print("******* TEST 3 RUNNING ON SMALL_MANHATTAN *******")
                self.test3BeforeSM()
        elif sumo.SCENARIO == 3:
            if TESTING_NUMBER == 0:
                print("******* TEST CASES BEING RAN ON NEWARK *******")
            elif TESTING_NUMBER == 1:
                print("******* TEST 1 RUNNING ON NEWARK *******")
                self.test1BeforeNW()
            elif TESTING_NUMBER == 2:
                print("******* TEST 2 RUNNING ON NEWARK *******")
                self.test2BeforeNW()

    def duringLoop(self, i):
        """
        This is the testing stage which is ran continuously during the loop
        Args:
            i (int): This is the number of timesteps
        """
        if sumo.SCENARIO == 0:
            if TESTING_NUMBER == 0:
                pass
            elif TESTING_NUMBER == 1:
                self.test1DuringSM(i)
            elif TESTING_NUMBER == 2:
                self.test2DuringSM(i)
            elif TESTING_NUMBER == 3:
                self.test3DuringSM(i)
        elif sumo.SCENARIO == 3:
            if TESTING_NUMBER == 0:
                pass
            elif TESTING_NUMBER == 1:
                self.test1DuringNW(i)
            elif TESTING_NUMBER == 2:
                self.test2DuringNW(i)