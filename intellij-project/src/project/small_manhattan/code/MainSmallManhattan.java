package project.small_manhattan.code;

import de.tudresden.sumo.cmd.Vehicle;
import it.polito.appeal.traci.SumoTraciConnection;

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


            conn.do_job_set(Vehicle.add("veh", "car", "s1", 0, 2, 1, (byte) 0));
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
