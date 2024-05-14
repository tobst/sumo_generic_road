#!/bin/bash

#Script
#     BatchProcess
#
#Description
#     Replace Sumo sim- parameters and evaluate overtaking distance and trip duration
#
#------------------------------------------------------------------------------

set -x

# List of variables to replace in file1 and file2
# This is strict pairs. Avoid using different number of elements in each list
lateral_resolution_list=("0.5" "2.5")
minGapLat_list=("0.5" "1.5")
length=${#lateral_resolution_list[@]}

probability_list=("0.01" "0.02" "0.04" "0.06" "0.08" "0.1" "0.2" "0.3" "0.4")
modal_bike_split_list=("0.0" "0.05" "0.1" "0.2" "0.3" "0.4" "0.5")

cp net.net.xml generated/

# Define a function to process a single combination of parameters
process_combination() {
    lateral_resolution=$1
    minGapLat=$2
    probability=$3
    modal_bike_split=$4


    # Get the absolute path to the current directory
    script_dir=/data/HLRS/sumo_test/sublane_model_4_4

    # Copy the file1 and file2 to a new file
    cp $script_dir/test.sumocfg $script_dir/generated/test_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.sumocfg
    cp $script_dir/input_routes.rou.xml $script_dir/generated/input_routes_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.rou.xml
    cd $script_dir/generated
    # Replace lateral-resolution
    sed -i "s/<lateral-resolution value=\"1.65\"\/>/<lateral-resolution value=\"$lateral_resolution\"\/>/g" test_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.sumocfg
    #replace input_route-filename
    sed -i "s/input_routes.rou.xml/input_routes_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.rou.xml/g" test_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.sumocfg
    # Replace minGapLat
    sed -i "s/<minGapLat value=\"1.5\"\/>/<minGapLat value=\"$minGapLat\"\/>/g" input_routes_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.rou.xml
    # Replace probability for flows
    sed -i "/flow/ s/probability=\"0.05\"/probability=\"$probability\"/g" input_routes_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.rou.xml

    # Replace modal split
    sed -i "/vType/ s/probability=\"0.1\"/probability=\"$modal_bike_split\"/g" input_routes_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.rou.xml
    sed -i "/vType/ s/probability=\"0.9\"/probability=\"$(echo "1-$modal_bike_split" | bc)\"/g" input_routes_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.rou.xml

    # Run the program
    sumo --output-prefix test_$lateral_resolution-$minGapLat-$probability-$modal_bike_split- -c test_$lateral_resolution-$minGapLat-$probability-$modal_bike_split.sumocfg
    python $script_dir/analyse_fcd.py test_$lateral_resolution-$minGapLat-$probability-$modal_bike_split-fcd.xml
    cd $script_dir
}

export -f process_combination

# Loop over all pairs of lateral_resolution and minGapLat
for ((i=0; i<$length; i++)); do
    lateral_resolution=${lateral_resolution_list[$i]}
    minGapLat=${minGapLat_list[$i]}
    for probability in "${probability_list[@]}"; do
        for modal_bike_split in "${modal_bike_split_list[@]}"; do
            # Run the function in the background with GNU Parallel
            echo "$lateral_resolution $minGapLat $probability $modal_bike_split"
        done
    done
done | parallel -j7 --colsep ' ' process_combination
