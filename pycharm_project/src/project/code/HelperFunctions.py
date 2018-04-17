import collections
import random
import time

import traci
from copy import deepcopy

from src.project.code import SumoConnection as sumo
from src.project.code import InitialMapHelperFunctions as initialFunc

"""
The HelperFunctions.py file deals with functions which are called during the runtime of the simulation in order to 
manipulate the vehicles within the simulation or return information regarding the current conditions present within
the simulation so that further action may be taken.
"""

# This is the penalisation factor given to the edge estimated travel time
PENALISATION = 2

# Stores the edge and their CURRENT corresponding estimated travel time
edgeSpeedGlobal = {}
# Stores the edge and their ADJUSTED corresponding estimated travel time (allows for penalisation of travel times)
adjustedEdgeSpeedGlobal = {}


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
    # print("Edge {} has congestion level {}".format(edge, returnCongestionLevelEdge(edge)))

    # Creating a named tuple to store (x, y) information
    coord = collections.namedtuple('coord', ['x', 'y'])
    c = coord(x=x, y=y)
    return c


def kPathsVehiclesList(edgesVehicleList):
    """
    Selects k potential outgoing paths from an edge

    Args:
        edgesVehicleList ({str: int[]}): Edges along with the vehicles which occupy them in the format edges: vehicles[]
    Returns:
        COMPLETE
    """
    for edge in edgesVehicleList.keys():
        print("edge {} outgoing {}".format(edge, initialFunc.getOutgoingEdges(edge)))


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
    # This is the list of all of the vehicles which have been rerouted
    reroutedList = set()

    # Going through the incoming edges and identifying vehicles on them
    for edge in initialFunc.multiIncomingEdges[edgeID]:
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
        # CHECK IF IT'S BETTER TO MODEL THIS OLD PATH AS A SET OR NOT
        oldPath = traci.vehicle.getRoute(vehicle)
        # If the edgeID exists in the vehicles current route then reroute them
        if edgeID in oldPath:
            # Reroute vehicles based on current travel times
            traci.vehicle.rerouteTraveltime(vehicle)
            reroutedList.add(vehicle)
            # if edgeID not in oldPath:
            #     print("Vehicle {} heading towards edge {} has been rerouted.\n"
            #           "     Old route: {}\n"
            #           "     New route: {}".format(vehicle, edgeID, oldPath, traci.vehicle.getRoute(vehicle)))

    # if sumo.ALGORITHM == 2:

    return reroutedList

def rerouteSelectedVehiclesLane(edgeID, laneID):
    """
    Selects the vehicles to be rerouted from the laneID (the lane which is currently congested) which belongs to edgeID
    and reroutes them based on current estimated travel times

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
    # This is the list of all of the vehicles which have been rerouted
    reroutedList = set()

    # Going through the incoming edges and identifying vehicles on them
    for edge in initialFunc.multiIncomingEdges[edgeID]:
        vehiclesOnEdge = traci.edge.getLastStepVehicleIDs(edge)
        # Appending the list of vehicles from edge onto vehiclesList
        vehiclesList.extend(vehiclesOnEdge)

        # If vehicles exist on that edge
        if vehiclesOnEdge:
            edgesList[edge] = vehiclesOnEdge

    # Effectively, we are testing if the vehicles need to occupy this specific lane to continue their journey, or if
    # another lane on the edge could instead be used/is necessary
    outgoingLanes = initialFunc.directedGraphLanes[laneID]

    # What vehicles have the edgeID
    for vehicle in vehiclesList:
        # The old/current path of the vehicle
        oldPath = traci.vehicle.getRoute(vehicle)
        # If the edgeID exists in the vehicles current route then reroute them
        if edgeID in oldPath:
            congestionIndex = oldPath.index(edgeID)
            # The edge intended to be taken by the vehicle directly after they have left the congested edge
            nextEdge = oldPath[congestionIndex + 1]
            lanesInNextEdge = initialFunc.edgesNetwork[nextEdge]

            # Testing if lanes present in the edge after the congested edge (of the vehicle's route) are any of the
            # outgoing lanes from the congested lane, otherwise do not reroute the vehicle as this congestion will not
            # affect the vehicle.
            if any(lane in lanesInNextEdge for lane in outgoingLanes):
                # Reroute vehicles based on current travel times
                traci.vehicle.rerouteTraveltime(vehicle)
                reroutedList.add(vehicle)


    return reroutedList


def getRoutePathTimeVehicle(veh, route="null"):
    """
    Calculates the total estimated time, considering the current road network conditions, of the route of a particular
    vehicle (for it's particular internal edge weights)

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

# def getRoutePathTime(route):
#     """
#     Calculates the total estimated time, considering the current road network conditions (for the entire road network)
#     of the route passed
#
#     Args:
#         route (str[]): The route in which the edges shall be checked for
#     Returns:
#         int: The estimated route time to take the route
#     """
#     totalEstimatedTime = 0
#
#     for edge in route:
#         # This is the vehicle's internal travel time for this edge
#         vehAdaptedTime = traci.vehicle.getAdaptedTraveltime(veh, time=currentTime, edgeID=edge)
#         # If adapted travel time has not been set
#         if vehAdaptedTime == -1001.0:
#             # Setting the vehicle's internal edge travel time to be the same as the global edge travel time
#             vehAdaptedTime = edgeSpeedGlobal[edge]
#         totalEstimatedTime += vehAdaptedTime
#         # Sets the vehicle's internal travel time for that edge
#         traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=vehAdaptedTime)
#
#     return totalEstimatedTime

def getGlobalRoutePathTime(route, realTime=True):
    """
    Calculates the total path time on a global scale, not specific to a vehicle

    Args:
        route (str): The route across the road network
        realTime (bool): This specifies whether or not the true current travel times should be used or if the user wants
        to test based on a certain adjusted road network (the adjustedEdgeSpeedGlobal) for rerouting purposes
    Returns:
        int: The estimated route times
    """
    totalEstimatedTime = 0

    if realTime:
        for edgeRealtime in route:
            totalEstimatedTime += edgeSpeedGlobal[edgeRealtime]
    else:
        for edge in route:
            totalEstimatedTime += adjustedEdgeSpeedGlobal[edge]

    return totalEstimatedTime

def aStar(edgeID):
    pass


# def kPaths(veh):
#     """
#     Determines k shortest paths for the vehicle and randomly assigns one
#
#     Args:
#         veh (str): The vehicle which needs rerouting
#     Returns:
#         routeList ([[str]]): The list of routes in which the vehicle could possibly be chosen to take (in the form
#         [[route1], [route2]... [routeK_MAX]])
#     """
#
#     # Contains a list of the routes (where each route consists of a list of edges)
#     routeList = []
#     # Counter
#     k = 1
#     # A set of all of the edges
#     edgesSet = set()
#
#     # Finding the best possible route for the vehicle
#     traci.vehicle.rerouteTraveltime(veh)
#     # The vehicle's current route
#     currentRoute = traci.vehicle.getRoute(veh)
#     bestTime = getGlobalRoutePathTime(currentRoute)
#
#     # Populating lists with the best route
#     routeList.append(currentRoute)
#     edgesSet.update(currentRoute)
#
#     # Creating up to k-1 additional routes
#     while k < sumo.K_MAX:
#         print()
#         print("This is the current route time {}".format(getRoutePathTimeVehicle(veh, currentRoute)))
#         print("This is the global route times {}".format(getGlobalRoutePathTime(currentRoute)))
#         penalisePathTime(currentRoute)
#
#         traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
#         newRoute = traci.vehicle.getRoute(veh)
#         newRouteTime = getGlobalRoutePathTime(newRoute, False)
#
#         currentRoute = newRoute
#         # Ensuring the route doesn't exist within the routeList
#         if currentRoute not in routeList:
#             # New route's estimated time doesn't exceed >20% of the optimal route time
#             if newRouteTime <= bestTime*1.2:
#                 routeList.append(currentRoute)
#                 edgesSet.update(currentRoute)
#                 k += 1
#             else:
#                 break
#
#     randomNum = random.randint(0, sumo.K_MAX - 1)
#     # Selecting a random route
#     routeSelection = routeList[randomNum]
#
#     traci.vehicle.setRoute(vehID=veh, edgeList=routeSelection)
#
#     # Setting the adjusted travel times for the edges to their default (the original estimated travel time given the
#     # current network traffic conditions).
#     adjustedEdgeSpeedGlobal = deepcopy(edgeSpeedGlobal)
#     for edge in adjustedEdgeSpeedGlobal.keys():
#         traci.edge.adaptTraveltime(edgeID=edge, time=adjustedEdgeSpeedGlobal[edge])
#
#     return routeList

def kPaths(veh):
    """
    Determines k shortest paths for the vehicle and randomly assigns one

    Args:
        veh (str): The vehicle which needs rerouting
    Returns:
        routeList ([[str]]): The list of routes in which the vehicle could possibly be chosen to take (in the form
        [[route1], [route2]... [routeK_MAX]])
    """
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
    bestTime = getGlobalRoutePathTime(currentRoute)

    # Populating lists with the best route
    routeList.append(currentRoute)
    edgesSet.update(currentRoute)

    # This is a fail safe in case there are less paths than K_MAX available for the vehicle to take
    timeOut = 0

    # Creating up to k-1 additional routes
    while k < sumo.K_MAX:
        print()
        print("This is the current route time {}".format(getRoutePathTimeVehicle(veh, currentRoute)))
        print("This is the global route times {}".format(getGlobalRoutePathTime(currentRoute)))
        penalisePathTimeVehicle(veh, currentRoute)

        traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
        newRoute = traci.vehicle.getRoute(veh)
        newRouteTime = getGlobalRoutePathTime(newRoute)

        currentRoute = newRoute
        # Ensuring the route doesn't exist within the routeList
        if currentRoute not in routeList:
            timeOut = 0
            # New route's estimated time doesn't exceed >20% of the optimal route time
            if newRouteTime <= bestTime*1.2:
                routeList.append(currentRoute)
                edgesSet.update(currentRoute)
                k += 1
            else:
                break
        else:
            timeOut += 1
            if timeOut == 10:
                break

    randomNum = random.randint(0, len(routeList) - 1)
    # Selecting a random route
    routeSelection = routeList[randomNum]

    traci.vehicle.setRoute(vehID=veh, edgeList=routeSelection)

    # Settings the vehicle's internal edge travel time back to the global edge travel time
    for edge in edgesSet:
        traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=edgeSpeedGlobal[edge])

    return routeList


# def k3Paths(veh):
#     """
#     Generates k-shortest paths for the vehicle and randomly selects one
#
#     Args:
#         veh (str): The vehicle which needs rerouting
#     """
#     # Getting the edge weights of the entire scenario for the current time step
#     getGlobalEdgeWeights()
#
#     # Set of all of the edges in which the vehicle's routes consist
#     edgesSet = set()
#     # A list containing the routes the vehicle can take
#     routeList = []
#     # Counter
#     k = 1
#
#     # Finding the best possible route for the vehicle
#     traci.vehicle.rerouteTraveltime(veh)
#     currentRoute = traci.vehicle.getRoute(veh)
#     # The best possible routes time taken
#     bestTime = getGlobalRoutePathTime(currentRoute)
#
#     # Populating lists with the best route
#     routeList.append(currentRoute)
#     edgesSet.update(currentRoute)
#
#     # Creating up to k-1 additional routes
#     while k < sumo.K_MAX:
#         # Penalising the currentRoute
#         penalisePathTimeVehicle(veh, currentRoute)
#
#         # Generating new route
#         traci.vehicle.rerouteTraveltime(veh, currentTravelTimes=True)
#         currentRoute = traci.vehicle.getRoute(veh)
#         newRouteTime = getGlobalRoutePathTime(currentRoute)
#
#         # Ensuring the route doesn't exist within the routeList
#         if currentRoute not in routeList:
#             # New route's estimated time doesn't exceed >20% of the optimal route time
#             if newRouteTime <= bestTime*1.2:
#                 routeList.append(currentRoute)
#                 edgesSet.update(currentRoute)
#                 k += 1
#             else:
#                 break
#
#     # Selecting a random route
#     randomNum = random.randint(0, sumo.K_MAX - 1)
#     routeSelection = routeList[randomNum]
#     traci.vehicle.setRoute(vehID=veh, edgeList=routeSelection)
#
#     # Settings the vehicle's internal edge travel time back to the global edge travel time
#     for edge in edgesSet:
#         traci.vehicle.setAdaptedTraveltime(vehID=veh, edgeID=edge, time=edgeSpeedGlobal[edge])


def penalisePathTimeVehicle(veh, route):
    """
    Penalises the path time of a particular vehicle, used for k-shortest paths

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


def penalisePathTime(route):
    """
    Penalises the path time of the edge

    Args:
        route (str): The edges (contained within the route) to be penalised
    """
    for edge in route:
        # Getting the current adapted time for that edge
        currentAdaptedTime = adjustedEdgeSpeedGlobal[edge]
        # Penalise the travel time by PENALISATION
        adjustedEdgeSpeedGlobal[edge] = currentAdaptedTime * 2
        traci.edge.adaptTraveltime(edge, adjustedEdgeSpeedGlobal[edge])


def getGlobalEdgeWeights():
    """
    Populates the global edge weight variable, which stores the edge and corresponding estimated travel time
    """
    # Clears the mapping for this timestep
    # edgeSpeedGlobal.clear()
    for edge in traci.edge.getIDList():
        travelTime = traci.edge.getTraveltime(edge)
        edgeSpeedGlobal[edge] = travelTime
        adjustedEdgeSpeedGlobal[edge] = travelTime
        # Initially setting the weights for the road network as being the current estimated travel times
        traci.edge.adaptTraveltime(edge, travelTime)