###################################################################################################################
# Unit tests to ensure the functionality of the functions works as intended and returns the correct results.      #
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

if not sumo.COMPUTER:
    sys.path.insert(1, '/Users/jonathan/Documents/comp3200/sumo/tools')
    os.environ["SUMO_HOME"] = "/Users/jonathan/Documents/comp3200/sumo"

import random
import unittest
import warnings
import sumolib
import sys
import traci
from copy import deepcopy

import src.code.RoutingFunctions
from src.code import RoutingFunctions as func
from src.code import Testing as testing
from src.code import InitialMapHelperFunctions as initialFunc
from src.code import SimulationFunctions as sim
from src.code import Database as db

#############
# VARIABLES #
#############

# True when testing the database functionality
databaseTestingBool = True


class SmallSouthamptonTestsRoute(unittest.TestCase):
    """
    These test cases must change the route file in order to run the tests
    """

    def setUp(self):
        if databaseTestingBool:
            raise unittest.SkipTest("Skipping all tests, databases are being tested (databaseTestingBool = True)")
        else:
            testing.TESTING_NUMBER = 0
            sumo.SCENARIO = 0
            sumo.net = sumolib.net.readNet(sumo.NET_FILE_SM)

            # Resetting
            func.vehicleReroutedAmount = {}
            func.reroutedVehicles = set()

    def tearDown(self):
        traci.close(False)
        with self.assertRaises(SystemExit):
            initialFunc.endSim(0)
        del self.main
        # time.sleep(2)

    def test_smallManhattan_kPaths_lessThanMaxSelection(self):
        """
        Assumption that k = 3

        In this situation, the initial best path is congested with traffic, therefore, once kPaths() is called it will
        deviate away from the best path at start up (as there are no vehicle's when the simulation initially begins) to
        a more appropriate route. However, given that the next best route other than the one initially selected in
        kPaths() is >20% (KPATH_MAX_ALLOWED_TIME = 1.2) worse in terms of time taken, no further routes should be
        selected.
        """
        src.code.RoutingFunctions.K_MAX = 3
        func.KPATH_MAX_ALLOWED_TIME = 1.2
        routeFile = sumo.MAIN_PROJECT + "small_manhattan/testing/routes_sm_rerouting_test.xml"
        self.main = sumo.Main()
        self.main.run(True, True, True, routeFile, functionName=self.id())
        testing.Testing().setupGenericCarSM()

        traci.vehicle.rerouteTraveltime("testVeh")
        initialRoute = traci.vehicle.getRoute("testVeh")

        for i in range(4):
            traci.simulationStep()

        sim.getGlobalEdgeWeights()

        currentLane = traci.vehicle.getLaneID("testVeh")
        currentEdge = traci.lane.getEdgeID(currentLane)

        # Initialising cumulativeExtraTime for testVeh
        func.cumulativeExtraTime['testVeh'] = 0

        routeList = func.kPaths("testVeh", currentEdge)

        self.assertTrue(initialRoute not in routeList and len(routeList) < src.code.RoutingFunctions.K_MAX)

    def test_smallManhattan_setRouteAllVehicles(self):
        """
        Attempting to set the route of 'testVeh' in the simulation after a random number of time steps (to test
        setRoute() functionality)
        """
        self.main = sumo.Main()
        self.main.run(True, True, True, functionName=self.id())

        src.code.RoutingFunctions.K_MAX = 3
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()

        # This is the edge in which the vehicle is on after 1 timestep
        beforeLane = traci.vehicle.getLaneID("testVeh")
        beforeEdge = initialFunc.lanesNetwork[beforeLane]

        # Run simulation for 50-100 time steps
        for i in range(random.randint(50, 100)):
            traci.simulationStep()

        # The edge in which the vehicle is now occupying
        currentLane = traci.vehicle.getLaneID("testVeh")
        currentEdge = initialFunc.lanesNetwork[currentLane]

        if currentEdge == beforeEdge:
            raise Exception("Before and after edges are the same")

        # Current route
        routeOld = traci.vehicle.getRoute("testVeh")
        # As we haven't rerouted the vehicle the edge in which it is on must be in the route definition for the vehicle
        currentEdgeIndex = routeOld.index(currentEdge)
        # Take the remainder of the route starting from the current edge to the final edge (remains the same)
        alteredRoute = routeOld[currentEdgeIndex:]

        # As the current route has the beginning edge in the list as being the initial point of origin of the vehicle
        # into the network (which doesn't correspond with the current edge that the vehicle is on) there should be a
        # TraCIException being raised to inform you that the route selection is invalid
        self.assertRaises(traci.TraCIException, lambda: traci.vehicle.setRoute("testveh", routeOld))

        # This route does begin with the edge in which the vehicle is current on, therefore should be excepted
        traci.vehicle.setRoute("testVeh", alteredRoute)

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
        self.main.run(True, True, True, routeFile, functionName=self.id())
        testing.Testing().setupGenericCarSM()

        for i in range(1):
            traci.simulationStep()

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        currentRoute = traci.vehicle.getRoute("testVeh")
        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute("testVeh")

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
        self.main.run(True, True, True, routeFile, functionName=self.id())
        testing.Testing().setupGenericCarSM()

        for i in range(4):
            traci.simulationStep()

        sim.getGlobalEdgeWeights()

        for edge in func.edgeSpeedGlobal.keys():
            traci.edge.adaptTraveltime(edge, func.edgeSpeedGlobal[edge])

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        currentRoute = traci.vehicle.getRoute("testVeh")
        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute("testVeh")

        self.assertEqual(currentRoute, newRoute)


class DatabaseTests(unittest.TestCase):
    """
    Tests the functionality of the database, these tests are to be run individually.
    """

    def setUp(self):
        """
        Ensures that the scenario is that of 'Testing (small_manhattan)'
        """
        if not databaseTestingBool:
            raise unittest.SkipTest("Skipping database tests, these must be ran individually.")
        else:
            testing.TESTING_NUMBER = 0
            func.reroutedVehicles = set()  # Resetting
            sumo.SCENARIO = 0
            sumo.net = sumolib.net.readNet(sumo.NET_FILE_SM)

    def tearDown(self):
        """
        Closes the traci connection once used
        """
        with self.assertRaises(SystemExit):
            initialFunc.endSim(0)
        del self.mainMethod

    def test_smallManhattan_vehicleReroutingAmount(self):
        """
        Tests that the vehicleReroutingAmount returns the correct values after the simulation has ran
        """
        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())

        testing.Testing().setupGenericCarSM(name="999", initialise=True)
        traci.simulationStep()

        # Assigning non-optimal route (to ensure route is being switched)
        nonOptimalRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute("999", nonOptimalRoute)

        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")
        func.rerouteSelectedVehicles(nextEdge)

        # Resetting
        func.reroutedVehicles = set()

        for i in range(30):
            traci.simulationStep()

        nonOptimalRoute = ['46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('999', nonOptimalRoute)

        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")
        func.rerouteSelectedVehicles(nextEdge)

        # Resetting
        func.reroutedVehicles = set()

        # Vehicle has rerouted twice and therefore should show up as being 2
        self.assertEqual(func.vehicleReroutedAmount["999"], 2)

    def test_smallManhattan_vehicleReroutingAmount_noChange(self):
        """
        The vehicle in question already has the most optimal route, therefore, when rerouteSelectedVehicles is called on
        edge ahead of the vehicle, vehicleReroutingAmount for that vehicle shouldn't be incremented as the vehicle's
        route does not change.
        """
        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())

        # Ensuring reset of vehicleReroutedAmount
        func.vehicleReroutedAmount = {'999': 0}
        func.cumulativeExtraTime = {}

        testing.Testing().setupGenericCarSM(name="999")
        traci.simulationStep()

        # Ensuring that the vehicle has the most optimal route
        traci.vehicle.rerouteTraveltime('999')
        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")
        func.rerouteSelectedVehicles(nextEdge)

        # Vehicle shouldn't have an edited vehicleReroutedAmount
        self.assertEqual(func.vehicleReroutedAmount["999"], 0)

    def test_smallManhattan_cumulativeExtraTime(self, clearDB=True):
        """
        Tests that when kPaths is ran (and the given route is not the original route), the cumulative extra time
        registers

        Args:
            clearDB (bool): True when the database should be cleared
        """
        if clearDB:
            database = db.Database()
            database.clearDB()

        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())
        # To allow for many different routes regardless of time
        func.KPATH_MAX_ALLOWED_TIME = 500

        if clearDB:
            testing.Testing().setupGenericCarSM(name="999", target='167922073#0', initialise=True)
        else:
            testing.Testing().setupGenericCarSM(name="999", target='167922073#0')

        # This is the cumulative route time before rerouting
        routeTimeBefore = 0
        # This is the cumulative route time after rerouting with kPaths (where a check is made to ensure that the best
        # route was not selected for rerouting for testing purposes)
        routeTimeAfter = 0
        # noinspection PyBroadException
        try:
            # This tracks the number of times the vehicle has been asked to reroute (essentially takes the data taken
            # from the DB)
            reroutedAmount = func.vehicleReroutedAmount['999']
        except Exception:
            # If the test needs to be run as if nothing is in the database
            reroutedAmount = 0

        for i in range(20):
            traci.simulationStep()

        # Current position of vehicle
        actualLocation = traci.vehicle.getLaneID('999')
        edgeLoc = initialFunc.lanesNetwork[actualLocation]

        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")

        # Getting best possible path
        traci.vehicle.rerouteTraveltime("999", False)
        currentRoute = traci.vehicle.getRoute("999")
        currentEdgeIndex = currentRoute.index(edgeLoc)
        newRoute = currentRoute
        sim.getGlobalEdgeWeights()

        routeTimeBefore += sim.getGlobalRoutePathTime(currentRoute[currentEdgeIndex:])
        if clearDB:
            func.cumulativeExtraTime['999'] = 0
        extraBefore = func.cumulativeExtraTime['999']

        # Running kPaths until the new route does not match the best route
        while newRoute == currentRoute:
            func.reroutedVehicles = set()  # Resetting
            func.rerouteSelectedVehicles(nextEdge, kPathsBool=True)
            newRoute = traci.vehicle.getRoute('999')
            if newRoute == currentRoute:
                func.cumulativeExtraTime['999'] = extraBefore

        reroutedAmount += 1

        routeTimeAfter += sim.getGlobalRoutePathTime(newRoute[currentEdgeIndex:])

        for i in range(30):
            traci.simulationStep()

        # Current position of vehicle
        actualLocation = traci.vehicle.getLaneID('999')
        edgeLoc = initialFunc.lanesNetwork[actualLocation]

        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")

        # Getting best possible path
        traci.vehicle.rerouteTraveltime("999", False)
        currentRoute = traci.vehicle.getRoute("999")
        currentEdgeIndex = currentRoute.index(edgeLoc)
        newRoute = currentRoute
        sim.getGlobalEdgeWeights()

        routeTimeBefore += sim.getGlobalRoutePathTime(currentRoute[currentEdgeIndex:])
        extraBefore = func.cumulativeExtraTime['999']

        while newRoute == currentRoute:
            func.reroutedVehicles = set()  # Resetting
            func.rerouteSelectedVehicles(nextEdge, kPathsBool=True)
            newRoute = traci.vehicle.getRoute('999')
            if newRoute == currentRoute:
                func.cumulativeExtraTime['999'] = extraBefore

        reroutedAmount += 1

        routeTimeAfter += sim.getGlobalRoutePathTime(newRoute[currentEdgeIndex:])

        for i in range(999):
            traci.simulationStep()

        # Because of the checks done to ensure the vehicle wouldn't pick the best route, the time taken should ALWAYS
        # be greater than (or equal to if the reroutes effectively cancel each other out) the best possible time
        # routeTimeBefore
        self.assertGreaterEqual("{0:.6g}".format(routeTimeAfter), "{0:.6g}".format(routeTimeBefore))
        # Checking that the calculation has been done correctly
        self.assertEqual("{0:.6g}".format((routeTimeAfter - routeTimeBefore)), "{0:.6g}".format(
            func.cumulativeExtraTime['999']))
        # Checks that the number of reroutings returned is correct
        self.assertEqual(reroutedAmount, func.vehicleReroutedAmount['999'])

    def test_smallManhattan_clearingTable(self):
        """
        Checking if clearing a particular table from the database works
        """
        self.test_smallManhattan_vehicleReroutingAmount_databaseInsertion()

        database = db.Database()
        # Number of rows before deletion
        rows = len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE))
        database.clearTable(db.VEHICLE_OUTPUT_TABLE)

        self.assertEqual(len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)), 0)
        self.assertGreater(rows, 0)
        database.closeDB()

    def test_smallManhattan_clearingDatabase(self):
        """
        Checking if clearDB clears all of the tables in the database
        """
        self.test_smallManhattan_vehicleReroutingAmount_databaseInsertion()

        database = db.Database()

        database.cursor.execute('DROP TABLE IF EXISTS {}'.format("new_table"))
        database.cursor.execute('CREATE TABLE {} (first_field INTEGER PRIMARY KEY)'.format("new_table"))
        database.cursor.execute('INSERT INTO {} (first_field) VALUES (123)'.format("new_table"))
        database.conn.commit()

        # Number of rows before deletion
        rowsVeh = len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE))
        rowsNew = len(database.getDBTableContents('new_table'))
        database.clearDB()

        self.assertEqual(len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)), 0)
        self.assertEqual(len(database.getDBTableContents('new_table')), 0)

        self.assertGreater(rowsVeh, 0)
        self.assertGreater(rowsNew, 0)

        database.cursor.execute('DROP TABLE new_table')
        database.closeDB()

    def test_smallManhattan_vehicleReroutingAmount_databaseInsertionkPaths(self, clearDB=True):
        """
        Checking that the database has been correctly populated (with a vehicleID which is being newly inserted) when
        using kPaths() instead of Dynamic Shortest Path

        Args:
            clearDB (bool): True when the database should be cleared
        """
        # In this vehicle reroutes twice and runs kPaths with non-optimal paths
        self.test_smallManhattan_cumulativeExtraTime(clearDB)

        database = db.Database()
        if clearDB:
            database.clearTable(db.VEHICLE_OUTPUT_TABLE)
        database.populateDBVehicleTable()

        if clearDB:
            # Should be only a single tuple in the table
            self.assertEqual(len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)), 1)
        self.assertEqual(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)[0][2], func.cumulativeExtraTime['999'])
        self.assertEqual(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)[0][1], func.vehicleReroutedAmount['999'])

        database.closeDB()

    def test_smallManhattan_vehicleReroutingAmount_databaseInsertion(self):
        """
        Checking that the database has been correctly populated (with a vehicleID which is being newly inserted)
        """
        self.test_smallManhattan_vehicleReroutingAmount()

        database = db.Database()
        database.clearTable(db.VEHICLE_OUTPUT_TABLE)
        database.populateDBVehicleTable()

        # Should be only a single tuple in the table
        self.assertEqual(len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)), 1)
        # Should consist of the tuple (999, 2, 0, 0)
        self.assertEqual(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)[0], (999, 2, 0, 0))
        database.closeDB()

    def test_smallManhattan_vehicleReroutingAmount_databaseInsertion_endSim(self):
        """
        Ensures that when calling endSim(database=True), the database is updated
        """
        self.test_smallManhattan_vehicleReroutingAmount()

        database = db.Database()
        database.clearTable(db.VEHICLE_OUTPUT_TABLE)

        with self.assertRaises(SystemExit):
            initialFunc.endSim(0, database=True)

        # Should be only a single tuple in the table
        self.assertEqual(len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)), 1)
        # Should consist of the tuple (999, 2, 0, 0)
        self.assertEqual(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)[0], (999, 2, 0, 0))
        database.closeDB()

    def test_smallManhattan_vehicleReroutingAmount_multipleVehiclesMultipleInstance(self, clearDB=True):
        """
        Checking that multiple tuples are inserted for each vehicle when vehicles are not necessarily rerouted in the
        same SUMO instance

        Args:
            clearDB (bool): True when the database should be cleared
        """
        self.test_smallManhattan_vehicleReroutingAmount()

        func.reroutedVehicles = set()  # Resetting

        database = db.Database()
        if clearDB:
            database.clearTable(db.VEHICLE_OUTPUT_TABLE)
        database.populateDBVehicleTable()

        # self.tearDown()
        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())

        if clearDB:
            testing.Testing().setupGenericCarSM(name="9999", initialise=True)
        else:
            # Adding another vehicle
            testing.Testing().setupGenericCarSM(name="9999")

        for i in range(20):
            traci.simulationStep()

        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("9999")

        # Assigning non-optimal route (to ensure route is being switched)
        nonOptimalRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('9999', nonOptimalRoute)
        func.rerouteSelectedVehicles(nextEdge)

        database.populateDBVehicleTable()

        # Should be 2 tuples in the database (2 vehicles)
        self.assertEqual(len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)), 2)
        # Vehicle 999 should have the same results before and after the second simulation (given that they are not
        # in the simulation)
        self.assertEqual(database.fairnessMetricsIntoDictionary()[999], (2, 0, 0))
        # Vehicle 9999 had a single rerouting and wasn't present in the first simulation
        self.assertEqual(database.fairnessMetricsIntoDictionary()[9999], (1, 0, 0))
        database.closeDB()

    def test_smallManhattan_vehicleReroutingAmount_multipleVehiclesSameInstance(self, clearDB=True):
        """
        Checking that multiple tuples are inserted for each vehicle when all vehicles are present in the instance (and
        subsequently rerouted)

        Args:
            clearDB (bool): True when the database should be cleared
        """
        database = db.Database()
        if clearDB:
            database.clearTable(db.VEHICLE_OUTPUT_TABLE)

        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())

        """
        Vehicle 9999
        """
        if clearDB:
            testing.Testing().setupGenericCarSM(name="9999", initialise=True)
        else:
            # Adding another vehicle
            testing.Testing().setupGenericCarSM(name="9999")

        for i in range(70):
            traci.simulationStep()

        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("9999")

        # Assigning non-optimal route (to ensure route is being switched)
        nonOptimalRoute = ['196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('9999', nonOptimalRoute)
        func.rerouteSelectedVehicles(nextEdge)

        func.reroutedVehicles = set()  # Resetting

        """
        Vehicle 999
        """
        if clearDB:
            testing.Testing().setupGenericCarSM(name="999", routeName="start999", zoom=False, initialise=True)
        else:
            # Adding another vehicle
            testing.Testing().setupGenericCarSM(name="999", routeName="start999", zoom=False)

        for i in range(20):
            traci.simulationStep()

        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")

        nonOptimalRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('999', nonOptimalRoute)
        func.rerouteSelectedVehicles(nextEdge)

        func.reroutedVehicles = set()  # Resetting

        for i in range(30):
            traci.simulationStep()

        """
        Vehicle 999
        """

        nonOptimalRoute = ['46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('999', nonOptimalRoute)
        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")
        func.rerouteSelectedVehicles(nextEdge)

        func.reroutedVehicles = set()  # Resetting

        database.populateDBVehicleTable()

        # Should be both of the tuples in the database
        self.assertEqual(len(database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)), 2)
        # If the database has been cleared these values should be correct
        if clearDB:
            # Vehicle 999 rerouted once, 9999 rerouted twice
            self.assertEqual(database.fairnessMetricsIntoDictionary()[999], (2, 0, 0))
            self.assertEqual(database.fairnessMetricsIntoDictionary()[9999], (1, 0, 0))
        database.closeDB()

    def test_smallManhattan_vehicleReroutingAmount_updating_singleVehicle(self):
        """
        The vehicle has already been inserted into the database with 2 previous reroutings (from another simulation).
        The vehicle shall be rerouted once more (another simulation instance), the database should reflect that change
        by updating after the simulation has elapsed; this is done without the loadFairnessMetrics() method.
        """
        self.test_smallManhattan_vehicleReroutingAmount()

        func.reroutedVehicles = set()  # Resetting

        # Adding the results of the previous test to the db
        database = db.Database()
        database.clearTable(db.VEHICLE_OUTPUT_TABLE)
        database.populateDBVehicleTable()

        self.tearDown()
        self.setUp()
        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())

        testing.Testing().setupGenericCarSM(name="999")

        for i in range(35):
            traci.simulationStep()

        # Assigning non-optimal route (to ensure route is being switched)
        nonOptimalRoute = ['46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('999', nonOptimalRoute)
        # Getting edge one ahead of current position (in the vehicle's route)
        nextEdge = sim.getEdgeOneAheadVehicleRoute("999")
        func.rerouteSelectedVehicles(nextEdge)

        # Populating the DB with the new results
        database.populateDBVehicleTable()
        contents = database.getDBTableContents(db.VEHICLE_OUTPUT_TABLE)[0]

        self.assertEqual(contents, (999, 3, 0, 0))
        database.closeDB()

    def test_smallManhattan_loadFairness(self):
        """
        Tests the loadFairnessMetrics() method which is meant to collect the metrics from the previously ran
        simulation(s) and place them in their corresponding variables.
        """
        # 2 simulations have been ran with 2 vehicles (initialise to begin with)
        self.test_smallManhattan_vehicleReroutingAmount_multipleVehiclesSameInstance(True)

        func.reroutedVehicles = set()  # Resetting

        # Resetting fairness metrics to ensure no carry-over
        func.vehicleReroutedAmount.clear()
        func.cumulativeExtraTime.clear()

        # Loading the metrics from the database into their corresponding variables
        initialFunc.loadFairnessMetrics()

        self.assertEqual(func.vehicleReroutedAmount['999'], 2)
        self.assertEqual(func.vehicleReroutedAmount['9999'], 1)

        self.test_smallManhattan_vehicleReroutingAmount_multipleVehiclesSameInstance(False)

        func.reroutedVehicles = set()  # Resetting

        # At this point, vehicle 999 has been rerouted 4 times, vehicle 9999 has been rerouted twice
        self.assertEqual(func.vehicleReroutedAmount['999'], 4)
        self.assertEqual(func.vehicleReroutedAmount['9999'], 2)

        # Opening database again
        database = db.Database()

        before999 = database.fairnessMetricsIntoDictionary()[999]
        before9999 = database.fairnessMetricsIntoDictionary()[9999]

        self.assertEqual(before999, (4, 0, 0))
        self.assertEqual(before9999, (2, 0, 0))

        func.vehicleReroutedAmount.clear()
        func.cumulativeExtraTime.clear()
        initialFunc.loadFairnessMetrics()

        # Running a final simulation which should affect both the vehicleReroutedAmount and cumulativeExtraTime for
        # vehicle 999
        self.test_smallManhattan_vehicleReroutingAmount_databaseInsertionkPaths(False)

        # Opening database again
        database = db.Database()

        # Testing that the vehicleReroutedAmount is larger than that before kPaths for vehicle 999
        self.assertGreater(database.fairnessMetricsIntoDictionary()[999][0], before999[0])
        # Testing that the cumulativeExtraTime is larger than that before kPaths for vehicle 999
        self.assertGreater(database.fairnessMetricsIntoDictionary()[999][1], before999[1])
        # Testing that, given vehicle 9999 doesn't appear in the kPaths simulation, vehicle 9999 remains unchanged in
        # the database
        self.assertEqual(before9999[0], database.fairnessMetricsIntoDictionary()[9999][0])
        self.assertEqual(before9999[1], database.fairnessMetricsIntoDictionary()[9999][1])

        database.closeDB()

    def test_smallManhattan_vehiclesDepartedAndArrived(self):
        """
        Tests the vehiclesDepartedAndArrived, the totalTimeSpent should be reflective of this once the vehicle
        has left the simulation
        """
        # Resetting
        database = db.Database()

        self.test_smallManhattan_timeSpentInNetwork(True)

        # Should be correct now as the database is populated after the vehicle has left the simulation (the loop
        # continues)
        self.assertEqual(database.fairnessMetricsIntoDictionary()[999][-1], 185)
        # Checked manually
        self.assertEqual(database.fairnessMetricsIntoDictionary()[111][-1], 139)

        """ Simulating another run of the simulation without clearing DB """
        self.test_smallManhattan_timeSpentInNetwork(False)

        # Should be double
        self.assertEqual(database.fairnessMetricsIntoDictionary()[999][-1], 185 * 2)
        self.assertEqual(database.fairnessMetricsIntoDictionary()[111][-1], 139 * 2)

    def test_smallManhattan_timeSpentInNetwork(self, clearDB=True):
        """
        Tests the loadFairnessMetrics() method which is meant to collect the metrics from the previously ran
        simulation(s) and place them in their corresponding variables.

        Args:
            clearDB = True if DB should be cleared
        """
        # Resetting
        database = db.Database()
        if clearDB:
            database.clearDB()
            func.vehicleReroutedAmount.clear()
            func.cumulativeExtraTime.clear()
            initialFunc.loadFairnessMetrics()

        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())

        testing.Testing().setupGenericCarSM('999')

        for i in range(500):
            traci.simulationStep()
            sim.vehiclesDepartedAndArrived(i)

            if i == 90:
                testing.Testing().setupGenericCarSM(name="111", zoom=False, routeName="111Route")

            if i % 50 == 0 and i > 0:
                sim.updateVehicleTotalEstimatedTimeSpentInSystem(50)
                database.populateDBVehicleTable()
                if clearDB:
                    if i == 150:
                        # Vehicle takes 185 timesteps to leave the simulation (worked out manually). Because of this,
                        # it only gets into the REROUTING_PERIOD (50) check 3 times, therefore, at the moment the value
                        # should be 150
                        self.assertEqual(database.fairnessMetricsIntoDictionary()[999][-1], 150)
                        # Vehicle 111 has been in the simulation for 2 different rerouting periods (although it hasn't
                        # been in the simulation for the entire duration of both), therefore an estimate of 2 rerouting
                        # periods are added to the DB
                        self.assertEqual(database.fairnessMetricsIntoDictionary()[111][-1], 100)

    def test_smallManhattan_fairnessIndex_insertion(self, clearDB=True):
        """
        Ensuring that the simulation_output table is being correctly inserted

        Args:
            clearDB (bool): True when DB to be cleared
        """
        # Resetting
        database = db.Database()
        if clearDB:
            database.clearDB()
            func.vehicleReroutedAmount.clear()
            func.cumulativeExtraTime.clear()
            initialFunc.loadFairnessMetrics()

        self.mainMethod = sumo.Main()
        self.mainMethod.run(True, True, True, functionName=self.id())

        testing.Testing().setupGenericCarSM()
        testing.Testing().setupGenericCarSM(name="testVeh2", zoom=False, routeName="veh2Route")
        testing.Testing().setupGenericCarSM(name="testVeh3", zoom=False, routeName="veh3Route")

        # testVeh has 3x the amount of cumulativeExtraTime and vehicleReroutedAmount, but also 3x timeSpentInNetwork
        # than testVeh3. testVeh2 has 2x the fairness metrics than testVeh3
        func.cumulativeExtraTime["testVeh"] = 30
        func.cumulativeExtraTime["testVeh2"] = 97
        func.cumulativeExtraTime["testVeh3"] = 10

        func.vehicleReroutedAmount["testVeh"] = 9
        func.vehicleReroutedAmount["testVeh2"] = 43
        func.vehicleReroutedAmount["testVeh3"] = 3

        sim.timeSpentInNetwork['testVeh'] = 90
        sim.timeSpentInNetwork['testVeh2'] = 858
        sim.timeSpentInNetwork['testVeh3'] = 27

        # Adding another vehicle
        testing.Testing().setupGenericCarSM(name="testVeh4", zoom=False, routeName="veh4Route")
        func.cumulativeExtraTime["testVeh4"] = 1436
        func.vehicleReroutedAmount["testVeh4"] = 325
        sim.timeSpentInNetwork['testVeh4'] = 1256

        for i in range(100):
            traci.simulationStep()
            if i == 80:
                fairnessIndex, standardDeviation = sim.fairnessIndex()

                # Checked manually
                self.assertEqual(standardDeviation, 1.1990119747104309)
                self.assertEqual(fairnessIndex, 0.7601976050579138)

                database.populateDBSimulationTable(i, fairnessIndex, standardDeviation, "Test", 0)

                self.assertEqual(database.getDBTableContents(db.SIMULATION_OUTPUT_TABLE),
                                 [('Test80', fairnessIndex, standardDeviation, 0)])

    def test_smallManhattan_fairnessMetricsIntoDictionary(self):
        """
        Tests the fairnessMetricsIntoDictionary() method which loads the VEHICLE_OUTPUT_TABLE into a dictionary format
        with vehicleID: fairnessMetrics
        """
        database = db.Database()
        database.clearTable(db.VEHICLE_OUTPUT_TABLE)

        # Running simulation
        self.test_smallManhattan_vehicleReroutingAmount()

        database.populateDBVehicleTable()

        # Should consist of the dictionary {999: (2, 0)}
        self.assertEqual({999: (2, 0, 0)}, database.fairnessMetricsIntoDictionary())


class SmallSouthamptonTests(unittest.TestCase):
    """
    Tests ran when the scenario is 'Testing (small_manhattan)'
    """

    def setUp(self):
        """
        Ensures that the scenario is that of 'Testing (small_manhattan)'
        """
        if databaseTestingBool:
            raise unittest.SkipTest("Skipping all tests, databases are being tested (databaseTestingBool = True)")
        else:
            testing.TESTING_NUMBER = 0
            sumo.SCENARIO = 0
            sumo.net = sumolib.net.readNet(sumo.NET_FILE_SM)
            # Ensuring reset of vehicleReroutedAmount
            func.vehicleReroutedAmount = {}
            func.reroutedVehicles = set()

            self.mainMethod = sumo.Main()
            self.mainMethod.run(True, True, True, functionName=self.id())

    def tearDown(self):
        """
        Closes the traci connection once used
        """
        traci.close(False)
        with self.assertRaises(SystemExit):
            initialFunc.endSim(0)
        del self.mainMethod
        # time.sleep(2)

    def test_smallManhattan_manualTravelTimes(self):
        """
        Tests altering the current travel times and the affects on the rerouting of the vehicle when considering the
        manual travel times
        """
        testing.Testing().setupGenericCarSM()
        sim.getGlobalEdgeWeights()
        # routeFile =

        for i in range(2):
            traci.simulationStep()

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        currentRoute = traci.vehicle.getRoute("testVeh")
        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute("testVeh")

        self.assertEqual(currentRoute, newRoute)

    def test_smallManhattan_reroutedVehicles_sameVehicle(self):
        """
        Pass if vehicle is not rerouted again in the same rerouting interval given that the vehicle has already
        undergone rerouting in that rerouting period
        """
        self.test_smallManhattan_reroutedVehicles_unpopulated()

        # In the same period try and reroute 'testVeh4' (check if testVeh4 eligible for rerouting)
        vehicleList, _, _, _ = func.selectVehiclesForRerouting('46538375#6', fairness=False)

        # List should be empty as it's not being rerouted
        self.assertEqual(vehicleList, [])

    def test_smallManhattan_reroutedVehicles_noRouteChange(self):
        """
        When the vehicle is attempted to be rerouted, the route doesn't change after rerouting, therefore the vehicle
        shouldn't be added to the reroutedVehicles set and should be able to undergo further rerouting
        """
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()

        # Ensuring testVeh has the most optimal route
        traci.vehicle.rerouteTraveltime("testVeh")
        reroutedList = func.rerouteSelectedVehicles('46538375#6', fairness=False)

        # List should be empty as it's not being rerouted
        self.assertEqual(reroutedList, set())
        self.assertFalse('testVeh' in func.reroutedVehicles)

    def test_smallManhattan_reroutedVehicles_reset(self):
        """
        Pass if, when another rerouting interval happens, the reroutedList is empty and vehicles rerouted in the
        previous rerouting period can be rerouted again
        """
        self.test_smallManhattan_reroutedVehicles_unpopulated()

        # For testing purposes the rerouting period is set as 50
        func.REROUTING_PERIOD = 50

        for i in range(sumo.END_TIME):
            traci.simulationStep()
            # New rerouting period
            if i % func.REROUTING_PERIOD == 0 and i >= 1:
                # Reset the reroutedVehicles set
                func.reroutedVehicles = set()

                # Getting edge one ahead of current position (in the vehicle's route)
                nextEdge = sim.getEdgeOneAheadVehicleRoute("testVeh4")
                vehicleList, _, _, vehiclesFastRouted = func.selectVehiclesForRerouting(nextEdge, fairness=False)
                break

        # testVeh4 should be eligible for rerouting again given that it is a new rerouting period
        self.assertEqual(vehicleList, ['testVeh4'])
        self.assertEqual(vehiclesFastRouted, [])

    def test_smallManhattan_reroutedVehicles_unpopulated(self):
        """
        The reroutedVehicles set holds the vehicle ID's of the vehicle's which have been rerouted during that rerouting
        period so that they are not rerouted again during the same rerouting period (prevents multiple rerouting of the
        same vehicles).

        Pass if the reroutedVehicles set is populated with the vehicles which are eligible for rerouting and
        subsequently rerouting them as their routes are set sub-optimally.
        Note: Although there are simulation steps in between, this should be treated as if a single rerouting period
        """
        src.code.RoutingFunctions.K_MAX = 3
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(initialise=True)
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh2", zoom=False, routeName="veh2Route", initialise=True)
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh3", zoom=False, routeName="veh3Route", initialise=True)

        for i in range(10):
            traci.simulationStep()

        sim.getGlobalEdgeWeights()
        traci.simulationStep()

        # Assigning non-optimal route (to ensure route is being switched)
        nonOptimalRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('testVeh', nonOptimalRoute)
        traci.vehicle.setRoute('testVeh2', nonOptimalRoute)
        traci.vehicle.setRoute('testVeh3', nonOptimalRoute)
        # Selects which vehicles shall be eligible for rerouting
        vehiclesList, _, _, _ = func.selectVehiclesForRerouting('46538375#6', fairness=False)
        # Reroutes the vehicles, should reroute all vehicles as fairness is not considered
        func.rerouteSelectedVehicles('46538375#6', kPathsBool=False, fairness=False)

        # Checks that the returned vehiclesList is the same as on the reroutedVehicles (should be as all vehicles
        # rerouted)
        self.assertEqual(sorted(vehiclesList), sorted(list(func.reroutedVehicles)))

        for i in range(50):
            traci.simulationStep()

        # Next vehicle
        testing.Testing().setupGenericCarSM(name="testVeh4", zoom=False, routeName="veh4Route", initialise=True)
        for i in range(10):
            traci.simulationStep()

        traci.vehicle.setRoute('testVeh4', nonOptimalRoute)
        nextVehicleList, _, _, _ = func.selectVehiclesForRerouting('46538375#6', fairness=False)
        func.rerouteSelectedVehicles('46538375#6', kPathsBool=False, fairness=False)
        self.assertEqual(nextVehicleList, ['testVeh4'])
        # Adding the 2 vehicle lists which have been rerouted
        vehiclesList.extend(nextVehicleList)
        self.assertEqual(sorted(vehiclesList), sorted(list(func.reroutedVehicles)))

    def test_smallManhattan_multiIncomingRecursion_4Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 2
        """
        src.code.RoutingFunctions.MAX_EDGE_RECURSIONS_RANGE = 4
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
        src.code.RoutingFunctions.MAX_EDGE_RECURSIONS_RANGE = 3
        output = initialFunc.getMultiIncomingEdges("511924978#1")
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '497165753#5', '569345508#1',
                          '5673497', '458180186#0', '497165756#2', '497165756#1'}
        self.assertEqual(set(output), expectedOutput)

    def test_smallManhattan_multiIncomingRecursion_2Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 2
        """
        src.code.RoutingFunctions.MAX_EDGE_RECURSIONS_RANGE = 2
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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                # Running with a subtest to identify point of failure (if any)
                with self.subTest(status_code=edge):
                    self.assertEqual(len(sumo.net.getEdge(edge).getOutgoing()), 1)

    def test_smallManhattan_reroutingLanes(self):
        """
        True if all the lanes contained within reroutingLanes have at least 2 outgoing lanes
        """
        for lane in initialFunc.reroutingLanes:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                with self.subTest(status_code=lane):
                    edge = traci.lane.getEdgeID(lane)
                    self.assertGreaterEqual(len(sumo.net.getEdge(edge).getOutgoing()), 2)

    def test_smallManhattan_fringeEdges(self):
        """
        True if all edges held within fringeEdges are fringe edges (edges on the fringe of the network - no incoming
        edges) in the traffic network
        """
        for edge in initialFunc.fringeEdges:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
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
        sim.getGlobalEdgeWeights()

        # Run some simulation steps so to make sure the simulation has had time to change the estimated travel times
        # away from the initial global
        for i in range(19):
            traci.simulationStep()

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=True)
        estimatedRouteTimeTrue = sim.getRoutePathTimeVehicle("testVeh")
        routeCurrentTrue = traci.vehicle.getRoute("testVeh")

        traci.vehicle.rerouteTraveltime("testVeh", currentTravelTimes=False)
        estimatedRouteTimeFalse = sim.getRoutePathTimeVehicle("testVeh")
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
                sim.getGlobalEdgeWeights()
                # Using deepcopy as an alternative to call-by-value
                edgeSpeed1 = deepcopy(func.edgeSpeedGlobal)
            # By this time vehicle has finished route and has left the simulation
            if i == 500:
                sim.getGlobalEdgeWeights()
                edgeSpeed2 = deepcopy(func.edgeSpeedGlobal)

        self.assertNotEqual(edgeSpeed1, edgeSpeed2)

    def test_smallManhattan_getRoutePathTime_noRouteArgument(self):
        """
        Checks whether or not the estimated time returned upon calling getRoutePathTimeVehicle(), leaving the 'route'
        argument as being default (null), returns the correct result based on the current traffic conditions
        """
        testing.Testing().setupGenericCarSM()
        sim.getGlobalEdgeWeights()

        totalPathTime = 0
        for edge in traci.vehicle.getRoute("testVeh"):
            # This returns the estimated travel time for this edge
            totalPathTime += traci.edge.getTraveltime(edge)

        self.assertEqual(totalPathTime, sim.getRoutePathTimeVehicle("testVeh"))

    def test_smallManhattan_getRoutePathTime_routeArgument(self):
        """
        Checks whether or not the estimated time returned upon calling getRoutePathTimeVehicle() returns the correct
        result based on the current traffic conditions given that a route argument is given which doesn't correspond to
        the vehicle's current route
        """
        testing.Testing().setupGenericCarSM()
        sim.getGlobalEdgeWeights()

        # This route isn't the same as the current vehicle's route
        testingVehicleRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '196116976#11', '196116976#12']

        totalPathTime = 0
        for edge in testingVehicleRoute:
            # This returns the estimated travel time for this edge
            totalPathTime += traci.edge.getTraveltime(edge)

        self.assertEqual(totalPathTime, sim.getRoutePathTimeVehicle("testVeh", testingVehicleRoute))

    def test_smallManhattan_fringe_edges(self):
        """
        True if all edges held within fringeEdges are fringe edges (edges on the fringe of the network - no incoming
        edges) in the traffic network
        """
        for edge in initialFunc.fringeEdges:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", ResourceWarning)
                with self.subTest(status_code=edge):
                    self.assertTrue(sumo.net.getEdge(edge).is_fringe())

    def test_smallManhattan_penalisePathTimeVehicle_routeTime(self):
        """
        Checks that the penalisePathTimeVehicle() method penalises the path given by a factor of 2
        """
        testing.Testing().setupGenericCarSM()
        sim.getGlobalEdgeWeights()

        traci.vehicle.rerouteTraveltime("testVeh")
        route = traci.vehicle.getRoute("testVeh")
        routeTime = sim.getRoutePathTimeVehicle("testVeh", route)

        # Initialising adjusted edges which stores the values of the edge and it's adjusted travel time for each vehicle
        adjustedEdges = {}
        for edge in route:
            adjustedEdges[edge] = func.edgeSpeedGlobal[edge]

        func.penalisePathTimeVehicle("testVeh", route, adjustedEdges)
        penalisedRouteTime = sim.getRoutePathTimeVehicle("testVeh", route)

        self.assertEqual(penalisedRouteTime, func.PENALISATION * routeTime)

    def test_smallManhattan_penalisePathTimeVehicle_routeTime_global(self):
        """
        When penalised, the travel time for the individual vehicle should be affected and the global travel times (along
        with other travel vehicle's internal travel times) should remain unaffected by this change.

        Pass if penalising the travel time only affects the individual vehicle and not the whole network
        """
        testing.Testing().setupGenericCarSM()

        # Adding vehicle and associated route
        traci.route.add("startNode2", ["226041028"])
        traci.vehicle.addFull("testVeh2", "startNode2", typeID="car")
        traci.vehicle.changeTarget("testVeh2", "5671629#0")

        traci.simulationStep()
        sim.getGlobalEdgeWeights()

        testVehRoute = traci.vehicle.getRoute("testVeh")
        testVehRouteTimeBefore = sim.getRoutePathTimeVehicle("testVeh", testVehRoute)
        testVeh2Route = traci.vehicle.getRoute("testVeh2")
        testVeh2RouteTime = sim.getRoutePathTimeVehicle("testVeh2", testVeh2Route)

        # Initialising adjusted edges which stores the values of the edge and it's adjusted travel time for each vehicle
        adjustedEdges = {}
        for edge in testVehRoute:
            adjustedEdges[edge] = func.edgeSpeedGlobal[edge]

        func.penalisePathTimeVehicle("testVeh", testVehRoute, adjustedEdges)
        penalisedRouteTime = sim.getRoutePathTimeVehicle("testVeh", testVehRoute)
        # Should remain unchanged as not penalised
        testVeh2RouteTimeAfter = sim.getRoutePathTimeVehicle("testVeh2", testVeh2Route)

        # Ensuring that penalisation has worked
        self.assertFalse(penalisedRouteTime == testVehRouteTimeBefore)
        # Ensuring that, given the path time has not been penalised for testVeh2, the internal route times are unchanged
        self.assertTrue(testVeh2RouteTime == testVeh2RouteTimeAfter)
        # Ensuring that the global route times have been left unchanged after a vehicle's route has been penalised
        self.assertTrue(testVeh2RouteTimeAfter == sim.getGlobalRoutePathTime(testVeh2Route))

    def test_smallManhattan_getGlobalRoutePathTime_realTime(self):
        """
        Checks the function getGlobalRoutePathTime(), when explicitly setting the realTime to True and False, that the
        correct route time is given after the route time has been altered using penalisePathTime().
        """
        sim.getGlobalEdgeWeights()

        route = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1', '420908138#0',
                 '420908138#1', '464516471#9', '569345537#0', '569345537#2']

        adjustedEdges = {}
        for edge in route:
            adjustedEdges[edge] = func.edgeSpeedGlobal[edge]

        initialTime = sim.getGlobalRoutePathTime(route)
        func.penalisePathTime(route)
        # At this point the penalisation should be applied, but as we are getting the current time (not the adjusted
        # penalised time) the route time should be the same as the initial time.
        routeTimeAfterPenalisation = sim.getGlobalRoutePathTime(route, True)

        self.assertEqual(routeTimeAfterPenalisation, initialTime)

    def test_smallManhattan_penalisePathTime(self):
        """
        Checks that the penalisePathTime() method penalises each of the edges belonging in a route for the entire road
        network
        """
        sim.getGlobalEdgeWeights()

        route = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1', '420908138#0',
                 '420908138#1', '464516471#9', '569345537#0', '569345537#2']

        initialTime = sim.getGlobalRoutePathTime(route)
        func.penalisePathTime(route)
        penalisedRouteTime = sim.getGlobalRoutePathTime(route, False)

        self.assertEqual(initialTime * func.PENALISATION, penalisedRouteTime)

    def test_smallManhattan_penalisePathTime_twice(self):
        """
        Running the penalisePathTime() twice on the same route
        """
        sim.getGlobalEdgeWeights()

        route = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1', '420908138#0',
                 '420908138#1', '464516471#9', '569345537#0', '569345537#2']

        initialTime = sim.getGlobalRoutePathTime(route)
        func.penalisePathTime(route)
        penalisedRouteTimeOnce = sim.getGlobalRoutePathTime(route, False)
        func.penalisePathTime(route)
        penalisedRouteTimeTwice = sim.getGlobalRoutePathTime(route, False)

        self.assertEqual(initialTime * func.PENALISATION * func.PENALISATION, penalisedRouteTimeTwice)

    def test_smallManhattan_penalisePathTimeVehicle_reset(self):
        """
        Checks that once the penalisePathTimeVehicle() method has been ran, the edge weights are reset back to what
        they were initially
        """
        sim.getGlobalEdgeWeights()

        testing.Testing().setupGenericCarSM(initialise=True)
        route = traci.vehicle.getRoute('testVeh')
        # This is the global time for the route, this shouldn't be affected by penalising the route time for a vehicle
        globalTime = sim.getGlobalRoutePathTime(route)

        func.penalisePathTimeVehicle('testVeh', route, {})
        # Getting the route time taken for 'testVeh' after penalisation
        penalisedTime = 0
        for edge in traci.vehicle.getRoute('testVeh'):
            penalisedTime += traci.vehicle.getAdaptedTraveltime('testVeh', edgeID=edge, time=sim.getCurrentTimestep())

        # Resetting route time for that vehicle
        func.resetVehicleAdaptedTravelTime('testVeh', route)
        resetTime = 0
        for edge in traci.vehicle.getRoute('testVeh'):
            resetTime += traci.vehicle.getAdaptedTraveltime('testVeh', edgeID=edge, time=sim.getCurrentTimestep())

        self.assertEqual(resetTime, globalTime)
        self.assertEqual(resetTime * func.PENALISATION, penalisedTime)

    def test_smallManhattan_penalisePathTimeVehicle_twiceWithAdjustedEdge(self):
        """
        Checks that the penalisation occurs correctly given that the vehicle has an 'adjustedEdge' variable (which
        tracks the adjusted travel times for that vehicle in the format {edge: time}
        """
        sim.getGlobalEdgeWeights()

        testing.Testing().setupGenericCarSM(initialise=True)
        route = traci.vehicle.getRoute('testVeh')
        # This is the global time for the route, this shouldn't be affected by penalising the route time for a vehicle
        globalTime = sim.getGlobalRoutePathTime(route)

        adjustedEdge = {}
        for edge in route:
            adjustedEdge[edge] = func.edgeSpeedGlobal[edge]

        func.penalisePathTimeVehicle('testVeh', route, adjustedEdge)

        ##################
        # PENALISATION 2 #
        ##################

        func.penalisePathTimeVehicle('testVeh', route, adjustedEdge)
        penalisedTime = 0
        # Getting the route time taken for 'testVeh' after penalisation
        for edge in traci.vehicle.getRoute('testVeh'):
            penalisedTime += traci.vehicle.getAdaptedTraveltime('testVeh', edgeID=edge, time=sim.getCurrentTimestep())

        self.assertEqual(globalTime * func.PENALISATION * func.PENALISATION, penalisedTime)

    def test_smallManhattan_penalisePathTimeVehicle_twiceWithoutAdjustedEdge(self):
        """
        Checks that the penalisation occurs correctly without an adjustedEdge variable
        """
        sim.getGlobalEdgeWeights()

        testing.Testing().setupGenericCarSM(initialise=True)
        route = traci.vehicle.getRoute('testVeh')
        # This is the global time for the route, this shouldn't be affected by penalising the route time for a vehicle
        globalTime = sim.getGlobalRoutePathTime(route)

        func.penalisePathTimeVehicle('testVeh', route, {})

        ##################
        # PENALISATION 2 #
        ##################

        func.penalisePathTimeVehicle('testVeh', route, {})
        penalisedTime = 0
        # Getting the route time taken for 'testVeh' after penalisation
        for edge in traci.vehicle.getRoute('testVeh'):
            penalisedTime += traci.vehicle.getAdaptedTraveltime('testVeh', edgeID=edge, time=sim.getCurrentTimestep())

        self.assertEqual(globalTime * func.PENALISATION * func.PENALISATION, penalisedTime)

    def test_smallManhattan_endSim(self):
        """
        Checks that the simulation has been successfully ended if endSim() is manually called

        :return: True if SystemExit is raised when endSim() is called
        """
        with self.assertRaises(SystemExit):
            for i in range(sumo.END_TIME):
                traci.simulationStep()
                if i == 20:
                    initialFunc.endSim(i)

    def test_smallManhattan_rerouteSelectedVehicles_lane_noVehiclesSelectedAsTurnOffWrong(self):
        """
        We shall assume that there are signs of congestion on lane 420908138#1_0 (edge 420908138#1), the 'testVeh' route
        contains the edge 420908138#1, however, the 'testVeh' should not be rerouted in this case as lane 420908138#1_0
        does not need to be visited by 'testVeh' as it is outgoing to an irrelevant lane which testVeh doesn't need to
        visit either. Essentially, despite the edge belonging in the congested lane technically being in the definition
        of testVeh's route, it shall not be rerouted as it is not directly impacted by the congestion caused on that
        lane (it must take another lane on the edge instead).

        Pass if 'testVeh' is not included in the vehicle list which has been rerouted
        """
        testing.Testing().setupGenericCarSM()
        sim.getGlobalEdgeWeights()
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

            # This is selecting vehicles with the generalised edge. This SHOULD select the vehicle as the vehicle will
            # be coming onto the edge in it's route
            reroutingEdge, _, _, _ = func.selectVehiclesForRerouting('420908138#1')
            self.assertTrue("testVeh" in reroutingEdge)

            # This is selecting the vehicle with a SPECIFIC lane, the vehicle shall pass through the edge but DOESN'T
            # need to pass through this specific lane to get to it's destination, therefore the vehicle should not be
            # selected
            reroutingLane, _, _, _ = func.selectVehiclesForRerouting('420908138#1_0')
            self.assertFalse('testVeh' in reroutingLane)
        else:
            raise Exception('Required edges not in optimal route.')

    def test_smallManhattan_rerouteSelectedVehicles_lane_vehicleSelectedAsIncomingToCongestion(self):
        """
        We shall assume that there are signs of congestion on lane 196116976#7_0 (edge 196116976#7), given that
        testVeh shall pass through edge 46538375#6 leading to edge 196116976#7, this congestion should be experienced
        by the vehicle and therefore should be rerouted

        Pass if 'testVeh' belongs to the list of vehicle's that were rerouted from rerouteSelectedVehicles
        """
        testing.Testing().setupGenericCarSM(initialise=True)

        for i in range(sumo.END_TIME):
            traci.simulationStep()
            # Checking if the 'testVeh' is on edge 420908138#0 (2 edges away from the congested edge)
            currentEdge = traci.lane.getEdgeID(traci.vehicle.getLaneID("testVeh"))
            # Once the vehicle has reached the desired edge break the loop
            if currentEdge == '46538375#6':
                break

        # Assigning non-optimal route (to ensure route is being switched)
        nonOptimalRoute = ['46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute('testVeh', nonOptimalRoute)

        sim.getGlobalEdgeWeights()
        rerouted = func.rerouteSelectedVehicles('196116976#7_0')
        # Check that the vehicle has been rerouted (if it's in the list it has been)
        self.assertEqual({'testVeh'}, rerouted)

    def test_smallManhattan_updateVehicleTotalEstimatedTimeSpentInSystem(self):
        """
        This checks the method updateVehicleTotalEstimatedTimeSpentInSystem and ensures that the global variables
        stoppedStateLastPeriod and timeSpentInNetwork are updated accordingly depending on the status of the vehicles in
        the simulation
        """
        database = db.Database()
        database.clearDB()

        func.vehicleReroutedAmount = {}
        func.cumulativeExtraTime = {}
        sim.timeSpentInNetwork = {}
        sim.timeSpentStopped = {}

        testing.Testing().setupGenericCarSM(name='1', initialise=True)
        testing.Testing().setupGenericCarSM(name='2', routeName='2Route', initialise=True, zoom=False)

        func.REROUTING_PERIOD = 50

        for i in range(500):
            if i % func.REROUTING_PERIOD == 0:
                if i == 50:
                    sim.updateVehicleTotalEstimatedTimeSpentInSystem()

                    self.assertEqual(sim.timeSpentStopped, {'1': 0, '2': 0})
                    self.assertEqual(sim.timeSpentInNetwork, {'1': 50, '2': 50})

                if i == 100:
                    sim.updateVehicleTotalEstimatedTimeSpentInSystem()

                    self.assertEqual(sim.timeSpentStopped, {'1': 0, '2': 0})
                    self.assertEqual(sim.timeSpentInNetwork, {'1': 100, '2': 100})

                if i == 150:
                    sim.updateVehicleTotalEstimatedTimeSpentInSystem()

                    self.assertEqual(sim.timeSpentStopped, {'1': 0, '2': 0})
                    self.assertEqual(sim.timeSpentInNetwork, {'1': 150, '2': 150})

                if i == 200:
                    sim.updateVehicleTotalEstimatedTimeSpentInSystem()

                    self.assertEqual(sim.timeSpentStopped, {'1': 0, '2': 0})
                    # Vehicle should've stopped at this point (however the system can't be sure that it's not a brief
                    # stop so the counter continues) and vehicle 2 should've made it to it's destination
                    self.assertEqual(sim.timeSpentInNetwork, {'1': 200, '2': 183})

                if i == 250:
                    sim.updateVehicleTotalEstimatedTimeSpentInSystem()

                    # At this point vehicle has stopped for 2 rerouting periods and will now start to increment the
                    # timeSpentStopped
                    self.assertEqual(sim.timeSpentStopped, {'1': 50, '2': 0})
                    self.assertEqual(sim.timeSpentInNetwork, {'1': 200, '2': 183})

                if i == 300:
                    sim.updateVehicleTotalEstimatedTimeSpentInSystem()

                    self.assertEqual(sim.timeSpentStopped, {'1': 100, '2': 0})
                    self.assertEqual(sim.timeSpentInNetwork, {'1': 200, '2': 183})

                if i == 350:
                    # Vehicle starts moving
                    sim.updateVehicleTotalEstimatedTimeSpentInSystem()

                    self.assertEqual(sim.timeSpentStopped, {'1': 100, '2': 0})
                    self.assertEqual(sim.timeSpentInNetwork, {'1': 250, '2': 183})

                if i == 400:
                    # Now that vehicle has left the network the approximate time should be calculated, it should be
                    # below 300
                    self.assertTrue(sim.timeSpentInNetwork['1'] < 300)

            if i == 120:
                # Vehicle stops before it's destination
                traci.vehicle.setStop('1', '569345537#0')


            if i == 310:
                traci.vehicle.resume('1')

            # print(i)
            # try:
            #     print(traci.vehicle.isStopped('1'))
            #     print(traci.vehicle.getStopState('1'))
            # except Exception as e:
            #     print("fini")
            # print()

            traci.simulationStep()

            sim.vehiclesDepartedAndArrived(i)

    def test_smallManhattan_rerouteSelectedVehicles_lane_callingkPaths(self):
        """
        Assumption that k = 3

        Vehicles are re-routed using kPaths algorithm directly called from the rerouteSelectedVehicles() method
        """
        src.code.RoutingFunctions.K_MAX = 3
        testing.Testing().setupGenericCarSM(initialise=True)
        sim.getGlobalEdgeWeights()
        traci.simulationStep()

        currentPath = traci.vehicle.getRoute("testVeh")

        # There should be an additional 2 routes other than the currentPath, therefore loop until one of these is
        # selected
        while currentPath == traci.vehicle.getRoute("testVeh"):
            # Resetting reroutedVehicles so that 'testVeh' can be rerouted again if need be
            func.reroutedVehicles = set()
            vehicleList = func.rerouteSelectedVehicles('46538375#6_0', kPathsBool=True)

        self.assertTrue("testVeh" in vehicleList and currentPath != traci.vehicle.getRoute("testVeh"))

    def test_smallManhattan_selectVehiclesBasedOnFairness_correctVehiclesReturned(self):
        """
        Tests the selectVehiclesBasedOnFairness method by passing in values where the values can be manually calculated
        and compared to the outcome of the function
        """
        src.code.RoutingFunctions.K_MAX = 3

        traci.simulationStep()
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh2", zoom=False, routeName="veh2Route")
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh3", zoom=False, routeName="veh3Route")

        for i in range(65):
            traci.simulationStep()

        sim.getGlobalEdgeWeights()
        traci.simulationStep()

        """ In this example testVeh3 has suffered the most, having 1 second of time spent for every 
        rerouting/cumulativeExtraTime. testVeh3 has experienced the most fairness having 3 seconds for every 
        rerouting/cumulative. testVeh2 is in the middle with 2 seconds."""

        func.cumulativeExtraTime["testVeh"] = 200
        func.cumulativeExtraTime["testVeh2"] = 600
        func.cumulativeExtraTime["testVeh3"] = 1

        func.vehicleReroutedAmount["testVeh"] = 200
        func.vehicleReroutedAmount["testVeh2"] = 600
        func.vehicleReroutedAmount["testVeh3"] = 1

        sim.timeSpentInNetwork['testVeh'] = 600
        sim.timeSpentInNetwork['testVeh2'] = 1200
        sim.timeSpentInNetwork['testVeh3'] = 1

        # Selecting vehicles based on fairness
        selectedVehicles, qoe, _, _ = sim.selectVehiclesBasedOnFairness(['testVeh', 'testVeh2', 'testVeh3'])
        self.assertEqual(selectedVehicles, ['testVeh', 'testVeh2'])

        # Calculated manually
        self.assertAlmostEqual(qoe.get('testVeh'), 10)
        self.assertEqual(qoe.get('testVeh2'), 7.5)
        self.assertEqual(qoe.get('testVeh3'), 0)
        # Select vehicles testVeh and testVeh2


        """ In this case cumulativeExtraTime is not necessarily proportional to timeSpentInNetwork and 
        vehicleReroutingAmount, testVeh3 has suffered by far the worst in terms of this. However, the other vehicles 
        still have many more vehicleReroutedAmount's than testVeh3 """

        func.cumulativeExtraTime["testVeh"] = 200
        func.cumulativeExtraTime["testVeh2"] = 600
        func.cumulativeExtraTime["testVeh3"] = 100

        func.vehicleReroutedAmount["testVeh"] = 200
        func.vehicleReroutedAmount["testVeh2"] = 600
        func.vehicleReroutedAmount["testVeh3"] = 1

        sim.timeSpentInNetwork['testVeh'] = 600
        sim.timeSpentInNetwork['testVeh2'] = 1200
        sim.timeSpentInNetwork['testVeh3'] = 1

        # Selecting vehicles based on fairness
        selectedVehicles, qoe, _, _ = sim.selectVehiclesBasedOnFairness(['testVeh', 'testVeh2', 'testVeh3'])
        self.assertEqual(selectedVehicles, ['testVeh', 'testVeh2'])

        # Calculated manually
        self.assertEqual(qoe.get('testVeh'), 10)
        self.assertAlmostEqual(round(qoe.get('testVeh2'), 4), 9.9586)
        self.assertEqual(qoe.get('testVeh3'), 0)

        """ These are just random values, QOE calculated manually to ensure correct calculation """

        func.cumulativeExtraTime["testVeh"] = 5254
        func.cumulativeExtraTime["testVeh2"] = 2103
        func.cumulativeExtraTime["testVeh3"] = 64

        func.vehicleReroutedAmount["testVeh"] = 459
        func.vehicleReroutedAmount["testVeh2"] = 296
        func.vehicleReroutedAmount["testVeh3"] = 9

        sim.timeSpentInNetwork['testVeh'] = 10532
        sim.timeSpentInNetwork['testVeh2'] = 4351
        sim.timeSpentInNetwork['testVeh3'] = 125

        # Selecting vehicles based on fairness
        selectedVehicles, qoe, _, _ = sim.selectVehiclesBasedOnFairness(['testVeh', 'testVeh2', 'testVeh3'])

        self.assertEqual(qoe.get('testVeh'), 10)
        self.assertAlmostEqual(round(qoe.get('testVeh2'), 4), 1.9322)
        self.assertEqual(qoe.get('testVeh3'), 0)

        self.assertEqual(selectedVehicles, ['testVeh'])

    def test_smallManhattan_selectVehiclesBasedOnFairness_allNewVehicles(self):
        """
        This is the case in which all 3 vehicles are new to the simulation and do not have any fairness values
        associated
        """
        src.code.RoutingFunctions.K_MAX = 3

        # The initialise=True marker ensures that all vehicles start with all fairness metrics = 0
        testing.Testing().setupGenericCarSM(initialise=True)
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh2", zoom=False, routeName="veh2Route", initialise=True)
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh3", zoom=False, routeName="veh3Route", initialise=True)

        for i in range(65):
            traci.simulationStep()

        # Selecting vehicles based on fairness
        selectedVehicles, _, _, _ = sim.selectVehiclesBasedOnFairness(['testVeh', 'testVeh2', 'testVeh3'])
        # All 3 should be selected as they all have the same fairness
        self.assertEqual(selectedVehicles, ['testVeh', 'testVeh2', 'testVeh3'])

    def test_smallManhattan_selectVehiclesBasedOnFairness_normalisedTime(self):
        """
        In this case, the vehicles have been in the simulation before and have a timeSpentInNetwork value > 0
        """
        src.code.RoutingFunctions.K_MAX = 3

        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh2", zoom=False, routeName="veh2Route")
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh3", zoom=False, routeName="veh3Route")

        # testVeh has 3x the amount of cumulativeExtraTime and vehicleReroutedAmount, but also 3x timeSpentInNetwork
        # than testVeh3. testVeh2 has 2x the fairness metrics than testVeh3
        func.cumulativeExtraTime["testVeh"] = 30
        func.cumulativeExtraTime["testVeh2"] = 20
        func.cumulativeExtraTime["testVeh3"] = 10

        func.vehicleReroutedAmount["testVeh"] = 9
        func.vehicleReroutedAmount["testVeh2"] = 6
        func.vehicleReroutedAmount["testVeh3"] = 3

        sim.timeSpentInNetwork['testVeh'] = 81
        sim.timeSpentInNetwork['testVeh2'] = 54
        sim.timeSpentInNetwork['testVeh3'] = 27

        traci.simulationStep()

        # Selecting vehicles based on fairness
        selectedVehicles, qoe, _, _ = sim.selectVehiclesBasedOnFairness(['testVeh', 'testVeh2', 'testVeh3'])

        # All 3 vehicles should be eligible for rerouting
        self.assertEqual(selectedVehicles, ['testVeh', 'testVeh2', 'testVeh3'])

        # Values should all have the same QOE (e.g. 3x the amount of time spent for 3x the amount of reroutings/extra
        # time)
        self.assertTrue(qoe.get('testVeh') == qoe.get('testVeh2') == qoe.get('testVeh3'))

        # Values should all be 10
        self.assertEqual(qoe.get('testVeh'), 10)
        self.assertEqual(qoe.get('testVeh2'), 10)
        self.assertEqual(qoe.get('testVeh3'), 10)

    def test_smallManhattan_fairnessIndex(self):
        """
        In this case, the vehicles have been in the simulation before and have a timeSpentInNetwork value > 0
        """
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh2", zoom=False, routeName="veh2Route")
        traci.simulationStep()
        testing.Testing().setupGenericCarSM(name="testVeh3", zoom=False, routeName="veh3Route")

        # testVeh has 3x the amount of cumulativeExtraTime and vehicleReroutedAmount, but also 3x timeSpentInNetwork
        # than testVeh3. testVeh2 has 2x the fairness metrics than testVeh3
        func.cumulativeExtraTime["testVeh"] = 30
        func.cumulativeExtraTime["testVeh2"] = 97
        func.cumulativeExtraTime["testVeh3"] = 10

        func.vehicleReroutedAmount["testVeh"] = 9
        func.vehicleReroutedAmount["testVeh2"] = 43
        func.vehicleReroutedAmount["testVeh3"] = 3

        sim.timeSpentInNetwork['testVeh'] = 90
        sim.timeSpentInNetwork['testVeh2'] = 858
        sim.timeSpentInNetwork['testVeh3'] = 27

        for i in range(50):
            traci.simulationStep()

        # Adding another vehicle
        testing.Testing().setupGenericCarSM(name="testVeh4", zoom=False, routeName="veh4Route")
        func.cumulativeExtraTime["testVeh4"] = 1436
        func.vehicleReroutedAmount["testVeh4"] = 325
        sim.timeSpentInNetwork['testVeh4'] = 1256

        traci.simulationStep()

        fairnessIndex, standardDeviation = sim.fairnessIndex()

        # Checked manually
        self.assertEqual(standardDeviation, 1.1990119747104309)
        self.assertEqual(fairnessIndex, 0.7601976050579138)

    def test_smallManhattan_kPaths_numberOfRoutes(self):
        """
        Assumption that k = 3

        Pass if the method kPaths() generates 3 potential routes for the specified vehicle
        """
        src.code.RoutingFunctions.K_MAX = 3
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        sim.getGlobalEdgeWeights()

        currentLane = traci.vehicle.getLaneID("testVeh")
        currentEdge = traci.lane.getEdgeID(currentLane)

        # Initialising cumulativeExtraTime for testVeh
        func.cumulativeExtraTime['testVeh'] = 0

        self.assertTrue(len(func.kPaths("testVeh", currentEdge)), 3)

    def test_smallManhattan_kPaths_routeAtomicity(self):
        """
        Assumption that k = 3

        Pass if the method kPaths() generates routes which are not the same as one another (they are all distinct)
        """

        src.code.RoutingFunctions.K_MAX = 3
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        sim.getGlobalEdgeWeights()

        currentLane = traci.vehicle.getLaneID("testVeh")
        currentEdge = traci.lane.getEdgeID(currentLane)

        # Initialising cumulativeExtraTime for testVeh
        func.cumulativeExtraTime['testVeh'] = 0

        kPaths = func.kPaths("testVeh", currentEdge)

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
        src.code.RoutingFunctions.K_MAX = 3
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        traci.simulationStep()
        sim.getGlobalEdgeWeights()

        # Assigning non-optimal route
        nonOptimalRoute = ['46538375#5', '46538375#6', '196116976#7', '196116976#8', '194920158#9', '420908137#1',
                           '420908138#0', '420908138#1', '5670867#0', '5673497', '441405435', '569345531', '569345535',
                           '46538335#0', '569345536', '569345537#0', '569345537#2']
        traci.vehicle.setRoute("testVeh", nonOptimalRoute)

        currentLane = traci.vehicle.getLaneID("testVeh")
        currentEdge = traci.lane.getEdgeID(currentLane)

        # Initialising cumulativeExtraTime for testVeh
        func.cumulativeExtraTime['testVeh'] = 0

        routeList = func.kPaths("testVeh", currentEdge)

        # Checks that the non-optimal route is not given from the k paths (as the 3 paths should have a lower estimated
        # time) and that the vehicle's current route is one of those found in the routeList (the selected route has been
        # assigned to the vehicle successfully
        self.assertTrue(nonOptimalRoute not in routeList and traci.vehicle.getRoute("testVeh") in routeList)

    def test_smallManhattan_kPaths_routeSelectionTime(self):
        """
        Assumption that k = 3 and KPATH_TIME_LIMIT = 2

        Pass if the best route time and the worst route time are bounded between bestTime - bestTime*KPATH_TIME_LIMIT
        """
        src.code.RoutingFunctions.K_MAX = 3
        func.KPATH_MAX_ALLOWED_TIME = 2
        testing.Testing().setupGenericCarSM()
        traci.simulationStep()
        traci.simulationStep()
        sim.getGlobalEdgeWeights()

        currentLane = traci.vehicle.getLaneID("testVeh")
        currentEdge = traci.lane.getEdgeID(currentLane)

        # Initialising cumulativeExtraTime for testVeh
        func.cumulativeExtraTime['testVeh'] = 0

        routeList = func.kPaths("testVeh", currentEdge)

        bestTime = sys.maxsize
        worstTime = 0

        for route in routeList:
            routeTime = sim.getGlobalRoutePathTime(route)
            if routeTime < bestTime:
                bestTime = routeTime
            else:
                if routeTime > worstTime:
                    worstTime = routeTime

        self.assertLess(bestTime, worstTime)

    def test_smallManhattan_rerouteSelectedVehicles_vehicleReroutedOnSingleOutgoingEdge(self):
        """
        We know that 'testVeh' begins on edge 46538375#5, which is the single incoming edge to edge 46538375#6. Given
        that, congestion will be assumed on edge 46538375#6 which means that 'testVeh' should be selected for rerouting
        and consequently rerouted.

        Pass if 'testVeh' route is changed from the non-optimal route which is manually assigned before rerouting occurs
        """
        testing.Testing().setupGenericCarSM(initialise=True)
        sim.getGlobalEdgeWeights()
        # Load the vehicles into the simulation
        traci.simulationStep()
        # This is a non-optimal route to the same target edge
        nonOptimalRoute = ['46538375#5', '46538375#6', '46538375#7', '46538375#9', '46538375#10', '46538375#11',
                           '569345537#2']

        # This is the optimal route to the same target edge at the same time in which the vehicle is being rerouted
        # (this should be the same as the route after rerouteSelectedVehicles() is called as it is the same timestep
        traci.vehicle.rerouteTraveltime("testVeh")
        optimalRoute = traci.vehicle.getRoute("testVeh")
        # Setting the vehicle's path to be the non-optimal route
        traci.vehicle.setRoute("testVeh", nonOptimalRoute)

        func.rerouteSelectedVehicles("46538375#6")
        routeAfterRerouting = traci.vehicle.getRoute("testVeh")

        self.assertTrue(routeAfterRerouting != nonOptimalRoute and routeAfterRerouting == optimalRoute)

    def test_smallManhattan_selectVehiclesForRerouting_vehiclesOnMultipleEdges(self):
        """
        Instead of vehicles all being on the same edge, instead we shall test if, when given an edge, all of the
        vehicles incoming to that congested edge up to MAX_EDGE_RECURSION_RANGE (default 3) are selected
        """
        # The timing between the insertions of the vehicles have been specially chosen so that each vehicle is on a
        # separate stretch of road (edge), all vehicles share the same route. Additionally, all vehicles are in
        # sequential order in terms of their route (testVeh4 is on the first edge, immediately after testVeh3 is on the
        # second edge in the route definition, ...)
        testing.Testing().setupGenericCarSM(zoom=False)
        for i in range(20): traci.simulationStep()
        testing.Testing().setupGenericCarSM("testVeh2", zoom=False, routeName="testVeh2Route")
        for i in range(10): traci.simulationStep()
        testing.Testing().setupGenericCarSM("testVeh3", zoom=False, routeName="testVeh3Route")
        for i in range(20): traci.simulationStep()
        testing.Testing().setupGenericCarSM("testVeh4", zoom=False, routeName="testVeh4Route")

        # testVeh is out in front
        nextEdge = sim.getEdgeOneAheadVehicleRoute("testVeh")

        # Eligible vehicles should be 3 recursive edges away from the edge ahead of testVeh, as vehicles are in
        # sequential order according to their route definition 'testVeh', 'testVeh2', and 'testVeh3' should appear while
        # 'testVeh4' shouldn't as it's outside of the 3 recursive edges away (being 4 edges away from the point of
        # congestion).
        eligible, _, _, _ = func.selectVehiclesForRerouting(nextEdge)
        self.assertEqual(sorted(eligible), ['testVeh', 'testVeh2', 'testVeh3'])

    def test_smallManhattan_kPaths_singlePathAvailable(self):
        """
        Assumption that k = 3
        There is only a single valid route to the destination, therefore kPaths() should return only a single route.
        """
        src.code.RoutingFunctions.K_MAX = 3

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

        sim.getGlobalEdgeWeights()

        currentLane = traci.vehicle.getLaneID("testVeh")
        currentEdge = traci.lane.getEdgeID(currentLane)

        # Initialising cumulativeExtraTime for testVeh
        func.cumulativeExtraTime['testVeh'] = 0

        routeList = func.kPaths("testVeh", currentEdge)

        singleRoute = []
        for route in routeList:
            singleRoute.extend(routeList)

        self.assertTrue(len(routeList) == 1)
        self.assertEqual(initialRoute, route)

    def test_smallManhattan_rerouteSelectedVehicles_noVehicles(self):
        """
        No vehicles are selected as there are no vehicles which are incoming to the road segment from
        MAX_EDGE_RECURSIONS_RANGE away
        """
        # Maximum range is 3
        src.code.RoutingFunctions.MAX_EDGE_RECURSIONS_RANGE = 3

        testing.Testing().setupGenericCarSM()
        traci.simulationStep()

        # Vehicle should be only 1 edge away from this point (and has the edge in it's route) so should be selected
        # based on this
        returned, _, _, _ = func.selectVehiclesForRerouting('46538375#6')
        self.assertEqual(returned, ['testVeh'])

        #  Vehicle is nowhere near this edge, should return an empty list
        returned, _, _, _ = func.selectVehiclesForRerouting('5672118#2')
        self.assertEqual(returned, [])

    def test_smallManhattan_multiIncomingEdges(self):
        """
        Checks that the values held in multiIncomingEdges variable matches the expected incoming edges up to
        MAX_RECURSIVE_INCOMING_EDGES (assumption that it is 3) away from the target edge
        """
        src.code.RoutingFunctions.MAX_EDGE_RECURSIONS_RANGE = 3
        targetEdge = '511924978#1'
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '497165753#5', '569345508#1',
                          '5673497', '458180186#0', '497165756#2', '497165756#1'}

        initialFunc.initialisation()
        self.assertEqual(initialFunc.multiIncomingEdges[targetEdge], expectedOutput)

    def test_calculateAverageRoadCongestion(self):
        """
        Ensures that the calculateAverageRoadCongestion() function works
        :return: True if correct value returned
        """
        sim.roadCongestion = {}
        sim.roadCongestion['road_1'] = 0.5
        sim.roadCongestion['road_2'] = 0.6
        sim.roadCongestion['road_3'] = 0.2

        manualCalculation = (0.5 + 0.6 + 0.2) / 3
        functionCalculation = sim.calculateAverageRoadCongestion()

        self.assertEqual(manualCalculation, functionCalculation)


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

    def test_newark_multiIncomingRecursion_3Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 3
        """
        output = initialFunc.getMultiIncomingEdges("511924978#1")
        self.assertEqual(output, ['497165756#3', '511924978#0', '441405436', '569345515#0', '497165753#5',
                                  '569345508#1', '5673497', '458180186#0', '497165756#2', '497165756#1'])

if __name__=="__main__":
    unittest.main(exit=False, warnings='ignore')
