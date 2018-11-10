# Fair _k_-Shortest Paths Re-Routing for Congestion Management

### Abstract
Traffic congestion in large cities is on the rise as urbanisation and economic growth rapidly increase.
Congestion cost U.K drivers over £37.7 billion in 2017, additionally to massive losses of time. Many congestion management techniques greedily shift drivers around congested areas with no concern of effects on future congestion on the road network. Furthermore, current systems may often cause frustration and are subsequently discontinued. This paper investigates the benefits of introducing fairness into congestion management systems and proposes a centralised approach to fairly alleviating congestion using existing prevalent path-finding algorithms, with the goal to reduce congestion over a road network. This project proposes a novel modification to existing $k$-shortest path algorithms, which doesn't currently take into account any measure of fairness. The system uses fairness metrics to proactively re-route vehicles through congested areas with minimal frustration for the driver.  Results gathered supported the conclusion that drivers experienced less re-routings and subsequently shorter journeys.

### Setup Guide

1. Ensure that you have Python 3.7 installed on your computer.
2. Install SUMO simulation software onto your computer. If using Windows, download the latest stable for Windows from http://sumo.dlr.de/wiki/Downloads. If using Mac, please refer to the below section *macOS SUMO Installation & Usage Guide* as this process is much more involved than a Windows installation. If using Linux, please refer to the Linux guide given on http://sumo.dlr.de/wiki/Installing in order to build your SUMO installation.

### macOS SUMO Installation & Usage Guide 
1. If you come from a previous macports installation you need to uninstall _SUMO_ and _fox_ toolkit first:  
 `sudo port uninstall sumo`  
 `sudo port uninstall fox`  

2. If you did not already install homebrew do it by invoking  
`ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"`  

3. make sure your homebrew db is up-to-date  
`brew update`  

4. Install dependencies  
`brew install Caskroom/cask/xquartz`  
`brew install autoconf`  
`brew install automake`  
`brew install pkg-config`  
`brew install libtool`  
`brew install gdal`  
`brew install proj`  
`brew install xerces-c`  
`brew install fox`  

5. Set necessary environment variables  
`export CPPFLAGS="$CPPFLAGS -I/opt/X11/include/"  
export LDFLAGS="-L/opt/X11/lib"`  

6. Get the source code and change to the appropriate directory  
`cd sumo-<version>`  

7. Run autoreconf  
`autoreconf -i`  

8. Run configure  
`./configure CXX=clang++ CXXFLAGS="-stdlib=libc++ -std=gnu++11" --with-xerces=/usr/local --with-proj-gdal=/usr/local`  

9. Build  
``make -j`sysctl -n hw.ncpu``  

10. Install  
`make install`  

11. After the installation you need to log out/in in order to let X11 start automatically, when calling a gui-based application like "sumo-gui". (Alternatively, you may start X11 manually by pressing cmd-space and entering "_XQuartz_").  

12. At this point, you’ll get an error when importing Traci, you must insert the SUMO tools into _PATH_ (or _PYTHONPATH_), this is done by putting the line … into the main Python module (where the main method is located)  
`sys.path.insert(1, ‘path_to_sumo_tools/sumo/tools')`.  

13. Set the _SUMO_HOME_ environment variable in Python code (same steps as 12).  
`os.environ["SUMO_HOME"] = “path_to_sumo_home/sumo"`  

14. (Alternative step) in macOS you can change the environmental variables in `~/.bash_profile`, in this you can add in a _SUMO_HOME_ variable.  

