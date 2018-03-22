package project.small_manhattan.code;

import de.tudresden.sumo.cmd.*;
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

    public static final String SUMO_BIN = "D:/Program Files/SUMO/bin/sumo-gui.exe";
    public static final String CONFIG_FILE = NORMAL_CONFIG;


    public static void main(String[] args) {

        //start Simulation
        SumoTraciConnection conn = new SumoTraciConnection(SUMO_BIN, CONFIG_FILE);

        //set some options
        conn.addOption("step-length", "0.1"); //timestep 100 ms
//        conn.addOption("device.rerouting.probability", "1.0");
//        conn.addOption("routing-algorithm", "dijkstra");

        try{

            //start TraCI
            conn.runServer();



            //load routes and initialize the simulation
            conn.do_timestep();
            Traci traci = new Traci();



            //Printing out all the edges in the simulation
            SumoStringList edges = (SumoStringList) conn.do_job_get(Edge.getIDList());
            for(String edge: edges) {
//                System.out.println("edge " + edge);
            }

            SumoStringList listExample = new SumoStringList();
            ArrayList<String> edgeList = new ArrayList<>();

            edgeList.add("452322756#0");
//            edgeList.add("452322756#1");
//            edgeList.add("452322756#2");
            listExample.addAll(edgeList);



            conn.do_job_set(Route.add("test", listExample));

//            System.out.println(conn.do_job_get(Route.getEdges("test")));

//            conn.do_job_set(Vehicle.add("veh", "car", "test", 0, 2, 1, (byte) 0));

            conn.do_job_set(Vehicle.add("veh2", "car", "s1", 0, 1, 1, (byte) 0));

            conn.do_job_set(Gui.trackVehicle("View #0", "veh2"));

            conn.do_job_set(Vehicle.changeTarget("veh2", "569345537#2"));

            //Across
//            conn.do_job_set(Vehicle.setEffort("veh2", 0, END_TIME, "46538375#8", 9));
//
//            //Down
//            conn.do_job_set(Vehicle.setEffort("veh2", 0, END_TIME, "196116976#7", 3));
//            conn.do_job_set(Vehicle.setEffort("veh2", 0, END_TIME, "196116976#9", 2));
//            conn.do_job_set(Vehicle.setEffort("veh2", 0, END_TIME, "420908138#1", 7));


            conn.do_job_set(Edge.setEffort("46538375#8", 5));
            conn.do_job_set(Edge.setEffort("196116976#7", 2));
            


//            conn.do_job_set(Edge.setEffort("196116976#7", 1));

//            conn.do_job_set(Vehicle.rerouteEffort("veh2"));
            System.out.println("Current time: " + conn.do_job_get(Simulation.getCurrentTime()));

//            System.out.println("Effort " + conn.do_job_get(Edge.getEffort("46538375", 0)));

//            conn.do_job_set(Vehicle.rerouteEffort("veh2"));

//            System.out.println(conn.do_job_get(Vehicle.getBestLanes("veh")));
//            Collection<Vehicle> vehicles = conn.



            for(int i=START_TIME; i<END_TIME; i++){

                if(i==10) {
                    conn.do_job_set(Vehicle.rerouteEffort("veh2"));
                    System.out.println("Vehicle effort veh2: " + conn.do_job_get(Vehicle.getEffort("veh2", i, "196116976#7")));

                }

                conn.do_timestep();
            }

//            System.out.println(conn.do_job_get(Edge.getEffort("196116976#7", 10)));

            //stop TraCI
            conn.close();

        }catch(Exception ex){ex.printStackTrace();}

    }

}
