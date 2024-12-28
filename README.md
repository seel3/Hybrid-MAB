# Hybrid-MAB
This is the github repo for masterproject "Machine Learning-Assisted Modification of PE
Malware for Antivirus Evasion"

The goal of this project is to create evasive malware samples using the multi armed bandit approach proposed by [song et. al](https://github.com/bitsecurerlab/MAB-malware).

This project extends the functionality of the MAB Malware Project by introducing a "hybrid mode" in which local av models like ember/malcov and defender are simontaneously queried in order to enhance performance while maintaining the same effectiveness.


## Hybrid Mode
Hybrid Mode has the same target as the av mode: an antivirus solution run inside a vm. However, the av mode took significantly longer (~3.6 times) than the model mode using ember/malconv. 

This is due to the fact that the av mode requires timeconsuming I/O operations as well as a certain scan period that is longer than that of ember/malconv.

To tackle this Problem the Hybrid Mode uses primarely the model to detect wether a sample is malicious or benign. Whenever the model can not determine if the sample is malware or not with a certanty above a fixed threshold, the av model is queried instead.



## TODO
* should a final scan using the av for a sample be done before it is minimized and should minimzation also be done only with the av?
* Thompson Sampling does not work and throws errors
* AV querying could be done using AMSI instead of just dropping the files on disk. This could be achieved by a client/server architecture where the rewriter can query amsi directly and get immediate feedback about a sample
* Check if parameters can be optimized (max concurrent samples etc.) to optimize performance or evasion rate
* evaluate ember vs. AV vs. hybrid mode
