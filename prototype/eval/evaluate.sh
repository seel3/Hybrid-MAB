#!/bin/bash

runs=10
count_evasive=()
count_minimal=()
total=()

# Create results.txt or clear if it exists
> results.txt

echo "Starting runs..."

for ((i=1; i<=runs; i++)); do
    echo "Run $i/$runs"

    # Get start time
    start=$(date +%s)

    # Execute attack
    /usr/bin/python3 /root/minimal-prototype/run_attack.py

    # Get stop time
    stop=$(date +%s)

    # Calculate elapsed time
    elapsed=$((stop - start))
    total+=("$elapsed")

    # Count files in "output/evasive" and "output/minimal"
    evasive_count=$(ls output/evasive | wc -l)
    minimal_count=$(ls output/minimal | wc -l)

    count_evasive+=("$evasive_count")
    count_minimal+=("$minimal_count")

    # Cleanup
    rm -rf data/share/av/*

done

# Print results to terminal
echo "\n"
echo "-----------------------------------------------"
echo "-------------------DONE------------------------"
echo "-----------------------------------------------"
echo "\n"
echo "Execution time per run:"
printf "%s\n" "${total[@]}"
echo "\n"
echo "Average execution time:"
average_time=$(awk "BEGIN {sum=0; for (i=0; i<${#total[@]}; i++) sum+=${total[i]}; print sum/${#total[@]}}")
echo "$average_time"
echo "\n"
echo "Evasive samples:"
printf "%s\n" "${count_evasive[@]}"
echo "\n"
echo "Average Evasive count:"
average_evasive=$(awk "BEGIN {sum=0; for (i=0; i<${#count_evasive[@]}; i++) sum+=${count_evasive[i]}; print sum/${#count_evasive[@]}}")
echo "$average_evasive"
echo "\n"
echo "Minimal samples:"
printf "%s\n" "${count_minimal[@]}"
echo "\n"
echo "Average Minimal count:"
average_minimal=$(awk "BEGIN {sum=0; for (i=0; i<${#count_minimal[@]}; i++) sum+=${count_minimal[i]}; print sum/${#count_minimal[@]}}")
echo "$average_minimal"

# Prepare detailed report
helper=""
for ((j=0; j<${#total[@]}; j++)); do
    helper+="Run $((j+1)): ${total[j]} sec\n"
done

helper2=""
for ((j=0; j<${#count_evasive[@]}; j++)); do
    helper2+="Run $((j+1)): ${count_evasive[j]} Evasive Samples\n"
done

helper3=""
for ((j=0; j<${#count_minimal[@]}; j++)); do
    helper3+="Run $((j+1)): ${count_minimal[j]} Minimal Samples\n"
done

# Write results to results.txt
cat <<EOL >> results.txt

Average execution time:
$average_time

Average evasive count:
$average_evasive

Average minimal count:
$average_minimal



Individual execution time: 
------------------------------------------------
$helper



Individual evasive count: 
------------------------------------------------
$helper2



Individual minimal count: 
------------------------------------------------
$helper3

EOL

echo "Results written to results.txt"