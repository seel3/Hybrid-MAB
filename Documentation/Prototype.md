# Prototype
The goal of this project is to create evasive malware samples using the multi armed bandit approach proposed by [song et. al](https://github.com/bitsecurerlab/MAB-malware).

## Concept

## Implementation

## Improvement
In order to increase performance of the prototype, a hybrid mode was introduced. In this mode, the av will only be queried, whenever the mal model is unable to determine if the sample is malware with a confidence of a crtain threshold.
This way the target remains the av, but trivial analysis is done by the more efficient model. 

In order to achive this, two analysis folders were introduced.
`data/share/rewriter/` is monitored by the model and the main folder that is beeing used.
Whenever the model can not say with a certainty above the configured threshold, weter a sample is malware or benign, it will get moved to the second folder.

The folder `data/share/av/` is a shared folder between the Windows vm and the ml server. Whenever a file is moved into this folder it is beeing scanned by the hosts Antivirus Software. 

Thresholds are beeing read directly from the config file via the parameters `upper_bound` and `lower_bound`.
If a sample recieves a score above `upper_bound` it will be immediatl be classified as benign and moved to the evasive sample folder. If the sample recieves a score below `lower_bound` it will be immediately classified as malicious and deleted. All other samples will be moved to the av folder for further analysis by the AV.
