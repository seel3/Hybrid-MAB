import os, time;

runs = 10
count_evasive = []
count_minimal = []
total = []


for i in range(runs):
    print(f"Run {i+1}/{runs}")
    # get start time
    start = time.time()

    # execute attack and end when done
    os.system("run_attack.py")
    # get stop time
    stop = time.time()
 
    count_evasive.append(len(os.listdir("output/evasive")))
    count_minimal.append(len(os.listdir("output/minimal")))

    total.append(stop-start)
    
    os.system("rm -rf data/share/av/")
    
    
    
print("\n")
print("-----------------------------------------------")
print("-------------------DONE------------------------")
print("-----------------------------------------------")
print("\n")
print("Execution time per run:")
print(total)
print("\n")
print("Average execution time:")
print(sum(total)/runs)
print("\n")
print("\n")
print("Evasive samples:")
print(count_evasive)
print("\n")
print("Average Evasive count:")
print(sum(total)/runs)
print("\n")
print("\n")
print("Minimal samples:")
print(count_minimal)
print("\n")
print("Average Minimal count:")
print(sum(count_minimal)/runs)

helper = ""
j = 1
for item in total:
    helper = helper + f"Run {j}: {item} sec\n"
    j += 1

helper2 = ""
for item in count_evasive:
    helper = helper + f"Run {j}: {item} Evasive Samples\n"
    j += 1
    
helper3 = ""
for item in count_minimal:
    helper = helper + f"Run {j}: {item} Evasive Samples\n"
    j += 1


f = open("results.txt", "a")
f.write(
f"""

Average execution time:
{sum(total)/runs}

Average evasive count:
{sum(count_evasive)/runs}

Average minimal count:
{sum(count_minimal)/runs}




Individual execution time: 
------------------------------------------------
{helper}



Individual evasive count: 
------------------------------------------------
{helper2}



Individual minimal count: 
------------------------------------------------
{helper3}


"""
)
f.close()