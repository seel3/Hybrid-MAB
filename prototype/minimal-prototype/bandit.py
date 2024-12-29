import copy
from scipy.stats import beta
from utils import *
from arm import *


class Bandit:
    def __init__(self):
        self.samples_manager = None
        self.list_arm = []
        self.list_arm.append(ArmOA(0))
        self.list_arm.append(ArmSA(1))
        self.list_arm.append(ArmSP(2))
        self.list_arm.append(ArmSR(3))
        self.list_arm.append(ArmRD(4))
        self.list_arm.append(ArmRC(5))
        self.list_arm.append(ArmBC(6))
        self.list_arm.append(ArmCR(7))
        self.idx_to_ori_idx = {}

        # Bayesian UCB
        self.c = 3
        self._as = [1] * len(self.list_arm)
        self._bs = [1] * len(self.list_arm)
        
        # used ONCE_ONLY arm
        self.used_once_only_arm_idxs = set()
        self.random_arm_count = 0

    
    def get_next_arm(self, sample, list_action, rand=False):
        """Function to get the next arm/modification to apply to the sample.

        Args:
            sample (Sample): The sample that modifications should be applied to
            list_action (list): list of possible actions
            rand (bool, optional): Random arm selection. Defaults to False.

        Raises:
            ValueError: _description_
            RuntimeError: _description_

        Returns:
            Arm: Selected arm
        """
        cr_path = Utils.get_randomized_folder() + Utils.get_ori_name(sample.path) + '.CR'
        
        # 50% chance to use CR action if .CR exists for the first action 
        if len(list_action) == 0 and os.path.exists(cr_path) and random.randint(0, 1) == 1: 
            idx = 7
        else:
            # Random Arm selection
            if rand:
                idx = random.randint(0, 6)
            else:
                while True:
                    # Tompson Sampling
                    samples = [np.random.beta(self._as[x], self._bs[x]) for x in range(len(self.list_arm))]
                    
                    # TODO: fix Tompson sampling list index out of range error when Tompson sampling is enabled through config
                    # Error:   
                    """
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
                    """

                    
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
                        debug()
                        raise RuntimeError("Index out of range during max calculation. Check list lengths and initialization.")

                    # Validate the selected index against conditions
                    if idx not in [4, 5, 6, 7] \
                            or (idx == 4 and 'RD' not in list_action) \
                            or (idx == 5 and 'RC' not in list_action) \
                            or (idx == 6 and 'BC' not in list_action):
                        break
                    
        # copy the selected arm and return it
        arm = copy.deepcopy(self.list_arm[idx])
        return arm

    def update_reward_with_alpha_beta(self, idx, alpha, beta):
        """Function to update the reward of an arm with the given alpha and beta values.

        Args:
            idx (int): Index of the arm to update
            alpha (int): Alpha value
            beta (int): Beta value
        """
        logger_rew.info('update_reward_with_alpha_beta: update %d with alpha: %d beta: %d' % (idx, alpha, beta))
        
        # Thompson Sampling is disabled -> return
        # TODO: list index errror from get_next_arm() could be also in here
        if Utils.is_thompson_sampling() == False:
            return

        # Bayesian UCB
        # Update Gaussian posterior
        if idx >= len(self._as): #TODO
            print(idx, len(self._as))
        self._as[idx] += alpha
        self._bs[idx] += beta

        if Utils.get_update_parent():
            # if child succ, give ori reward too!
            if alpha == 1:
                if idx in self.idx_to_ori_idx:
                    ori_idx = self.idx_to_ori_idx[idx]
                    self._as[ori_idx] += alpha

    def add_new_arm(self, new_arm):
        """function to add a new arm to the bandits when a new specific machine is found

        Args:
            new_arm (arm): Arm to add to the existing arms of a bandit
        """
        # Thompson Sampling is disabled -> return
        # TODO: list index errror from get_next_arm() could be also in here
        if Utils.is_thompson_sampling() == False:
            return
        # original index of arm
        ori_idx = new_arm.idx
        # update new arm index
        new_arm.idx = len(self.list_arm)
        self.idx_to_ori_idx[new_arm.idx] = ori_idx

        # find existing arm
        new_arm.update_description()
        for idx, arm in enumerate(self.list_arm):
            # arm already exist, update existing arm
            if arm.description == new_arm.description:    
                logger_rew.info('no need to add a new arm, update existing arm')
                self._as[idx] += 1
                return
            
        # add new arm
        self.list_arm.append(new_arm)
        self._as.append(1)
        self._bs.append(1)
