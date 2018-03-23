package project.small_manhattan.code;

import de.tudresden.sumo.cmd.Edge;
import de.tudresden.sumo.cmd.Gui;
import de.tudresden.sumo.cmd.Route;
import de.tudresden.sumo.cmd.Vehicle;
import de.tudresden.ws.container.SumoStringList;
import it.polito.appeal.traci.SumoTraciConnection;

import java.util.ArrayList;

public class Test extends TestToRun {

    SumoTraciConnection conn;
    Simulation sim;

    public Test(Simulation sim) {
        conn = new SumoTraciConnection(Simulation.SUMO_BIN, Simulation.TEST_CONFIG);
        this.sim = sim;
    }

    //Setup before main loop begins
    protected void beforeLoop() throws Exception {
        //Creating a starting node
        SumoStringList listExample = new SumoStringList();
        ArrayList<String> edgeList = new ArrayList<>();
        edgeList.add("46538375#6");
        listExample.addAll(edgeList);
        conn.do_job_set(Route.add("startNode", listExample));

        //Adding in vehicle
        conn.do_job_set(Vehicle.add("testVeh", "car", "startNode", 0, 1, 1, (byte) 0));

        //GUI tracking vehicle and zoom
        conn.do_job_set(Gui.trackVehicle("View #0", "testVeh"));
        conn.do_job_set(Gui.setZoom("View #0", (Double.parseDouble(conn.do_job_get(Gui.getZoom("View #0")).toString()))* Simulation.ZOOM_FACTOR));

        //Changing the target of the vehicle to another edge
        conn.do_job_set(Vehicle.changeTarget("testVeh", "569345537#2"));

        //Setting efforts of edges
        conn.do_job_set(Edge.setEffort("46538375#8", 1));
        conn.do_job_set(Edge.setEffort("196116976#7", 2));
    }

    protected void afterLoop() {

    }

    protected void duringLoop(int i) throws Exception {
        if(i == 10) {
            testVehicleSetEffort(conn, "testVeh", "46538375#8");

            conn.do_job_set(Vehicle.rerouteEffort("testVeh"));
        }

        conn.do_timestep();
    }

    private void testVehicleSetEffort(SumoTraciConnection conn, String vehID, String edgeID) throws Exception {
        double edgeEffortDouble = (Double) conn.do_job_get(Edge.getEffort(edgeID, sim.getCurrentTime()));
        conn.do_job_set(Vehicle.setEffort(vehID, Simulation.START_TIME, Simulation.END_TIME, edgeID, edgeEffortDouble));

        System.out.println("Vehicle effort for " + vehID + " on edge " + edgeID + " at time " + sim.getCurrentTime() + ": " + conn.do_job_get(Vehicle.getEffort(vehID, sim.getCurrentTime(), edgeID)));
    }

    protected SumoTraciConnection getConn() {
        return conn;
    }

}
