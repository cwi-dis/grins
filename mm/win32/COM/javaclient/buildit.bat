set path=C:\jdk1.4\bin;%path%
javac   grins/*.java grins/demo/*.java grins/player/*.java
jar cvf grinsp.jar grins/*.class grins/demo/*.class grins/player/*.class
move grinsp.jar bin
javah grins.GRiNSPlayer
javah grins.GRiNSPlayerMonitor
