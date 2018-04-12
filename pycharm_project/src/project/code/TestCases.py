import unittest
import sumolib
import os
import traci

from src.project.code import SumoConnection as sumo
from src.project.code import RoutingAlgorithms as routing
from src.project.code import HelperFunctions as func
from src.project.code import Testing as testing

#
# net = sumolib.net.readNet(os.getcwd()+"\small_manhattan.net.xml")


class SmallSouthamptonTests(unittest.TestCase):
    """
    Tests ran when the scenario is 'Testing (small_manhattan)'
    """

    def setUp(self):
        """
        Ensures that the scenario is that of 'Testing (small_manhattan)'
        """
        if sumo.SCENARIO != 0:
            raise unittest.SkipTest("Scenario is {}, small Manhattan unit tests shall not be executed.".format(sumo.SCENARIO))
        else:
            testing.TESTING_NUMBER = 0
            main = sumo.Main()
            main.run(True, True, True)

    def tearDown(self):
        """
        Closes the traci connection once used
        """
        traci.close(False)

    # def setUp(self):
    #     netFile = "D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/" \
    #               "pycharm_project/src/project/small_manhattan/configuration_files/testing/small_manhattan.net.xml"
    #     net = sumolib.net.readNet(netFile)

    def test_smallManhattan_multiIncomingRecursion_4Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 2
        """
        sumo.MAX_EDGE_RECURSIONS_RANGE = 4
        output = func.getMultiIncomingEdges("511924978#1")
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
        output = func.getMultiIncomingEdges("511924978#1")
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '497165753#5', '569345508#1',
                          '5673497', '458180186#0', '497165756#2', '497165756#1'}
        self.assertEqual(set(output), expectedOutput)

    def test_smallManhattan_multiIncomingRecursion_2Recursions(self):
        """
        Tests that multiIncomingRecursion (and consequently recursiveIncomingEdges) returns the correct edges list when
        number of recursions (MAX_EDGE_RECURSIONS_RANGE) is equal to 2
        """
        sumo.MAX_EDGE_RECURSIONS_RANGE = 2
        output = func.getMultiIncomingEdges("511924978#1")
        expectedOutput = {'511924978#0', '497165756#3', '441405436', '569345515#0', '458180186#0', '497165756#2'}
        self.assertEqual(set(output), expectedOutput)

    def test_smallManhattan_directedGraphsEdges(self):
        """
        Tests that the directedGraphsEdges has been populated correctly (the edge has the correct outgoing edges)
        """
        self.assertEqual(func.directedGraphEdges['196116976#11'], {'46443656#3', '196116976#12'})

    def test_smallManhattan_directedGraphsLanes(self):
        """
        Tests that the directedGraphsLanes has been populated correctly (the lane has the correct outgoing lanes)
        """
        self.assertEqual(func.directedGraphLanes['542258337#5_1'], {'569345540#5_3', '569345540#5_2', '46443656#0_1'})

    def test_smallManhattan_singleOutgoingEdges(self):
        """
        True if the singleOutgoingEdges variable contains only edges with a single outgoing edge
        """
        for edge in func.singleOutgoingEdges:
            # Running with a subtest to identify point of failure (if any)
            with self.subTest(status_code=edge):
                self.assertTrue(len(sumo.net.getEdge(edge).getOutgoing()) == 1)

    def test_smallManhattan_reroutingLanes(self):
        """
        True if all the lanes contained within reroutingLanes have at least 2 outgoing lanes
        """
        for lane in func.reroutingLanes:
            with self.subTest(status_code=lane):
                edge = traci.lane.getEdgeID(lane)
                self.assertTrue(len(sumo.net.getEdge(edge).getOutgoing()) >= 2)

    def test_smallManhattan_fringeEdges(self):
        """
        True if all edges held within fringeEdges are fringe edges (edges on the fringe of the network - no incoming
        edges) in the traffic network
        """
        for edge in func.fringeEdges:
            with self.subTest(status_code=edge):
                self.assertTrue(sumo.net.getEdge(edge).is_fringe())

    # def test_smallManhattan_edgeSpeedGlobal(self):
    #     """
    #     Testing if the speeds in edgeSpeedGlobal are correct at the point of starting the simulation given that there
    #     are no vehicles in the simulation
    #     """
    #     for edge in func.edgeSpeedGlobal.keys():

    def test_smallManhattan_fringeEdges(self):
        """
        True if all edges held within fringeEdges are fringe edges (edges on the fringe of the network - no incoming
        edges) in the traffic network
        """
        for edge in func.fringeEdges:
            with self.subTest(status_code=edge):
                self.assertTrue(sumo.net.getEdge(edge).is_fringe())

    def test_smallManhattan_rerouteSelectedVehiclesEdge_noVehicles(self):
        """
        Congestion is detected 
        """
        for edge in func.fringeEdges:
            with self.subTest(status_code=edge):
                self.assertTrue(sumo.net.getEdge(edge).is_fringe())

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
        output = func.getMultiIncomingEdges("511924978#1")
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
