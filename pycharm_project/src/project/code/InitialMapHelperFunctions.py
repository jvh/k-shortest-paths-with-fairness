import sys
import time

import traci

from src.project.code import SumoConnection as sumo
from src.project.code import HelperFunctions as helpFunc

"""
This particular file deals with all of the information regarding the map, particularly the generation of the map into 
memory so that elements of the map may be efficiently accessed during runtime without unnecessary calls to Traci 
throughout.

Essentially, these functions are only called once at the start of the simulation. During runtime, instead of directly
calling the functions, the data shall be accessed by the corresponding variable.
"""

# This is the minimum edge/lane length to be considered for possible rerouting
MIN_EDGE_LENGTH = 25

# Stores the entire road network, with {edge: [lanes]}
edgesNetwork = {}
# Contains the laneID along with the corresponding edgeID in the format {laneID: edgeID}
lanesNetwork = {}
# Stores the edges which are on the fringe of the network (fringe edges)
fringeEdges = set()
# Stores the lengths of each lane in the format {laneID: length}
laneLengths = {}
# Stores the lengths of each edge in the format {edgeID: length}
edgeLengths = {}
# Stores the directed graph in terms of the lanes in the format {originLane: {outgoingLanes}}
directedGraphLanes = {}
# Stores the directed graph in terms of the edges in the format {originEdge: {outgoingEdges}}
directedGraphEdges = {}

# These are the edges which only nave a single outgoing connection (there is only a single edge outgoing)
singleOutgoingEdges = set()
# These are the lanes which share an edge which has at least 2 outgoing edges from it
reroutingLanes = set()
# Stores the edge and the corresponding incoming edges up to MAX_EDGE_RECURSION_RANGE away
multiIncomingEdges = {}


def endSim(i, manual = True):
    """
    Ends the simulation and prints the time taken

    Args:
        i (int): The timestep of the simulation
        manual (bool): Specifies if the simulation has been ended manually or at the point of simulation finish
    """
    sumo.timerEnd = time.clock()
    if manual:
        sys.exit("\nSystem has been ended manually at timestep {}, time taken {}".format(i, sumo.timerEnd -
                                                                                         sumo.timerStart))
    else:
        sys.exit("\nSimulation time has elapsed with {} timesteps, time taken {}".format(i, sumo.timerEnd -
                                                                                         sumo.timerStart))

def initialisation():
    """
    This initialises the simulation with settings which are relevant to all scenarios
    """
    loadMap()
    createDirectedRoadNetwork()
    collectEdgesWithSingleOutgoing()
    collectEdgesWithMultiOutgoing()
    generateRecursiveIncomingEdges()
    sumo.timerStart = time.clock()

def loadMap():
    """
    This loads the map into a dictionary (of edges) which contains a list of lanes for each edge. This has been
    implemented for efficiency purposes as many calls to SUMO through traci causes major slowdown.

    edgesNetwork is in the form {edge: [lanes]}: The edge with its corresponding lanes
    """
    # Populating all non-special edges
    for edgeID in traci.edge.getIDList():
        # Special edges, i.e. connector or internal edges, have ':' prepended to them, don't consider these in rerouting
        if edgeID[:1] != ":":
            edgesNetwork[edgeID] = []
            edgeLengths[edgeID] = sumo.net.getEdge(edgeID).getLength()
            # Finding edges on the fringe of the network
            populateFringeEdges(edgeID)

    # Populating edges with their corresponding non-special lanes
    for lane in traci.lane.getIDList():
        # Remove any special lanes
        if lane[:1] != ":":
            laneLengths[lane] = traci.lane.getLength(lane)
            edge = traci.lane.getEdgeID(lane)
            lanesNetwork[lane] = edge
            edgesNetwork[edge].append(lane)


def createDirectedRoadNetwork():
    """
    This stores the road network into a directed graph in terms of both lanes (directedGraphLanes) and edges
    (directedGraphEdges) for easy access
    """
    # Lane directed graph
    for lane in lanesNetwork.keys():
        directedGraphLanes[lane] = getOutgoingLanes(lane)

    # Edge directed Graph
    for edge in edgesNetwork.keys():
        directedGraphEdges[edge] = getOutgoingEdges(edge)


def collectEdgesWithSingleOutgoing():
    """
    Generates a list of all of the edges with at most 1 outgoing edge.

    The lanes existing on a edge with only a single outgoing edge will also only have a single outgoing lane (a single
    destination).

    This function only considers lanes which do not belong to a fringe edge and only accounts for lanes larger than
    MIN_EDGE_LENGTH
    """
    for edge in edgesNetwork.keys():
        if len(directedGraphEdges[edge]) == 1 and edge not in fringeEdges and edgeLengths[edge] >= MIN_EDGE_LENGTH:
            singleOutgoingEdges.add(edge)


def collectEdgesWithMultiOutgoing():
    """
    Generates a list of all of the edges with at least 2 outgoing edges.

    The lanes which exist on this edge may lead to different possible turns (i.e. a right hand lane may afford a right
    hand turn, whereas a left hand lane may afford a left hand turn). These lanes should be considered separately during
    rerouting as they may lead different directions with other lanes which share the same edge.

    This function only considers edges which do not belong to a fringe edge and only accounts for edges larger than
    MIN_EDGE_LENGTH
    """
    for edge in edgesNetwork.keys():
        if len(directedGraphEdges[edge]) >= 2 and edge not in fringeEdges and edgeLengths[edge] >= MIN_EDGE_LENGTH:
            for lane in edgesNetwork[edge]:
                reroutingLanes.add(lane)


def populateFringeEdges(edge):
    """
    Populates the fringeEdges variable with the edges which exist on the fringe of the network
    """
    if sumo.net.getEdge(edge).is_fringe():
        fringeEdges.add(edge)


def generateRecursiveIncomingEdges():
    """
    This generates all of the incoming edges up to MAX_EDGE_RECURSION_RANGE away from each edges and stores it in a
    dictionary as edge: set(recursive incoming edge list).

    This is calculated before runtime for easy access to the incoming edges of a particular edge during real time
    application
    """
    for edge in directedGraphEdges.keys():
        multiIncomingEdges[edge] = set(getMultiIncomingEdges(edge))


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
            In the format {edgeID: order}
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


def getOutgoingEdges(edgeID):
    """
    Returns a list of all of the outgoing edges to the specified edge

    Args:
        edgeID (str): The identification of the edge to collect outgoing edges
    Returns:
        outgoingEdgeSet (str{}): The edges outgoing from edgeID
    """
    outgoingEdgeSet = set()
    for edgeOut in sumo.net.getEdge(edgeID).getOutgoing():
        outgoingEdgeSet.add(edgeOut.getID())
    return outgoingEdgeSet


def getOutgoingLanes(laneID):
    """
    Returns a list of all of the outgoing lanes to the specified lane

    Args:
        laneID (str): The identification of the lane to collect outgoing lanes
    Returns:
        outgoingLaneSet (str{}): The outgoing lanes
    """
    outgoingLaneSet = set()
    for laneOut in sumo.net.getLane(laneID).getOutgoing():
        outgoingLaneSet.add(laneOut.getToLane().getID())
    return outgoingLaneSet


def getIncomingEdges(edgeID):
    """
    Returns a list of all of the incoming edges to the specified edge

    Args:
        edgeID (str): The identification of the edge to collect incoming edges
    Returns:
        incEdgeList (str[]): The edges incoming to edgeID
    """
    incEdgeList = []
    # This is the list of incoming edges for edgeID; however, these are references to the object and not their IDs
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