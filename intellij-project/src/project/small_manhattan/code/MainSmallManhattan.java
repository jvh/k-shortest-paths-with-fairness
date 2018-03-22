package project.small_manhattan.code;

import de.tudresden.sumo.cmd.*;
import de.tudresden.sumo.util.Sumo;
import de.tudresden.ws.Traci;
import de.tudresden.ws.container.SumoStringList;
import it.polito.appeal.traci.SumoTraciConnection;

import java.util.ArrayList;

public class MainSmallManhattan {

    public static final String NORMAL_CONFIG = "src/project/small_manhattan/configuration_files/config.cfg";
    public static final String LITE_CONFIG = "src/project/configuration_files/config_lite.cfg";
    public static final String TEST_CONFIG = "src/project/configuration_files/config_test.cfg";

    //Simulation start and end times
    public static final int START_TIME = 0;
    public static final int END_TIME = 100000;
    //Zoom factor for GUI
    public static final int ZOOM_FACTOR = 12;

    public static final String SUMO_BIN = "D:/Program Files/SUMO/bin/sumo-gui.exe";
    public static final String CONFIG_FILE = NORMAL_CONFIG;

    public static final SumoTraciConnection SUMO_CONN = new SumoTraciConnection(SUMO_BIN, CONFIG_FILE);

    public static void main(String[] args) {
        MainSmallManhattan msm = new MainSmallManhattan();
        SumoTraciConnection conn = msm.SUMO_CONN;

        //Changing the timestep to be 0.1s
        conn.addOption("step-length", "0.1");
        conn.addOption("device.rerouting.probability", "1.0");
        conn.addOption("routing-algorithm", "dijkstra");

        try{
            //Start Traci
            conn.runServer();
            //Initialise the simulation & load routers + vehicles
            conn.do_timestep();

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
            conn.do_job_set(Gui.setZoom("View #0", (Double.parseDouble(conn.do_job_get(Gui.getZoom("View #0")).toString()))*ZOOM_FACTOR));

            //Changing the target of the vehicle to another edge
            conn.do_job_set(Vehicle.changeTarget("testVeh", "569345537#2"));

            //Setting efforts of edges
            conn.do_job_set(Edge.setEffort("46538375#8", 1));
            conn.do_job_set(Edge.setEffort("196116976#7", 2));


            //Running for the duration of the simulation
            for(int i = START_TIME; i < END_TIME; i++){
                if(i == 10) {
                    msm.testVehicleSetEffort(conn, "testVeh", "46538375#8");

                    conn.do_job_set(Vehicle.rerouteEffort("testVeh"));
                }

                conn.do_timestep();
            }
            //stop TraCI
            conn.close();

        }catch (Exception e) {
            e.printStackTrace();
        }
    }

    //Returns the current time of the simulation in ms
    public static int getCurrentTime() throws Exception {
      return Integer.parseInt(SUMO_CONN.do_job_get(Simulation.getCurrentTime()).toString());
    }

    private void testVehicleSetEffort(SumoTraciConnection conn, String vehID, String edgeID) throws Exception {
        double edgeEffortDouble = Double.parseDouble(conn.do_job_get(Edge.getEffort(edgeID, getCurrentTime())).toString());
        conn.do_job_set(Vehicle.setEffort(vehID, START_TIME, END_TIME, edgeID, edgeEffortDouble));

        System.out.println("Vehicle effort for " + vehID + " on edge " + edgeID + " at time " + getCurrentTime() + ": " + conn.do_job_get(Vehicle.getEffort(vehID, getCurrentTime(), edgeID)));
    }

}
