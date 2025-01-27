from utils import *
import random
from models import *
from sample import Sample
from arm import *
from pathlib import Path

class SamplesManager:
    """class to manage samples and provide functionality to interact with the samples
    """
    def __init__(self, sample_folder, bandit):
        """init class

        Args:
            sample_folder (path): Path to the folder containing the malwaresamples
            bandit (Bandit): A bandit object to manage the modification of the samples
        """
        # folder where samples are stored
        self.sample_folder = sample_folder
        # bandit object to manage the modification of the samples
        self.bandit = bandit
        # set the samples manager of the bandit to this object
        self.bandit.samples_manager = self

        # list of all samples
        self.list_sample = []
        # set the limit of concurrent samples that will be modified
        self.sample_concurrent_limit = Utils.get_max_working_sample_count()
        # get all samples from the sample folder and sort it
        list_file = glob.glob('%s*' %sample_folder)
        list_file.sort()
        # create a sample object from each file and add it to the list of samples
        for x in list_file:
            sample = Sample(x)
            self.list_sample.append(sample)
        

    def get_samples_with_status(self, status):
        """get samples with a certain status

        Args:
            status (int): Macro that defines the status of the sample

        Returns:
            sample[]: array of samples with the given status
        """
        return [ sample for sample in self.list_sample if sample.status == status ]

    def get_count_with_status(self, status):
        """get the ammount of samples with a certain status

        Args:
            status (int): Macro that defines the status of the sample

        Returns:
            int: Count of samples with the given status
        """
        count = 0
        for sample in self.list_sample:
            if sample.status == status:
                count += 1
        return count


    def get_next_sample(self):
        """function that retrieves the next sample from the list of samples with the status SAMPLE_STATUS_PENDING that have been pulled less than the maximum pull count
        
        This sample's status will then be set to SAMPLE_STATUS_WORKING

        Returns:
            sample: The sample that has been selected
        """
        # get all samples with status pending
        list_pending = self.get_samples_with_status(SAMPLE_STATUS_PENDING)
        # get max pull count
        max_pull_count = Utils.get_max_pull()
        # get all samples that have been pulled less than the max pull count from the list of pending samples
        list_pending = [x for x in list_pending if x.pull_count < max_pull_count]
        # if there are no samples left, return None
        if len(list_pending) > 0:
            # get the count of working samples
            count_working = self.get_count_with_status(SAMPLE_STATUS_WORKING)
            # if the count of working samples is more than the limit of concurrent samples, return None
            if count_working >= self.sample_concurrent_limit:
                logger_rew.info('concurrent sample %d is more than %d, waiting...' %(count_working, self.sample_concurrent_limit))
                return None
            else:
                # select a random sample from the list of pending samples
                sample = random.choice(list_pending)
                # set the status of the sample to working
                sample.status = SAMPLE_STATUS_WORKING
                # get the count of working samples
                count_working = self.get_count_with_status(SAMPLE_STATUS_WORKING)
                logger_rew.info('select pending sample: %s (pull_count:%d)' %(sample.sname, sample.pull_count))
                logger_rew.info('count_working: %d' %count_working)
                # return the selected sample
                return sample

    def get_initial_pending_list(self):
        """Performs initial check if the classifier can detect the original samples.
        Can be left as it is since the initial classification is only run once and always done by the model
        """
        logger_rew.info('check whether classifier can detect the original samples...')

        # copy all samples to the scan folder
        for sample in self.list_sample:
            sample.copy_to_scan_folder(rewriter_scan_folder)
        logger_rew.info('copy finish')
        # loop as long as there are samples that are not pending or skipped
        while(True):
            # loop through all samples
            for sample in self.list_sample:
                #if the sample has no status it has not been checked yet
                if sample.status == None:
                    # check the scan status of the sample
                    scan_status = sample.check_scan_status(rewriter_scan_folder)
                    # if the scan status is deleted, set the status of the sample to pending
                    if scan_status == SCAN_STATUS_DELETED:
                        sample.status = SAMPLE_STATUS_PENDING
                    # if the scan status is pass, set the status of the sample to skip
                    elif scan_status == SCAN_STATUS_PASS:
                        sample.status = SAMPLE_STATUS_SKIP
            # get the count of all samples
            count_all = len(self.list_sample)
            # set the count of pending and skipped samples to 0
            count_pending = count_skip = 0
            
            # loop through all samples again to count statuses
            for sample in self.list_sample:
                # if the status of the sample is pending, increase the count of pending/skipped samples
                if sample.status == SAMPLE_STATUS_PENDING:
                    count_pending += 1
                elif sample.status == SAMPLE_STATUS_SKIP:
                    count_skip += 1
            logger_rew.info('(%d/%d): detect %d, fail %d' %(count_pending + count_skip, count_all, count_pending, count_skip))
            # TODO: what is the purpose of this sleep? Can it bee removed orr will this lead to more computational load?
            time.sleep(2)
            # if all samples have been checked, break the loop
            if count_pending + count_skip == len(self.list_sample):
                break
        logger_rew.info('check finish.')
        logger_rew.info('remove remaining files.')
        # clear the scan folder
        os.system('rm -f %s/*' %rewriter_scan_folder)
   

    def update_working_list(self):
        """function to update the list of samples that are worked with currently
        """
        # get all samples with status working and create empty lists for failed and successful(evasive) modifications
        list_working = self.get_samples_with_status(SAMPLE_STATUS_WORKING)
        logger_rew.info('len list_working: %d' %len(list_working))
        list_fail = []
        list_succ = []

        # get sha256 of all samples to identify them by
        for sample in list_working:
            sha256 = Utils.get_ori_name(sample.path)

            # check where the sample is located (av/model folder) and scan it with the corresponding scanner
            if any(basename(sample.current_exe_path) in filename for filename in os.listdir(av_folder)):
                # av scan
                scan_status = sample.check_scan_status(av_folder) 
            else:
                # model scan
                scan_status = sample.check_scan_status(rewriter_scan_folder)
            # if any modification hs been applied to the sample add it to the lists of failed or evasive samples
            if len(sample.list_applied_arm) > 0:
                if scan_status == SCAN_STATUS_DELETED:
                    list_fail.append(sample)
                elif scan_status == SCAN_STATUS_PASS:
                    list_succ.append(sample)

        # loop through all failed samples
        for sample in list_fail:
            if len(sample.list_applied_arm) > 0:
                # get the last applied arm/modification
                last_arm = sample.list_applied_arm[-1]
                # update reward for the last arm beta +1
                self.bandit.update_reward_with_alpha_beta(last_arm.idx, 0, 1)
                # if the sample has been modified more or equal times than the maximum length, delete the modifications and the sample from disk
                if len(sample.list_applied_arm) >= sample.max_length:

                    logger_rew.info('restart: delete %s related arms and files on disk after max_length(%d) tries' %(sample.sname, sample.max_length))
                    sample.delete_applied_arm()
                    sample.delete_tmp_files(rewriter_output_folder)
                    sample.set_current_exe_path(sample.path)
                    
                # set the sample status to pending
                sample.status = SAMPLE_STATUS_PENDING
                
        # loop through all successful samples
        for sample in list_succ:
            # get the last applied arm/modification
            last_arm = sample.list_applied_arm[-1]
            # output the successful modification etc
            logger_rew.info('### Evade! %s (pull_count: %d)' %(sample.current_exe_path, sample.pull_count))
            logger_rew.info('%s exists: %d' %(sample.current_exe_path, os.path.exists(sample.current_exe_path)))
            logger_rew.info('mv %s %s' %(sample.current_exe_path, evasive_folder))
            
            # move the modified sample to the evasive folder
            os.system('mv %s %s' %(sample.current_exe_path, evasive_folder))
            # set the different paths of the sample to the new path in the evasive folder
            new_path = evasive_folder + basename(sample.current_exe_path)
            logger_rew.info('%s exists: %d' %(new_path, os.path.exists(new_path)))
            sample.evasive_path = evasive_folder + basename(sample.current_exe_path)
            sample.set_current_exe_path(sample.evasive_path)
            # remove the file all temp files from the scan folder
            os.system('rm -f %s%s' %(rewriter_scan_folder, basename(sample.current_exe_path)))
            sample.delete_tmp_files(rewriter_output_folder)
            
            # set the sample scan_status to deleted for minimization
            sample.scan_status = SCAN_STATUS_DELETED
            # set the sample status to evasive
            sample.status = SAMPLE_STATUS_EVASIVE
        logger_rew.info('==============================================')
        logger_rew.info('list_arm: %d' %len(self.bandit.list_arm))
        # loop through all arms and output their alpha and beta values
        for idx, arm in enumerate(self.bandit.list_arm):
            # Bayesian UCB
            logger_rew.info('%-2d %-12s alpha: %-3d beta: %-3d' %(arm.idx, arm.description, self.bandit._as[idx], self.bandit._bs[idx]))
        logger_rew.info('==============================================')

   
    def minimize_evasive_sample(self):
        """function to minimize the evasive samples
        """
        # get all samples with status evasive
        list_evasive = self.get_samples_with_status(SAMPLE_STATUS_EVASIVE)
        # loop through all evasive samples
        for sample in list_evasive:
            # if the scan status of the sample is deleted(includes new evasive samples) or pass
            if sample.scan_status in [SCAN_STATUS_DELETED, SCAN_STATUS_PASS]:
                # if seq cur x is smaller than the ammount of modifications that have been applied to the sample
                if sample.seq_cur_x < len(sample.list_applied_arm):
                    # prepare the action subset
                    ret = sample.prepare_action_subset()
                    if ret == -1:
                        continue
                    sample.replay_action_subset()
                    ori_arm_names = str(sample.get_names_from_arm_list(sample.list_applied_arm)).replace('\'', '').replace(' ', '').replace('None', '--')
                    cur_arm_names = str(sample.get_names_from_arm_list(sample.current_applied_arm_subset)).replace('\'', '').replace(' ', '').replace('None', '--')
                    logger_min.info('%s: %s (%d, %d) %s' %(sample.sname, ori_arm_names, sample.seq_cur_x, sample.seq_cur_y, cur_arm_names))
                    
                    # scan the sample with the current modifications
                    # TODO: should this be done with the av only or the hybrid approach?
                    # sample.copy_to_scan_folder(av_folder)
                    sample.copy_to_scan_folder(minimizer_scan_folder)



    def update_evasive_list(self):
        """function to update the list of evasive samples
        """
        # get all evasive samples
        list_evasive = self.get_samples_with_status(SAMPLE_STATUS_EVASIVE)

        # loop through all evasive samples
        for sample in list_evasive:
            # if the sample has not been minimized yet
            if sample.scan_status == SCAN_STATUS_WAITING:
                # check the status of the sample
                # TODO: Same as above/Part of the Problem above. Should this be done with the av only or the hybrid approach?
                #sample.scan_status = sample.check_scan_status(av_folder)
                sample.scan_status = sample.check_scan_status(minimizer_scan_folder)
                # if the sample has been deleted, the last removed modification made the sample non evasive. 
                if sample.scan_status == SCAN_STATUS_DELETED:
                    logger_min.info('%s: [FAIL] %s' %(sample.sname, sample.current_exe_path))
                    if sample.seq_cur_y == 0:
                        # add the removed arm to the usefil arm list
                        sample.list_useful_arm_idxs.append(sample.seq_cur_x)
                    sample.inc_seq_cur_y()
                # if the sample has passed the scan, it is evasive even after removal of the last modification
                elif sample.scan_status == SCAN_STATUS_PASS:
                    sample.latest_minimal_path = sample.current_exe_path
                    logger_min.info('%s: [SUCC] %s' %(sample.sname, sample.current_exe_path))
                    if len([arm for arm in sample.current_applied_arm_subset if arm]) == 1:
                        logger_min.info('%s: [SUCC] Quick Minimize ' %(sample.sname))
                        sample.list_useful_arm_idxs.append(len(sample.list_applied_arm) - 1)
                        sample.status = SAMPLE_STATUS_MINIMAL
                    sample.seq_cur_x_to_kept_arm[sample.seq_cur_x] = sample.current_applied_arm_subset[sample.seq_cur_x]

                    # clean up scan_folder
                    os.system('rm -f %s/%s*' %(minimizer_scan_folder, basename(sample.path)))
                    # update minimal arms
                    sample.list_minimal_arm = [ arm for arm in sample.current_applied_arm_subset if arm ]
                    sample.inc_seq_cur_x()
            # if every modification has been checked for minimization
            if sample.seq_cur_x >= len(sample.list_applied_arm) or sample.status == SAMPLE_STATUS_MINIMAL:
                # if the sample has been minimized
                sample.status = SAMPLE_STATUS_MINIMAL
                # update path of the sample and move it to the minimal folder
                minimal_path = sample.get_minimal_file()
                logger_min.info('%s: ###### [FINISH] %s' %(sample.sname, minimal_path))
                os.system('cp -p %s %s' %(minimal_path, minimal_folder))

                # find essential arms
                if len(sample.list_minimal_arm) == 0:
                    sample.list_minimal_arm = [ arm for arm in sample.list_applied_arm if arm ]
                logger_min.info('list_minimal_arm: %s' %sample.get_names_from_arm_list(sample.list_minimal_arm))

                # update reward
                for idx in sample.list_useful_arm_idxs:
                    ori_arm = sample.list_applied_arm[idx]
                    if idx < len(sample.list_applied_arm) - 1:
                        logger_min.info('update_reward_with_alpha_beta(%d, 1, -1)' %ori_arm.idx)
                        self.bandit.update_reward_with_alpha_beta(ori_arm.idx, 1, -1)   # beta -1 because +1 when fail
                    else:
                        logger_min.info('update_reward_with_alpha_beta(%d, 1, 0)' %ori_arm.idx)
                        self.bandit.update_reward_with_alpha_beta(ori_arm.idx, 1, 0)
                    if ori_arm.idx in [0, 1, 2, 3]:     # OA SA SR SP
                        self.bandit.add_new_arm(ori_arm)

                # clean up
                sample.delete_tmp_files(minimizer_output_folder)

    def update_minimal_list(self):
        """function to update the list of minimal samples
        is only beeing called if cuckoo sandbox is enabled
        TODO: can this function be removed?
        """
        list_minimal = self.get_samples_with_status(SAMPLE_STATUS_MINIMAL)
        for sample in list_minimal:
            # if not submitted, submit, otherwise get existing task_id
            minimal_path = sample.get_minimal_file()
            task_id = self.cuckoo.get_task_id(minimal_path)


            cuckoo_status = self.cuckoo.get_task_status(task_id)

            if cuckoo_status == 'reported':
                functional = self.cuckoo.is_functional(task_id, sample.path)
                if functional:
                    # evasive and functional, copy to the final output folder
                    logger_cuc.info('%s: Evasive sample is functional' %sample.sname)
                    os.system('mv %s %s' %(minimal_path, functional_folder))
                    sample.status = SAMPLE_STATUS_FUNCTIONAL    ########################## this sample is done.
                else:
                    # non-functional, try again
                    logger_cuc.info('%s: Evasive sample is broken, add it back to pool' %sample.sname)

                    sample.reset()      # reset members, except broken_action_idxs!!
                    sample.status = SAMPLE_STATUS_PENDING   ########################## add back to pending queue
                self.cuckoo.del_sample_and_task(minimal_path)    # clean up cuckoo
            else:
                time.sleep(1)
