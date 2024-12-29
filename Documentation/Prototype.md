# Prototype
The goal of this project is to create evasive malware samples using the multi armed bandit approach proposed by [song et. al](https://github.com/bitsecurerlab/MAB-malware).

## Concept


## Implementation
### Arms
All possible modifications of a pe-file are implemented as an arm of a bandit (e.g. ArmOA = overlay append). All arms inherit the same methods as their parent class Arm:
* transfer: defines how the modification of a sample will happen 
* pull: will apply the modification defined in transfer
* helper functions: will provide functionality to calculate offsets, free space within a section, etc.


### Bandit
A Bandit is a collection of different arms. It provides functionality to apply modifications to a sample depending on rewards associated with the modification (get_next_arm) as well as functionality to propergate the rewards from scans by the classifier(update_reward_with_alpha_beta). The Bandit has also the functionality to create new arms (specific machines) from old arms (generic machines) that performed well(add_new_arm).

### Sample
A Sample represents a malware binary and stores important imformation about it such as:
* path to the sample
* results from classifier scans
* a list of arms that are currently applied to it
* ...

It provides functionality to check its scan status and update it if nessecary as well as functionality that is beeing used by the rewriter and minimizer to interact with the arms to the sample.

### Sample Manager
The sample manager is a container for all samples that are currently beeing handeled by the program and provides a queue for the rewriter/minimizer to get samples from. It organizes the samples in lists depending on their current status (e.g. evasive, pending analysis, etc).  It also provides helper functionalities such as counting samples with different statuses.

### Rewriter
The rewriter starts as a own thread and will first query a analysis for all samples to perform an initial asessment wether a sample is malware or benign. Aftewards it will start a loop in which it pulls a sample from the sample manager queue, query the bandit to modify the sample and query the classifier to evaluate the sample.
It will periodically check for statuses of all samples and control the program folow depending on the feedback. Results are shown to the user in fixed intervals.

### Minimizer
The minimizer runs in its own thread from the start of the program. It will check if any samples are evasive and if so try to remove different arms from the sample and wether this removes the evasiveness from the sample. It will continue to do so until the rewriter sends an exit signal.


### Classifier
The classifier is checks samples inside a given folder. It has its own thread that gets started when the program is run. While there is no exit sign from one of the other components it will coninously scan the minimizer and rewriter folder with a given model. 
Depending on the results of a scan, an analysed file will either be deleted or moved to a folder conatining the evasive samples.

## Improvement
In order to increase performance of the prototype, a hybrid mode was introduced. In this mode, the av will only be queried, whenever the mal model is unable to determine if the sample is malware with a confidence of a crtain threshold.
This way the target remains the av, but trivial analysis is done by the more efficient model. 

In order to achive this, two analysis folders were introduced.
`data/share/rewriter/` is monitored by the model and the main folder that is beeing used.
Whenever the model can not say with a certainty above the configured threshold, weter a sample is malware or benign, it will get moved to the second folder.

The folder `data/share/av/` is a shared folder between the Windows vm and the ml server. Whenever a file is moved into this folder it is beeing scanned by the hosts Antivirus Software. 

Thresholds are beeing read directly from the config file via the parameters `upper_bound` and `lower_bound`.
If a sample recieves a score above `upper_bound` it will be immediatl be classified as benign and moved to the evasive sample folder. If the sample recieves a score below `lower_bound` it will be immediately classified as malicious and deleted. All other samples will be moved to the av folder for further analysis by the AV.
