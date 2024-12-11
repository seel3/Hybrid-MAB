import os, time;

runs = 10
file = "run_attack.py"
total = []

# start vm  
#os.system(f"virsh start win11")


for i in range(runs):
    # mount share
    os.system(f"sudo mount -t cifs -o username=mlvalidator,domain=MYDOMAIN,uid=1000 //192.168.100.192/share/ /home/seel3/share/")
    
    # get start time
    start = time.time()

    # execute attack and end when done
    os.system("sudo docker run -ti -v /home/seel3/share:/root/MAB-malware/data/share eval_container")

    # get stop time
    stop = time.time()
    
    # unmount share
    os.system(f"sudo umount /home/seel3/share/")
    
    # reset vm with qemu agent
    os.system(f"virsh snapshot-revert win11 init")

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