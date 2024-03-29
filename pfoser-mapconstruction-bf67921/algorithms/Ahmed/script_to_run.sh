#To Compile:
CODE_PATH="." #path to the MapConstruction folder.
cd $CODE_PATH
javac -d bin/ src/mapconstruction2/*.java

#To Run:
INPUT_PATH="/home/peyman/Documents/projects/balad/codes/data/gps-csv/sample-new" #path to the folder that constains all input tracks
OUTPUT_PATH="/home/peyman/Documents/projects/balad/codes/results/ahmed" #path to the folder where output will be written
EPS=150.0 #epsilon in meters
HAS_ALTITUDE=true #if input file has altitude information
ALT_EPS=4.0 #minimum altitude difference in meters between two streets

java -cp bin/ mapconstruction2.MapConstruction $INPUT_PATH $OUTPUT_PATH $EPS $HAS_ALTITUDE $ALT_EPS
