import collections
import traci

from src.project.code import SumoConnection as sumo
from src.project.code import RoutingAlgorithms as algo


def returnCongestionLevel(laneID):
    """
    Gives the congestion level of the road, laneID

    Args:
        laneID (str): The ID of the lane (road)
     Return:
         float: The occupancy (congestion) of the road, in percentage
    """
    return traci.lane.getLastStepOccupancy(laneID)


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


def getLane2DCoordinates(laneID):
    """
    Gets the 2D coordinates of the 'from' node which connects to the lane

    Args:
        laneID (str): The lane
    Returns:
        (str, str): Returns the tuple (x, y)
            Individual elements can be accessed by tuple.x and tuple.y
    """
    edge = traci.lane.getEdgeID(laneID)
    # Getting them 'from' node associated with that edge
    node = sumo.net.getEdge(edge).getFromNode().getID()
    # Getting the 2D coordinates (x, y) for that node
    x, y = sumo.net.getNode(node).getCoord()
    # Changes the GUI offset to the coordinates of the node
    traci.gui.setOffset("View #0", x, y)
    print("Lane {} has congestion level {}".format(laneID, returnCongestionLevel(laneID)))

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


def rerouteSelectedVehicles(edgeID):
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

    print(edgesList)

    # What vehicles have the edgeID
    for vehicle in vehiclesList:
        # The old/current path of the vehicle
        oldPath = traci.vehicle.getRoute(vehicle)
        # If the edgeID exists in the vehicles current route then reroute them
        if edgeID in traci.vehicle.getRoute(vehicle):
            # Reroute vehicles based on current travel times
            traci.vehicle.rerouteTraveltime(vehicle)

            if edgeID not in traci.vehicle.getRoute(vehicle):
                print("Vehicle {} heading towards edge {} has been rerouted.\n"
                      "     Old route: {}\n"
                      "     New route: {}".format(vehicle, edgeID, oldPath, traci.vehicle.getRoute(vehicle)))

    # if sumo.ALGORITHM == 2:
    #     kPathsVehiclesList(edgesList)

    # print("MEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEP")

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
        # Penalise the travel time by 2
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=currentAdaptedTime*200, begTime=currentSysTime,
                                           endTime=currentSysTime + 1)

    # print("This is the current time {}".format(currentSysTime))
    # print("EDGE 46538375#6 PENALISED {}".format(traci.vehicle.getAdaptedTraveltime("testVeh", time=currentSysTime, edgeID="46538375#6")))


def getRoutePathTime(veh, route="null"):
    """
    Calculates the total estimated time, considering the current road network conditions, of the route of a vehicle

    Args:
        veh (str): The vehicle with the route to test
    Returns:
        int: The estimated route times
    """
    currentTime = sumo.Main.getCurrentTime()
    totalEstimatedTime = 0
    if route == "null":
        route = traci.vehicle.getRoute(veh)

    for edge in route:
        # This is the vehicle's internal travel time for this edge
        vehAdaptedTime = traci.vehicle.getAdaptedTraveltime(veh, time=currentTime, edgeID=edge)
        # If adapted travel time has not been set
        if vehAdaptedTime == -1001.0:
            # Setting the vehicle's internal edge travel time to be the same as the global edge travel time
            vehAdaptedTime = traci.edge.getTraveltime(edge)
        totalEstimatedTime += vehAdaptedTime
        # Sets the vehicle's internal travel time for that edge for the duration of 1 second
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=vehAdaptedTime, begTime=currentTime,
                                           endTime=currentTime + 1)

    # print("This is the current time {}".format(currentTime))
    # print("EDGE 46538375#6 NOT {}".format(traci.vehicle.getAdaptedTraveltime(veh, time=currentTime, edgeID="46538375#6")))


    return totalEstimatedTime


def aStar(edgeID):
    pass


def kPaths(veh):
    # Contains a list of the routes (where each route consists of a list of edges)
    routeList = []
    # A list of all of the edges
    # Counter
    k = 0
    # The vehicle's current route
    currentRoute = traci.vehicle.getRoute(veh)
    print("Not penalised {}".format(getRoutePathTime(veh, currentRoute)))
    # penalisePathTime(veh, currentRoute)
    # print("Penalised {}".format(getRoutePathTime(veh, currentRoute)))
    # routeList.append(currentRoute)


    print(sumo.Main.getCurrentTime() + 100)
    # traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID="196116976#7", time=999999999, begTime=sumo.Main.getCurrentTime(), endTime=sumo.Main.getCurrentTime() + 200)

    # traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
    # rou = traci.vehicle.getRoute(veh)
    #
    # print("This is the old route {}".format(currentRoute))
    # print("This is the new route {}".format(rou))

    # Creating up to k-1 additional routes
    # while k < sumo.K_MAX:
    #     traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
    #     newRoute = traci.vehicle.getRoute(veh)
    #     print("This is the routeList {}".format(routeList))
    #     k += 1
    #     print("This is the route time {}".format(getRoutePathTime(veh, newRoute)))
    #     print("rou1 {}".format(newRoute))
    #     print("rou2 {}".format(currentRoute))
    #     # Ensuring the new route and current route are not exactly identical
    #     if newRoute != currentRoute:
    #         print("good")

