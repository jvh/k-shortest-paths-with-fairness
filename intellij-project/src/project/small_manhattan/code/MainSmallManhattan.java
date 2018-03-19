package project.small_manhattan.code;

import de.tudresden.sumo.cmd.Route;
import de.tudresden.sumo.cmd.Vehicle;
import de.tudresden.sumo.config.Constants;
import de.tudresden.sumo.util.Sumo;
import de.tudresden.ws.container.SumoStringList;
import it.polito.appeal.traci.SumoTraciConnection;

import java.util.ArrayList;

public class MainSmallManhattan {

    public static final String NORMAL_CONFIG = "src/project/small_manhattan/configuration_files/config.cfg";
    public static final String LITE_CONFIG = "src/project/configuration_files/config_lite.cfg";
    public static final String TEST_CONFIG = "src/project/configuration_files/config_test.cfg";

    static String sumo_bin = "D:/Program Files/SUMO/bin/sumo-gui.exe";
    static final String config_file = NORMAL_CONFIG;


    public static void main(String[] args) {

        //start Simulation
        SumoTraciConnection conn = new SumoTraciConnection(sumo_bin, config_file);

        //set some options
        conn.addOption("step-length", "0.1"); //timestep 100 ms

        try{

            //start TraCI
            conn.runServer();

            //load routes and initialize the simulation
            conn.do_timestep();

            SumoStringList hello = new SumoStringList();
            ArrayList<String> als = new ArrayList<>();

            als.add("452322756#0");
            als.add("452322756#1");
            als.add("452322756#2");

            hello.addAll(als);

            conn.do_job_set();


            conn.do_job_set(Route.add("test", hello));

            System.out.println(conn.do_job_get(Route.getEdges("test")));

            conn.do_job_set(Vehicle.add("veh", "car", "test", 0, 2, 1, (byte) 0));

            conn.do_job_set(Vehicle.add("veh2", "car", "s1", 0, 2, 1, (byte) 0));
            System.out.println(conn.do_job_get(Vehicle.getBestLanes("veh")));
//            Collection<Vehicle> vehicles = conn.



            for(int i=0; i<3600; i++){
                conn.do_timestep();
            }

            //stop TraCI
            conn.close();

        }catch(Exception ex){ex.printStackTrace();}

    }

}
