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

Possible fix:
```python
    def get_next_arm(self, sample, list_action, rand=False):
        # Bayesian UCB
        # list_value = [self._as[x] / float(self._as[x] + self._bs[x]) + beta.std(
        #        self._as[x], self._bs[x]) * self.c for x in range(len(self.list_arm))]
        #
        # logger_rew.info(list_value)
        #max_value = max(list_value)
        #list_max_value_idx = []
        # for idx, i in enumerate(list_value):
        #    if i == max_value:
        #        list_max_value_idx.append(idx)
        #idx = random.choice(list_max_value_idx)

        #print('list_action:', list_action)
        cr_path = Utils.get_randomized_folder() + Utils.get_ori_name(sample.path) + '.CR'
        if len(list_action) == 0 and os.path.exists(cr_path) and random.randint(0, 1) == 1: # 50% chance to use CR action if .CR exists for the first action 
            idx = 7
        else:
            if rand:
                idx = random.randint(0, 6)
            else:
                while True:
                    # Tompson Sampling
                    samples = [np.random.beta(self._as[x], self._bs[x]) for x in range(len(self.list_arm))]
                    
                    # Make a local copy of list_arm to avoid concurrent modification issues
                    list_arm = self.list_arm[:] 

                    # Check for consistent sizes
                    if len(self._as) != len(list_arm) or len(self._bs) != len(list_arm):
                        raise ValueError("Mismatch in lengths: self.list_arm, self._as, and self._bs must have the same size.")

                    # Generate samples
                    samples = [np.random.beta(self._as[x], self._bs[x]) for x in range(len(list_arm))]

                    # Find the index of the maximum sample value
                    try:
                        idx = max(range(len(list_arm)), key=lambda x: samples[x])
                    except IndexError:
                        raise RuntimeError("Index out of range during max calculation. Check list lengths and initialization.")

                    # Validate the selected index against conditions
                    if idx not in [4, 5, 6, 7] \
                            or (idx == 4 and 'RD' not in list_action) \
                            or (idx == 5 and 'RC' not in list_action) \
                            or (idx == 6 and 'BC' not in list_action):
                        break

        arm = copy.deepcopy(self.list_arm[idx])
        return arm

```