# Prototype

## Basic Concept

## Implementation

## Improvement
A possible Improvement could be to partially substitute defender. Depending on how long it takes to query defender it could be beneficial to only query defender whenever the substitute model confidence crosses a certain threshold. 

For example: 
* Substitue model says sample is 60% malicious or below -> query defender.
* Above 60% defender does not have to be queried




## Problems

### List index error in Thompson sampling:

The function `get_next_arm` produced the following error during the attack on Windoww defender:

```
Exception in thread Thread-1:
Traceback (most recent call last):
File "/usr/lib/python3.6/threading.py", line 916, in _bootstrap_inner
    self.run()
File "/usr/lib/python3.6/threading.py", line 864, in run
    self._target(*self._args, **self._kwargs)
File "/root/MAB-malware/rewriter_MAB.py", line 61, in run
    arm = self.bandit.get_next_arm(sample, sample.get_applied_actions(), rand=self.rand)
File "/root/MAB-malware/bandit.py", line 98, in get_next_arm
    idx = max(range(len(self.list_arm)), key=lambda x: samples[x])
File "/root/MAB-malware/bandit.py", line 98, in <lambda>
    idx = max(range(len(self.list_arm)), key=lambda x: samples[x])
IndexError: list index out of range
```

Fixed this by disabeling thompson sampeling in general. 