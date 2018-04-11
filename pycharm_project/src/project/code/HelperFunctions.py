import collections
import traci
import random
import time
import sys

from src.project.code import SumoConnection as sumo
from src.project.code import RoutingAlgorithms as algo

# This describes the penalisation given to the edge weights
PENALISATION = 2
# This is the minimum edge/lane length to be considered for possible rerouting
MIN_EDGE_LENGTH = 25

# Stores the edge and their corresponding estimated travel time
edgeSpeedGlobal = {}

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
# Stores the directed graph in terms of the lanes in the format {originLane: [outgoingLanes]}
directedGraphLanes = {}
# Stores the directed graph in terms of the edges in the format {originEdge: [outgoingEdges]}
directedGraphEdges = {}

# These are the edges which only nave a single outgoing connection (there is only a single edge outgoing)
singleOutgoingEdges = set()
# These are the lanes which share an edge which has at least 2 outgoing edges from it
reroutingLanes = set()


def initialisation():
    """
    This initialises the simulation with settings which are relevant to all scenarios
    """
    loadMap()
    createDirectedRoadNetwork()
    collectEdgesWithSingleOutgoing()
    collectEdgesWithMultiOutgoing()

    # for edge in fringeEdges:
    #     if edge in singleOutgoingEdges:
    #         print("NO EDGES")
    #
    # for lane in reroutingLanes:
    #     edge = lanesNetwork[lane]
    #     if edge in fringeEdges:
    #         print("NO LANE")

    sumo.timerStart = time.clock()

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

def getGlobalEdgeWeights():
    """
    Populates the global edge weight variable, which stores the edge and corresponding estimated travel time
    """
    # Clears the mapping for this timestep
    edgeSpeedGlobal.clear()
    for edge in traci.edge.getIDList():
        edgeSpeedGlobal[edge] = traci.edge.getTraveltime(edge)

def returnCongestionLevelLane(laneID):
    """
    Gives the congestion level of the road, laneID

    Args:
        laneID (str): The ID of the lane (road)
    Return:
         float: The occupancy (congestion) of the road, in percentage
    """
    return traci.lane.getLastStepOccupancy(laneID)

def returnCongestionLevelEdge(edgeID):
    """
    Gives the congestion level of the edge

    Args:
        edgeID (str): The ID of the edge
    Return:
         float: The occupancy (congestion) of the road, in percentage
    """
    return traci.edge.getLastStepOccupancy(edgeID)

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

def getEdge2DCoordinates(edge):
    """
    Gets the 2D coordinates of the 'from' node which connects to the lane

    Args:
        edge (str): The edge to teleport to
    Returns:
        (str, str): Returns the tuple (x, y)
            Individual elements can be accessed by tuple.x and tuple.y
    """
    # Getting them 'from' node associated with that edge
    node = sumo.net.getEdge(edge).getFromNode().getID()
    # Getting the 2D coordinates (x, y) for that node
    x, y = sumo.net.getNode(node).getCoord()
    # Changes the GUI offset to the coordinates of the node
    traci.gui.setOffset("View #0", x, y)
    print("Edge {} has congestion level {}".format(edge, returnCongestionLevelEdge(edge)))

    # Creating a named tuple to store (x, y) information
    coord = collections.namedtuple('coord', ['x', 'y'])
    c = coord(x=x, y=y)
    return c


def getOutgoingEdges(edgeID):
    """
    Returns a list of all of the outgoing edges to the specified edge

    Args:
        edgeID (str): The identification of the edge to collect outgoing edges
    Returns:
        outgoingEdgeList (str[]): The edges outgoing from edgeID
    """
    outgoingEdgeList = []
    for edgeOut in sumo.net.getEdge(edgeID).getOutgoing():
        outgoingEdgeList.append(edgeOut.getID())
    return outgoingEdgeList

def getOutgoingLanes(laneID):
    """
    Returns a list of all of the outgoing lanes to the specified lane

    Args:
        laneID (str): The identification of the lane to collect outgoing lanes
    Returns:
        outgoingLaneList (str[]): The outgoing lanes
    """
    outgoingLaneList = []
    for laneOut in sumo.net.getLane(laneID).getOutgoing():
        outgoingLaneList.append(laneOut.getToLane().getID())
    return outgoingLaneList

def kPathsVehiclesList(edgesVehicleList):
    """
    Selects k potential outgoing paths from an edge

    Args:
        edgesVehicleList ({str: int[]}): Edges along with the vehicles which occupy them in the format edges: vehicles[]
    Returns:
        COMPLETE
    """
    for edge in edgesVehicleList.keys():
        print("edge {} outgoing {}".format(edge, getOutgoingEdges(edge)))


def rerouteSelectedVehiclesEdge(edgeID):
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
    # The edges and their corresponding vehicles in the order {edge : vehicle (str[])}
    edgesList = {}

    # Going through the incoming edges and identifying vehicles on them
    for edge in getMultiIncomingEdges(edgeID):
        vehiclesOnEdge = traci.edge.getLastStepVehicleIDs(edge)
        # Appending the list of vehicles from edge onto vehiclesList
        vehiclesList.extend(vehiclesOnEdge)

        # If vehicles exist on that edge
        if vehiclesOnEdge:
            edgesList[edge] = vehiclesOnEdge

    # print(edgesList)

    # What vehicles have the edgeID
    for vehicle in vehiclesList:
        # The old/current path of the vehicle
        oldPath = set(traci.vehicle.getRoute(vehicle))
        # If the edgeID exists in the vehicles current route then reroute them
        if edgeID in oldPath:
            # Reroute vehicles based on current travel times
            traci.vehicle.rerouteTraveltime(vehicle)

            # if edgeID not in oldPath:
            #     print("Vehicle {} heading towards edge {} has been rerouted.\n"
            #           "     Old route: {}\n"
            #           "     New route: {}".format(vehicle, edgeID, oldPath, traci.vehicle.getRoute(vehicle)))

    # if sumo.ALGORITHM == 2:

    return vehiclesList

def rerouteSelectedVehiclesLane(edgeID, laneID):
    """
    Selects the vehicles to be rerouted from edgeID (the edge which is currently congested) and reroutes them based
    on current estimated travel times

    Args:
        edgeID (str): The edge in which the congestion is occurring
    Returns:
        str[]: The list of vehicles to be rerouted
    """
    totalTime = 0
    startTime = time.clock()

    # The list of vehicles existing on the edges
    vehiclesList = []
    # The edges and their corresponding vehicles in the order {edge : vehicle (str[])}
    edgesList = {}

    # Going through the incoming edges and identifying vehicles on them
    for edge in getMultiIncomingEdges(edgeID):
        vehiclesOnEdge = traci.edge.getLastStepVehicleIDs(edge)
        # Appending the list of vehicles from edge onto vehiclesList
        vehiclesList.extend(vehiclesOnEdge)

        # If vehicles exist on that edge
        if vehiclesOnEdge:
            edgesList[edge] = vehiclesOnEdge

    # print(edgesList)

    # Effectively, we are testing if the vehicles need to occupy this specific lane to continue their journey, or if
    # another lane on the edge could instead be used/is necessary
    outgoingLanes = directedGraphLanes[laneID]


    # What vehicles have the edgeID
    for vehicle in vehiclesList:
        # The old/current path of the vehicle
        oldPath = traci.vehicle.getRoute(vehicle)
        # If the edgeID exists in the vehicles current route then reroute them
        if edgeID in oldPath:
            congestionIndex = oldPath.index(edgeID)
            # The edge intended to be taken by the vehicle directly after they have left the congested edge
            nextEdge = oldPath[congestionIndex + 1]
            lanesInNextEdge = edgesNetwork[nextEdge]

            # Testing if lanes present in the next edge (of the vehicle's route) are any of the outgoing lanes from the
            # congested lane
            if any(lane in lanesInNextEdge for lane in outgoingLanes):
                # Reroute vehicles based on current travel times
                traci.vehicle.rerouteTraveltime(vehicle)
                ok = "ok"
            else:
                meep = "meep"

            # print("Congested lane {} on edge {}".format(laneID, congestedEdge))
            # print(oldPath)
            # print(nextEdge)
            # print(edgesNetwork[edgeID])
            # print()


            # time.sleep(10)



            # if edgeID not in oldPath:
            #     print("Vehicle {} heading towards edge {} has been rerouted.\n"
            #           "     Old route: {}\n"
            #           "     New route: {}".format(vehicle, edgeID, oldPath, traci.vehicle.getRoute(vehicle)))

    # if sumo.ALGORITHM == 2:

    print()
    print("TIMER {}".format(time.clock() - startTime))
    print()

    return vehiclesList


def penalisePathTime(veh, route):
    """
    Penalises the path time of the vehicle, used for k-shortest paths

    Args:
        veh (str): The vehicle which needs to have the adjusted route time
        route (str): The route to be penalised for the vehicle, veh
    """
    currentSysTime = sumo.Main.getCurrentTime()
    for edge in route:
        # Sets an adapted travel time for an edge (specifically for that vehicle)
        currentAdaptedTime = traci.vehicle.getAdaptedTraveltime(vehID=veh, edgeID=edge, time=currentSysTime)
        # Penalise the travel time by a multiplication of 2
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=(currentAdaptedTime*PENALISATION))

    # print("This is the current time {}".format(currentSysTime))
    # print("EDGE 46538375#6 PENALISED {}".format(traci.vehicle.getAdaptedTraveltime("testVeh", time=currentSysTime, edgeID="46538375#6")))


def getRoutePathTime(veh, route="null"):
    """
    Calculates the total estimated time, considering the current road network conditions, of the route of a vehicle

    Args:
        veh (str): The vehicle with the route to test
        route (str[]): The route the vehicle is taking
    Returns:
        int: The estimated route time for veh (for defined route, otherwise current)
    """
    currentTime = sumo.Main.getCurrentTime()
    totalEstimatedTime = 0
    # If route has not been defined, set route to the current vehicle route
    if route == "null":
        route = traci.vehicle.getRoute(veh)

    for edge in route:
        # This is the vehicle's internal travel time for this edge
        vehAdaptedTime = traci.vehicle.getAdaptedTraveltime(veh, time=currentTime, edgeID=edge)
        # If adapted travel time has not been set
        if vehAdaptedTime == -1001.0:
            # Setting the vehicle's internal edge travel time to be the same as the global edge travel time
            vehAdaptedTime = edgeSpeedGlobal[edge]
        totalEstimatedTime += vehAdaptedTime
        # Sets the vehicle's internal travel time for that edge
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=vehAdaptedTime)

    return totalEstimatedTime

def getGlobalRoutePathTime(route):
    """
    Calculates the total path time on a global scale, not specific to a vehicle

    Args:
        route (str): The route across the road network
    Returns:
        int: The estimated route times
    """
    totalEstimatedTime = 0
    for edge in route:
        totalEstimatedTime += edgeSpeedGlobal[edge]

    return totalEstimatedTime

def aStar(edgeID):
    pass


def kPaths(veh):
    """
    Selects k shortest paths for the vehicle and randomly selects one

    Args:
        veh (str): The vehicle which needs rerouting
    Returns:
        FILL IN
    """
    # Getting the edge weights of the entire scenario for the current time step
    getGlobalEdgeWeights()

    # Contains a list of the routes (where each route consists of a list of edges)
    routeList = []
    # Counter
    k = 1
    # A set of all of the edges
    edgesSet = set()

    # Finding the best possible route for the vehicle
    traci.vehicle.rerouteTraveltime(veh)
    # The vehicle's current route
    currentRoute = traci.vehicle.getRoute(veh)
    # The best possible routes time taken
    bestTime = getGlobalRoutePathTime(currentRoute)
    print("Not penalised {}".format(getRoutePathTime(veh, currentRoute)))

    # Populating lists with the best route
    routeList.append(currentRoute)
    edgesSet.update(currentRoute)

    # Creating up to k-1 additional routes
    while k < sumo.K_MAX:
        print()
        print("This is the current route time {}".format(getRoutePathTime(veh, currentRoute)))
        print("This is the global route times {}".format(getGlobalRoutePathTime(currentRoute)))
        penalisePathTime(veh, currentRoute)

        traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute(veh)
        newRouteTime = getGlobalRoutePathTime(newRoute)

        currentRoute = newRoute
        # Ensuring the route doesn't exist within the routeList
        if currentRoute not in routeList:
            # New route's estimated time doesn't exceed >20% of the optimal route time
            if newRouteTime <= bestTime*10.2:
                routeList.append(currentRoute)
                edgesSet.update(currentRoute)
                k += 1
            else:
                break

    randomNum = random.randint(0, sumo.K_MAX - 1)
    # Selecting a random route
    routeSelection = routeList[randomNum]

    print(randomNum)
    print("The route selected is {}".format(routeSelection))

    traci.vehicle.setRoute(vehID=veh, edgeList=routeSelection)

    print()
    print("This is the routeList {}".format(routeList))
    print("This is the edgesSet {}".format(edgesSet))

    # Settings the vehicle's internal edge travel time back to the global edge travel time
    for edge in edgesSet:
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=edgeSpeedGlobal[edge])


def k3Paths(veh):
    """
    Generates k-shortest paths for the vehicle and randomly selects one

    Args:
        veh (str): The vehicle which needs rerouting
    """
    # Getting the edge weights of the entire scenario for the current time step
    getGlobalEdgeWeights()

    # Set of all of the edges in which the vehicle's routes consist
    edgesSet = set()
    # A list containing the routes the vehicle can take
    routeList = []
    # Counter
    k = 1

    # Finding the best possible route for the vehicle
    traci.vehicle.rerouteTraveltime(veh)
    currentRoute = traci.vehicle.getRoute(veh)
    # The best possible routes time taken
    bestTime = getGlobalRoutePathTime(currentRoute)

    # Populating lists with the best route
    routeList.append(currentRoute)
    edgesSet.update(currentRoute)

    # Creating up to k-1 additional routes
    while k < sumo.K_MAX:
        # Penalising the currentRoute
        penalisePathTime(veh, currentRoute)

        # Generating new route
        traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
        currentRoute = traci.vehicle.getRoute(veh)
        newRouteTime = getGlobalRoutePathTime(currentRoute)

        # Ensuring the route doesn't exist within the routeList
        if currentRoute not in routeList:
            # New route's estimated time doesn't exceed >20% of the optimal route time
            if newRouteTime <= bestTime*1.2:
                routeList.append(currentRoute)
                edgesSet.update(currentRoute)
                k += 1
            else:
                break

    # Selecting a random route
    randomNum = random.randint(0, sumo.K_MAX - 1)
    routeSelection = routeList[randomNum]
    traci.vehicle.setRoute(vehID=veh, edgeList=routeSelection)

    # Settings the vehicle's internal edge travel time back to the global edge travel time
    for edge in edgesSet:
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=edgeSpeedGlobal[edge])