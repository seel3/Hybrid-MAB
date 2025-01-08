# Hybrid-MAB
This is the github repo for masterproject "Machine Learning-Assisted Modification of PE
Malware for Antivirus Evasion"

The goal of this project is to create evasive malware samples using the multi armed bandit approach proposed by [song et. al](https://github.com/bitsecurerlab/MAB-malware).

This project extends the functionality of the MAB Malware Project by introducing a "hybrid mode" in which local av models like ember/malcov and defender are simontaneously queried in order to enhance performance while maintaining the same effectiveness.


## Hybrid Mode
Hybrid Mode has the same target as the av mode: an antivirus solution run inside a vm. However, the av mode took significantly longer (~3.6 times) than the model mode using ember/malconv. 

This is due to the fact that the av mode requires timeconsuming I/O operations as well as a certain scan period that is longer than that of ember/malconv.

To tackle this Problem the Hybrid Mode uses primarely the model to detect wether a sample is malicious or benign. Whenever the model can not determine if the sample is malware or not with a certanty above a fixed threshold, the av model is queried instead.





## Meeting 09.01.2025
* Prototyp funktioniert
    * Kurze Erklärung/Vorführung
    * Zeitstand bei 300 Stunden
* Dokumentation ist vollständig
    * Code ist ausführlich kommentiert
    * Erklärung der Oberflächlichen Fnktionsweise in Documentation/Prototype
    * Erklärung der Infrastruktur unter Documentation/Infrastructure
    * Bereits bekannte Overview in State of the Art.pdf
* Was soll bis zur Abgabe noch gemacht werden/Soll überhaupt noch was gemacht werden?
* Todos aus meiner Sicht welche in der Zeit machbar wären:
    * Erstellen eines eigenständigen Docker images und hochladen auf Dockerhub
        * Modelle und Malware Samples aktuell nur in MAB-malware image. WEnn image weg dann alles weg
        * GPU support funktioniert nicht in Mab-malware image aufgrund falscher libraries -> fix in eigenem Image
    * Finden einer guten Konfiguration aller Parameter:
        * Thresholds sollten so gesetzt werden, dass Anzahl von minimalen Samples ca. gleich ist wie bei AV (aber performance sollte um einiges besser sein)
        * Anschließend können parameter wie scan time, Epochen usw abgeändert werden um Anzahl von minimalen Samples zu erhöhen
    * Besprechen der TODO's im Code
        * Thompson Sampling funktioniert immer noch nicht. (Fehlerhafte Implementierung?) 
            
            Unwahrscheinlich dass das in restlicher Zeit zu fixen ist. 
            
            Problem tritt teils auch in UCB auf, hier kommt es zu einem endlos loop.

            Problem könnte die scan_folder_time sein. (Zu niedrig? -> AV löscht sample nachdem es in sample manager bereits als evasive geführt wurde?)

            Funktioniert aber auch ohne sehr gut und kann in config deaktiviert werden.

        * In der minimierungs prozedur(sprich nach erfolgreicher evasiveness): sollte hier nur mehr mit der av gearbeitet werden oder weiterhin hybrid? Grundsätzlich will ich ja dass das ganze gegen die AV minimieren. 
            
            Könnte dazu führen dass zwar der minimierungsprozess langsamer wird aber dafür kann es keine false negatives geben.

## TODO
* create a stable environment that enables GPU usage (base on MAB container or start from scratch?)
    * Retrain Ember with lief 12.3 or only update torch in the original container, so it can use the gpu?
        * Retraining ember could be complicated because i don't have the original samples. Lief version is therefore a Problem.
        * Updating torch to enable GPU support works fine so far
    * add benign content from data to data folder of container
    * create a requirements.txt that is not causing problems
    * ensure that torch/lighbgm can use GPU
    * rewrite Dockerfile to use ubuntu/debian base image instad ob MAB-malware image
* should a final scan using the av for a sample be done before it is minimized and should minimzation also be done only with the av?
    * It could be sufficient to make the minimizer scans av only and not hybrid. 
    * Is this really nessecary?
* Thompson Sampling does not work and throws errors
    * This sometimes also applies to UCB. Here the reward propagation is just stuck in an endless loop.
    * Only ocurrs with AV scan
        * Maybe scan time is too low/high?
* AV querying could be done using AMSI instead of just dropping the files on disk. This could be achieved by a client/server architecture where the rewriter can query amsi directly and get immediate feedback about a sample. 
* Check if parameters can be optimized (max concurrent samples etc.) to optimize performance or evasion rate
* evaluate ember vs. AV vs. hybrid mode
