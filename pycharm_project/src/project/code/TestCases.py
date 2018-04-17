import unittest
import sumolib
import os
import traci
from copy import deepcopy

from src.project.code import SumoConnection as sumo
from src.project.code import RoutingAlgorithms as routing
from src.project.code import HelperFunctions as func
from src.project.code import Testing as testing
from src.project.code import InitialMapHelperFunctions as initialFunc


class SmallSouthamptonTestsRoute(unittest.TestCase):
    """
    These test cases must change the route file in order to run the tests
    """

    def setUp(self):
        if sumo.SCENARIO != 0:
            raise unittest.SkipTest("Scenario is {}, small Manhattan unit tests shall not be executed."
                                    .format(sumo.SCENARIO))
        else:
            testing.TESTING_NUMBER = 0

    def tearDown(self):
        traci.close(False)
        del self.main

    def test_smallManhattan_kPaths_lessThanMaxSelection(self):
        """
        Assumption that k = 3
        In this situation, the initial best path is congested with traffic, therefore, once kPaths() is called it will
        deviate away from the best path at start up (as there are no vehicle's when the simulation initially begins) to
        a more appropriate route. However, given that the next best route other than the one initially selected in
        kPaths() is >20% worse in terms of time taken, no further routes should be selected.
        """
        sumo.K_MAX = 3
        routeFile = sumo.MAIN_PROJECT + "small_manhattan/testing/routes_sm_rerouting_test.xml"
        self.main = sumo.Main()
        self.main.run(True, True, True, routeFile)
        testing.Testing().setupGenericCarSM()

        traci.vehicle.rerouteTraveltime("testVeh")
        initialRoute = traci.vehicle.getRoute("testVeh")

        for i in range(4):
            traci.simulationStep()

        func.getGlobalEdgeWeights()
        routeList = func.kPaths("testVeh")

        self.assertTrue(initialRoute not in routeList and len(routeList) < sumo.K_MAX)

    def test_smallManhattan_manualTravelTimes(self):
        """
        Tests altering the current travel times and the affects on the rerouting of the vehicle when considering the
        manual travel times

        Pass if the routes are different (as the vehicle should want to change route to reflect the traffic along the
        fastest route at runtime due to the routes file - traffic manually created)
        """
        # This route file purposely sends drivers down the fastest route (at runtime)
        routeFile = sumo.MAIN_PROJECT + "small_manhattan/testing/routes_sm_rerouting_test.xml"
        self.main = sumo.Main()
        self.main.run(True, True, True, routeFile)
        testing.Testing().setupGenericCarSM()

        for i in range(4):
            traci.simulationStep()

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        currentRoute = traci.vehicle.getRoute("testVeh")
        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute("testVeh")

        print("This is the current {}".format(currentRoute))
        print("This is the new {}".format(newRoute))

        self.assertNotEqual(currentRoute, newRoute)

    def test_smallManhattan_automaticTravelTimeAdjustment(self):
        """
        The travel time for each edge is adjusted manually to reflect the current traffic conditions, meaning that when
        currentTravelTimes=False, the rerouting should still consider the current travel times

        Pass if both the currentTravelTimes=False and True are both the same, given that they both represent the true
        travel times
        """
        # This route file purposely sends drivers down the fastest route (at runtime)
        routeFile = sumo.MAIN_PROJECT + "small_manhattan/testing/routes_sm_rerouting_test.xml"
        self.main = sumo.Main()
        self.main.run(True, True, True, routeFile)
        testing.Testing().setupGenericCarSM()

        for i in range(4):
            traci.simulationStep()

        func.getGlobalEdgeWeights()

        for edge in func.edgeSpeedGlobal.keys():
            traci.edge.adaptTraveltime(edge, func.edgeSpeedGlobal[edge])

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        currentRoute = traci.vehicle.getRoute("testVeh")
        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute("testVeh")

        self.assertEqual(currentRoute, newRoute)

class SmallSouthamptonTests(unittest.TestCase):
    """
    Tests ran when the scenario is 'Testing (small_manhattan)'
    """

    def setUp(self):
        """
        Ensures that the scenario is that of 'Testing (small_manhattan)'
        """
        if sumo.SCENARIO != 0:
            raise unittest.SkipTest("Scenario is {}, small Manhattan unit tests shall not be executed."
                                    .format(sumo.SCENARIO))
        else:
            testing.TESTING_NUMBER = 0
            self.main = sumo.Main()
            self.main.run(True, True, True)

    def tearDown(self):
        """
        Closes the traci connection once used
        """
        traci.close(False)
        del self.main

    def test_smallManhattan_manualTravelTimes(self):
        """
        Tests altering the current travel times and the affects on the rerouting of the vehicle when considering the
        manual travel times
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()
        # routeFile =

        for i in range(2):
            traci.simulationStep()

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        currentRoute = traci.vehicle.getRoute("testVeh")
        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute("testVeh")

        self.assertEqual(currentRoute, newRoute)



    def test_smallManhattan_edgeSpeedGlobal_remainsConstant(self):
        """
        Ensuring that when calls are made to edgeSpeedGlobal, it stays the same throughout until getGlobalEdgeWeights()
        is called again.
        """
        pass

    def test_smallManhattan_multiIncomingRecursion_4Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 2
        """
        sumo.MAX_EDGE_RECURSIONS_RANGE = 4
        output = initialFunc.getMultiIncomingEdges("511924978#1")
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '497165753#5', '569345508#1',
                          '5673497', '458180186#0', '497165756#2', '497165756#1', '5673063#5', '497165756#0',
                          '497165756#4', '569345508#0', '5672118#0', '497165753#4', '458180191#2', '5670867#0'}
        self.assertEqual(set(output), expectedOutput)

    def test_smallManhattan_multiIncomingRecursion_3Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 3
        """
        sumo.MAX_EDGE_RECURSIONS_RANGE = 3
        output = initialFunc.getMultiIncomingEdges("511924978#1")
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '497165753#5', '569345508#1',
                          '5673497', '458180186#0', '497165756#2', '497165756#1'}
        self.assertEqual(set(output), expectedOutput)

    def test_smallManhattan_multiIncomingRecursion_2Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 2
        """
        sumo.MAX_EDGE_RECURSIONS_RANGE = 2
        output = initialFunc.getMultiIncomingEdges("511924978#1")
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '458180186#0', '497165756#2'}
        self.assertEqual(set(output), expectedOutput)

    def test_smallManhattan_directedGraphsEdges(self):
        """
        Tests that the directedGraphsEdges has been populated correctly (the edge has the correct outgoing edges)
        """
        self.assertEqual(initialFunc.directedGraphEdges['196116976#11'], {'46443656#3', '196116976#12'})

    def test_smallManhattan_directedGraphsLanes(self):
        """
        Tests that the directedGraphsLanes has been populated correctly (the lane has the correct outgoing lanes)
        """
        self.assertEqual(initialFunc.directedGraphLanes['542258337#5_1'], {'569345540#5_3', '569345540#5_2',
                                                                           '46443656#0_1'})

    def test_smallManhattan_singleOutgoingEdges(self):
        """
        True if the singleOutgoingEdges variable contains only edges with a single outgoing edge
        """
        for edge in initialFunc.singleOutgoingEdges:
            # Running with a subtest to identify point of failure (if any)
            with self.subTest(status_code=edge):
                self.assertEqual(len(sumo.net.getEdge(edge).getOutgoing()), 1)

    def test_smallManhattan_reroutingLanes(self):
        """
        True if all the lanes contained within reroutingLanes have at least 2 outgoing lanes
        """
        for lane in initialFunc.reroutingLanes:
            with self.subTest(status_code=lane):
                edge = traci.lane.getEdgeID(lane)
                self.assertGreaterEqual(len(sumo.net.getEdge(edge).getOutgoing()), 2)

    def test_smallManhattan_fringeEdges(self):
        """
        True if all edges held within fringeEdges are fringe edges (edges on the fringe of the network - no incoming
        edges) in the traffic network
        """
        for edge in initialFunc.fringeEdges:
            with self.subTest(status_code=edge):
                self.assertTrue(sumo.net.getEdge(edge).is_fringe())

    def test_smallManhattan_edgeSpeedGlobal(self):
        """
        Testing if the speeds in edgeSpeedGlobal match the speeds given directly by Traci after sim steps given a single
        vehicle. When the vehicle is rerouted and currentTravelTimes=True and False, the currentTravelTimes=False
        estimated journey time should give the same result given that the global edge weights have been updated in
        edgeSpeedGlobal[] at the same point in which currentTravelTimes=True is called (i.e. they both have the same
        estimated travel times).

        Additionally, the routes should be the same given that the same travel times are returned
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()

        # Run some simulation steps so to make sure the simulation has had time to change the estimated travel times
        # away from the initial global
        for i in range(19):
            traci.simulationStep()

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        estimatedRouteTimeTrue = func.getRoutePathTimeVehicle("testVeh")
        routeCurrentTrue = traci.vehicle.getRoute("testVeh")

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        estimatedRouteTimeFalse = func.getRoutePathTimeVehicle("testVeh")
        routeCurrentFalse = traci.vehicle.getRoute("testVeh")

        self.assertTrue((estimatedRouteTimeTrue == estimatedRouteTimeFalse) and (routeCurrentTrue == routeCurrentFalse))

    def test_smallManhattan_edgeSpeedGlobal_twice(self):
        """
        Checks that after a number of timesteps the edgeSpeedGlobal variable doesn't contain the times held in the
        previous check (as the simulation runs the vehicle in the simulation should change the estimated travel time).

        Pass if the 2 edgeSpeedGlobal's aren't identical
        """
        testing.Testing().setupGenericCarSM()

        edgeSpeed1 = {}
        edgeSpeed2 = {}

        for i in range(600):
            traci.simulationStep()
            # Vehicle is still in simulation
            if i == 20:
                func.getGlobalEdgeWeights()
                # Using deepcopy as an alternative to call-by-value
                edgeSpeed1 = deepcopy(func.edgeSpeedGlobal)
            # By this time vehicle has finished route and has left the simulation
            if i == 500:
                func.getGlobalEdgeWeights()
                edgeSpeed2 = deepcopy(func.edgeSpeedGlobal)

        self.assertNotEqual(edgeSpeed1, edgeSpeed2)


    def test_smallManhattan_getRoutePathTime_noRouteArgument(self):
        """
        Checks whether or not the estimated time returned upon calling getRoutePathTimeVehicle(), leaving the 'route'
        argument as being default (null), returns the correct result based on the current traffic conditions
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()

        totalPathTime = 0
        for edge in traci.vehicle.getRoute("testVeh"):
            # This returns the estimated travel time for this edge
            totalPathTime += traci.edge.getTraveltime(edge)

        self.assertEqual(totalPathTime, func.getRoutePathTimeVehicle("testVeh"))

    def test_smallManhattan_getRoutePathTime_routeArgument(self):
        """
        Checks whether or not the estimated time returned upon calling getRoutePathTimeVehicle() returns the correct
        result based on the current traffic conditions given that a route argument is given which doesn't correspond to
        the vehicle's current route
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()

        # This route isn't the same as the current vehicle's route
        testingVehicleRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '196116976#11', '196116976#12']

        totalPathTime = 0
        for edge in testingVehicleRoute:
            # This returns the estimated travel time for this edge
            totalPathTime += traci.edge.getTraveltime(edge)

        self.assertEqual(totalPathTime, func.getRoutePathTimeVehicle("testVeh", testingVehicleRoute))

    def test_smallManhattan_fringeEdges(self):
        """
        True if all edges held within fringeEdges are fringe edges (edges on the fringe of the network - no incoming
        edges) in the traffic network
        """
        for edge in initialFunc.fringeEdges:
            with self.subTest(status_code=edge):
                self.assertTrue(sumo.net.getEdge(edge).is_fringe())

    def test_smallManhattan_penalisePathTimeVehicle_routeTime(self):
        """
        Checks that the penalisePathTimeVehicle() method penalises the path given by a factor of 2
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()

        traci.vehicle.rerouteTraveltime("testVeh")
        route = traci.vehicle.getRoute("testVeh")
        routeTime = func.getRoutePathTimeVehicle("testVeh", route)

        func.penalisePathTimeVehicle("testVeh", route)
        penalisedRouteTime = func.getRoutePathTimeVehicle("testVeh", route)

        self.assertEqual(penalisedRouteTime, func.PENALISATION * routeTime)

    def test_smallManhattan_getGlobalRoutePathTime_realTime(self):
        """
        Checks the function getGlobalRoutePathTime(), when explicitly setting the realTime to True and False, that the
        correct route time is given after the route time has been altered using penalisePathTime().
        """
        func.getGlobalEdgeWeights()

        route = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1', '420908138#0',
                 '420908138#1', '464516471#9', '569345537#0', '569345537#2']

        initialTime = func.getGlobalRoutePathTime(route)
        func.penalisePathTime(route)
        # At this point the penalisation should be applied, but as we are getting the current time (not the adjusted
        # penalised time) the route time should be the same as the initial time.
        routeTimeAfterPenalisation = func.getGlobalRoutePathTime(route, True)

        self.assertEqual(routeTimeAfterPenalisation, initialTime)

    def test_smallManhattan_penalisePathTime(self):
        """
        Checks that the penalisePathTime() method penalises each of the edges belonging in a route for the entire road
        network
        """
        func.getGlobalEdgeWeights()

        route = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1', '420908138#0',
                 '420908138#1', '464516471#9', '569345537#0', '569345537#2']

        initialTime = func.getGlobalRoutePathTime(route)
        func.penalisePathTime(route)
        penalisedRouteTime = func.getGlobalRoutePathTime(route, False)

        self.assertEqual(initialTime * func.PENALISATION, penalisedRouteTime)

    def test_smallManhattan_penalisePathTime_twice(self):
        """
        Running the penalisePathTime() twice on the same route
        """
        func.getGlobalEdgeWeights()

        route = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1', '420908138#0',
                 '420908138#1', '464516471#9', '569345537#0', '569345537#2']

        initialTime = func.getGlobalRoutePathTime(route)
        func.penalisePathTime(route)
        penalisedRouteTimeOnce = func.getGlobalRoutePathTime(route, False)
        func.penalisePathTime(route)
        penalisedRouteTimeTwice = func.getGlobalRoutePathTime(route, False)

        self.assertEqual(initialTime * func.PENALISATION * func.PENALISATION, penalisedRouteTimeTwice)

    def test_smallManhattan_penalisePathTimeVehicle_reset(self):
        """
        Checks that once the penalisePathTimeVehicle() method has been ran, the edge weights are reset back to what
        they were initially
        """
        pass

    def test_smallManhattan_endSim(self):
        """
        Checks that the simulation has been successfully ended if endSim() is manually called
        """
        with self.assertRaises(SystemExit):
            for i in range(sumo.END_TIME):
                traci.simulationStep()
                if i == 20:
                    initialFunc.endSim(i)

    def test_smallManhattan_rerouteSelectedVehiclesLane_noVehiclesSelectedAsTurnOffWrong(self):
        """
        We shall assume that there are signs of congestion on lane 420908138#1_0 (edge 420908138#1), the 'testVeh' route
        contains the edge 420908138#1, however, the 'testVeh' should not be rerouted in this case as lane 420908138#1_0
        does not need to be visited by 'testVeh' as it is outgoing to an irrelevant lane (which 'testVeh' will not visit
        either).

        Pass if 'testVeh' is not included in the vehicle list which has been rerouted
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()
        traci.vehicle.rerouteTraveltime("testVeh")
        optimalRoute = traci.vehicle.getRoute("testVeh")

        # Checking that the edges we wish to test are in the optimal route
        if '420908138#1' in optimalRoute and '194920158#9' in optimalRoute:
            for i in range(sumo.END_TIME):
                traci.simulationStep()
                currentEdge = traci.lane.getEdgeID(traci.vehicle.getLaneID("testVeh"))
                # Once the vehicle has reached the desired edge break the loop
                if currentEdge == '194920158#9':
                    break

            self.assertFalse("testVeh" in func.rerouteSelectedVehiclesLane('420908138#1', '420908138#1_0'))
        else:
            raise Exception('Required edges not in optimal route.')

    def test_smallManhattan_rerouteSelectedVehiclesLane_vehicleSelectedAsIncomingToCongestion(self):
        """
        We shall assume that there are signs of congestion on lane 464516471#9_1 (edge 464516471#9). Given that the
        'testVeh' last checked optimal route does contain the edge 464516471#9 and therefore shall potentially need to
        access lane 464516471#9_1, the vehicle should be rerouted based on this.

        Pass if 'testVeh' belongs to the list of vehicle's that were rerouted from rerouteSelectedVehiclesLane
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()
        traci.vehicle.rerouteTraveltime("testVeh")
        optimalRoute = traci.vehicle.getRoute("testVeh")

        # Checking that the edges we wish to test are in the optimal route
        if '420908138#1' in optimalRoute and '464516471#9' in optimalRoute:
            for i in range(sumo.END_TIME):
                traci.simulationStep()
                # Checking if the 'testVeh' is on edge 420908138#0 (2 edges away from the congested edge)
                currentEdge = traci.lane.getEdgeID(traci.vehicle.getLaneID("testVeh"))
                # Once the vehicle has reached the desired edge break the loop
                if currentEdge == '420908138#1':
                    break

            # Check that the vehicle has been rerouted (if it's in the list it has been)
            self.assertTrue("testVeh" in func.rerouteSelectedVehiclesLane('464516471#9', '464516471#9_1'))
        else:
            raise Exception('Required edges not in optimal route.')

    def test_smallManhattan_kPaths_numberOfRoutes(self):
        """
        Assumption that k = 3

        Pass if the method kPaths() generates 3 potential routes for the specified vehicle
        """
        sumo.K_MAX = 3
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        func.getGlobalEdgeWeights()

        self.assertTrue(len(func.kPaths("testVeh")), 3)

    def test_smallManhattan_kPaths_routeAtomicity(self):
        """
        Assumption that k = 3

        Pass if the method kPaths() generates routes which are not the same as one another (they are all distinct)
        """
        sumo.K_MAX = 3
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        func.getGlobalEdgeWeights()

        kPaths = func.kPaths("testVeh")
        route1, route2, route3 = kPaths

        self.assertNotEqual(route1, route2)
        self.assertNotEqual(route1, route3)
        self.assertNotEqual(route2, route3)

    def test_smallManhattan_kPaths_routeSelection(self):
        """
        Assumption that k = 3

        Pass if the method kPaths() selects one of the generated routes and that the non-optimal solution (a solution
        which shouldn't belong in kPaths() due to it's lack of optimality) is no longer the route of the vehicle
        """
        sumo.K_MAX = 3
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        traci.simulationStep()
        func.getGlobalEdgeWeights()

        # Assigning non-optimal route
        nonOptimalRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute("testVeh", nonOptimalRoute)

        routeList = func.kPaths("testVeh")

        print(routeList)

        # Checks that the non-optimal route is not given from the k paths (as the 3 paths should have a lower estimated
        # time) and that the vehicle's current route is one of those found in the routeList (the selected route has been
        # assigned to the vehicle successfully
        self.assertTrue(nonOptimalRoute not in routeList and traci.vehicle.getRoute("testVeh") in routeList)


    def test_smallManhattan_rerouteSelectedVehiclesEdge_vehicleReroutedOnSingleOutgoingEdge(self):
        """
        We know that 'testVeh' begins on edge 46538375#5, which is the single incoming edge to edge 46538375#6. Given
        that, congestion will be assumed on edge 46538375#6 which means that 'testVeh' should be selected for rerouting
        and consequently rerouted.

        Pass if 'testVeh' route is changed from the non-optimal route which is manually assigned before rerouting occurs
        """
        testing.Testing().setupGenericCarSM()
        func.getGlobalEdgeWeights()
        # Load the vehicles into the simulation
        traci.simulationStep()
        # This is a non-optimal route to the same target edge
        nonOptimalRoute = ['46538375#5', '46538375#6', '46538375#7', '46538375#9', '46538375#10', '46538375#11',
                           '569345537#2']

        # This is the optimal route to the same target edge at the same time in which the vehicle is being rerouted
        # (this should be the same as the route after rerouteSelectedVehiclesEdge() is called as it is the same timestep
        traci.vehicle.rerouteTraveltime("testVeh")
        optimalRoute = traci.vehicle.getRoute("testVeh")
        # Setting the vehicle's path to be the non-optimal route
        traci.vehicle.setRoute("testVeh", nonOptimalRoute)

        func.rerouteSelectedVehiclesEdge("46538375#6")
        routeAfterRerouting = traci.vehicle.getRoute("testVeh")

        self.assertTrue(routeAfterRerouting != nonOptimalRoute and routeAfterRerouting == optimalRoute)

    def test_smallManhattan_kPaths_singlePathAvailable(self):
        """
        Assumption that k = 3
        There is only a single valid route to the destination, therefore kPaths() should return only a single route.
        """
        sumo.K_MAX = 3

        # Setting up vehicle
        traci.route.add("startNode", ["499172074#4"])
        traci.vehicle.addFull("testVeh", "startNode", typeID="car")
        traci.gui.trackVehicle("View #0", "testVeh")
        traci.gui.setZoom("View #0", traci.gui.getZoom() * sumo.ZOOM_FACTOR)
        traci.vehicle.changeTarget("testVeh", "499172074#9")

        traci.vehicle.rerouteTraveltime("testVeh")
        initialRoute = traci.vehicle.getRoute("testVeh")

        for i in range(4):
            traci.simulationStep()

        func.getGlobalEdgeWeights()
        routeList = func.kPaths("testVeh")

        singleRoute = []
        for route in routeList:
            singleRoute.extend(routeList)

        self.assertTrue(len(routeList) == 1)
        self.assertEqual(initialRoute, route)

    def test_smallManhattan_rerouteSelectedVehiclesEdge_noVehicles(self):
        """
        Congestion is detected
        """
        for edge in initialFunc.fringeEdges:
            with self.subTest(status_code=edge):
                self.assertTrue(sumo.net.getEdge(edge).is_fringe())

    def test_smallManhattan_multiIncomingEdges(self):
        """
        Checks that the values held in multiIncomingEdges variable matches the expected incoming edges up to
        MAX_RECURSIVE_INCOMING_EDGES (assumption that it is 3) away from the target edge
        """
        sumo.MAX_EDGE_RECURSIONS_RANGE = 3
        targetEdge = '511924978#1'
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '497165753#5', '569345508#1',
                          '5673497', '458180186#0', '497165756#2', '497165756#1'}

        initialFunc.initialisation()
        self.assertEqual(initialFunc.multiIncomingEdges[targetEdge], expectedOutput)

class NewarkTests(unittest.TestCase):
    """
    Tests ran when the scenario is 'Testing (newark)'
    """

    def setUp(self):
        """
        Ensures that the scenario is that of 'Testing (newark)'
        """
        if sumo.SCENARIO != 3:
            raise unittest.SkipTest("Scenario is {}, Newark unit tests shall not be executed.".format(sumo.SCENARIO))
        else:
            print("meep")

    def test_newark_multiIncomingRecursion_3Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 3
        """
        output = initialFunc.getMultiIncomingEdges("511924978#1")
        self.assertEqual(output, ['497165756#3', '511924978#0', '441405436', '569345515#0', '497165753#5',
                                  '569345508#1', '5673497', '458180186#0', '497165756#2', '497165756#1'])

        # if sumo.MAX_EDGE_RECURSIONS_RANGE == 3:
        #     output = func.getMultiIncomingEdges("511924978#1")
        #     self.assertEqual(output, ['497165756#3', '511924978#0', '441405436', '569345515#0', '497165753#5',
        #                               '569345508#1', '5673497', '458180186#0', '497165756#2', '497165756#1'])
        # else:
        #     raise unittest.SkipTest("The MAX_EDGE_RECURSIONS_RANGE is {}, and therefore 3 recursions shall not be "
        #                             "tested")

if __name__=="__main__":
    unittest.main(exit=False)
