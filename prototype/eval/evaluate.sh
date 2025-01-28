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
    /usr/bin/python3 /root/Hybrid-MAB/run_attack.py

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
    rm -rf output/minimal/*
    rm -rf output/evasive/*

done

# Print results to terminal
echo "
"
echo "-----------------------------------------------"
echo "-------------------DONE------------------------"
echo "-----------------------------------------------"
echo "
"
echo "Execution time per run:"
printf "%s\n" "${total[@]}"
echo "
"

# Average execution time
sum_total=0
for t in "${total[@]}"; do
    sum_total=$((sum_total + t))
done
average_time=$(echo "scale=2; $sum_total / ${#total[@]}" | bc)
echo "Average execution time:"
echo "$average_time"
echo "
"

# Evasive samples
echo "Evasive samples:"
printf "%s\n" "${count_evasive[@]}"
echo "
"

# Average evasive count
sum_evasive=0
for e in "${count_evasive[@]}"; do
    sum_evasive=$((sum_evasive + e))
done
average_evasive=$(echo "scale=2; $sum_evasive / ${#count_evasive[@]}" | bc)
echo "Average Evasive count:"
echo "$average_evasive"
echo "
"

# Minimal samples
echo "Minimal samples:"
printf "%s\n" "${count_minimal[@]}"
echo "
"

# Average minimal count
sum_minimal=0
for m in "${count_minimal[@]}"; do
    sum_minimal=$((sum_minimal + m))
done
average_minimal=$(echo "scale=2; $sum_minimal / ${#count_minimal[@]}" | bc)
echo "Average Minimal count:"
echo "$average_minimal"
echo "
"

# Prepare detailed report
helper=""
for ((j=0; j<${#total[@]}; j++)); do
    helper+="Run $((j+1)): ${total[j]} sec
    "
done

helper2=""
for ((j=0; j<${#count_evasive[@]}; j++)); do
    helper2+="Run $((j+1)): ${count_evasive[j]} Evasive Samples
    "
done

helper3=""
for ((j=0; j<${#count_minimal[@]}; j++)); do
    helper3+="Run $((j+1)): ${count_minimal[j]} Minimal Samples
    "
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
