import os, time;

runs = 10
file = "run_attack.py"
total = []

for i in range(runs):

    # TODO: start vm
    
    # TODO: mount share


    # get start time
    start = time.time()

    #os.system("docker run -ti wsong008/mab-malware bash")

    #os.system(f"python {file}")

    # get stop time
    stop = time.time()
    
    # TODO: unmount share
    # TODO: reset vm with qemu agent
    

    print(i)
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