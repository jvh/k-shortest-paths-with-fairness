import sys

import traci
import time

from src.code import SumoConnection as sumo
from src.code import RoutingFunctions as func
from src.code import InitialMapHelperFunctions as initialFunc
from src.code import SimulationFunctions as sim

__author__ = "Jonathan Harper"

"""
Used to test various scenarios during the runtime of TraCI and seeing how the simulation reacts in accordance to these.
"""

# Specifies the test which shall be performed. E.g. '1' would perform 'test1BeforeX' and 'test1DuringX'
TESTING_NUMBER = 1

class Testing:
    """
    Functionality is tested in this class, with various measures to check that correct output is given
    """

    @staticmethod
    def setupGenericCarSM(name="testVeh", startPos=["46538375#5"], target="569345537#2", zoom=True,
                          routeName="startNode", initialise=False):
        """
        Sets up a generic vehicle on the road network with a route (only to be used on small manhattan)

        Args:
            name (str): Specifies the name of the vehicle input
            startPos  [str]: The original starting position/route of the vehicle
            target (str): The target in which the vehicle shall be rerouted to
            zoom (bool): True if the camera should be panned to this vehicle
            routeName (str): The name of the route in which the vehicle shall be taking
            initialise (bool): Whether or not fairness values should be initialised with the vehicle
        """
        # Adding vehicle and associated route
        traci.route.add(routeName, startPos)
        traci.vehicle.addFull(name, routeName, typeID="car")

        if zoom:
            # GUI tracking vehicle and zoom
            traci.gui.trackVehicle("View #0", name)
            traci.gui.setZoom("View #0", traci.gui.getZoom() * sumo.ZOOM_FACTOR)

        # Changing the target of the vehicle to another edge
        traci.vehicle.changeTarget(name, target)

        if initialise:
            func.vehicleReroutedAmount[name] = 0
            func.cumulativeExtraTime[name] = 0
            sim.timeSpentInNetwork[name] = 0
            sim.timeSpentStopped[name] = 0

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
            print(initialFunc.getIncomingEdges("46538375#5"))
            # Prints the incoming edges for 196116976#7
            print(initialFunc.getIncomingEdges("196116976#7"))

            print("Recursive edges for 511924978#1 are: {}".format(
                initialFunc.getMultiIncomingEdges("511924978#1")))

            print("The current congestion for lane {} is {}".format(lane, sim.returnCongestionLevelLane(lane)))

        traci.simulationStep()

    def test2BeforeSM(self):
        self.setupGenericCarSM()
        traci.simulationStep()

        traci.vehicle.rerouteTraveltime("testVeh")

        edge = "46538375#5"
        outgoingEdges = initialFunc.getOutgoingEdges(edge)
        print("These are the outgoing edges for edge {}: {}".format(edge, outgoingEdges))

        print("Estimated route path time: {}".format(
            sim.getRoutePathTimeVehicle("testVeh")))
        routes = traci.vehicle.getRoute("testVeh")
        print("This is the route: {}".format(routes))
        func.penalisePathTimeVehicle("testVeh", routes)
        print("This is the adjusted route time {}".format(
            sim.getRoutePathTimeVehicle("testVeh")))

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        print("This is the route {}".format(traci.vehicle.getRoute("testVeh")))
        print("This is the route after rerouting {}".format(
            sim.getRoutePathTimeVehicle("testVeh")))

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
                sim.getRoutePathTimeVehicle("testVeh")))

        traci.simulationStep()

    def test3BeforeSM(self):
        self.setupGenericCarSM()
        # func.loadMap()
        print(initialFunc.edgesNetwork)

        # Testing to ensure fringeEdges() only returns edges which actually exist on the fringe
        for edge in initialFunc.fringeEdges:
            if not sumo.net.getEdge(edge).is_fringe():
                print("NOT FRINGE")
        print("These are the lane lengths {}".format(initialFunc.laneLengths))
        print("These are the edge lengths {}".format(initialFunc.edgeLengths))

    def test3DuringSM(self, i):


        if i == 2:
            func.kPaths("testVeh")

        if i == 20:
            initialFunc.endSim(i)

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
        print("This is the entire road network {}".format(initialFunc.edgesNetwork))
        print("These are all of the lanes {}".format(initialFunc.lanesNetwork))
        print()
        print("This is the directed lane graph {}".format(
            initialFunc.directedGraphLanes))
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

    def beforeLoop(self, functionName=""):
        """
        This is the testing stage which is ran before the main loop of the program begins

        Args:
            functionName (str): The name of the function which called this
        """
        # Input validation
        if not 0 <= TESTING_NUMBER <= 3:
            sys.exit("Please enter a valid TESTING_NUMBER")

        if sumo.SCENARIO == 0:
            if TESTING_NUMBER == 0:
                if functionName != "":
                    print("******* TEST CASE " + functionName + " BEING RAN *******")
                else:
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
                if functionName != "":
                    print("******* TEST CASE " + functionName + " BEING RAN *******")
                else:
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