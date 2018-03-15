package project.code;

import de.tudresden.sumo.cmd.Simulation;
import de.tudresden.sumo.cmd.Vehicle;
import it.polito.appeal.traci.SumoTraciConnection;

public class Main {

    public static final String NORMAL_CONFIG = "src/project/configuration_files/config.cfg";
    public static final String LITE_CONFIG = "src/project/configuration_files/config_lite.cfg";

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

            for(int i=0; i<3600; i++){
                System.out.println("hello");
                conn.do_timestep();
            }

            //stop TraCI
            conn.close();

        }catch(Exception ex){ex.printStackTrace();}

    }

}
