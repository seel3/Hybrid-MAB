import os, time;

runs = 10
file = "run_attack.py"
total = []


for i in range(runs):
    # get start time
    start = time.time()

    # execute attack and end when done
    os.system("python run_attack.py")

    # get stop time
    stop = time.time()

    total.append(stop-start)
    
    
    
print("\n")
print("\n")
print("\n")
print("Execution time per run:")
print(total)
print("\n")
print("Average execution time:")
print(sum(total)/runs)

helper = ""
j = 1
for item in total:
    helper = helper + f"Run {j}: {item} sec\n"
    j += 1

f = open("results.txt", "a")
f.write(
f"""
Individual execution time: 
------------------------------------------------
{helper}


Average execution time:
{sum(total)/runs}
"""
)
f.close()