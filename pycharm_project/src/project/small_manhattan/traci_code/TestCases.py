import unittest
import sumolib
import os

# import traci
from src.project.small_manhattan.traci_code import SumoConnection as sumo
# from src.project.small_manhattan.traci_code.SumoConnection import *
from src.project.small_manhattan.traci_code import RoutingAlgorithms as routing

#
# net = sumolib.net.readNet(os.getcwd()+"\small_manhattan.net.xml")

def fun(x):
    return x + 1


class MyUnitTests(unittest.TestCase):

    # def setUp(self):
    #     netFile = "D:/Nina/Dropbox/UNIVERSITY/YEAR 3/COMP3200 - 3rd Year Individual Project/sumo-project/" \
    #               "pycharm_project/src/project/small_manhattan/configuration_files/testing/small_manhattan.net.xml"
    #     net = sumolib.net.readNet(netFile)

    def test(self):
        self.assertEqual(fun(3), 4)
        # print(net.getEdges("hello"))

    def test_multiIncomingRecursion(self):
        test = routing.Testing()
        output = test.getMultiIncomingEdges("511924978#1")
        self.assertEqual(output, ['497165756#3', '511924978#0', '441405436', '569345515#0', '497165753#5', '569345508#1', '5673497', '458180186#0', '497165756#2', '497165756#1'])

if __name__=="__main__":

    unittest.main(exit=False)
