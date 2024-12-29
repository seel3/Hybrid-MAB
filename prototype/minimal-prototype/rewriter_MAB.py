from utils import *
import pexpect

class MABRewriter:
    """class for rewriter using MAB
    """
    def __init__(self, bandit, samples_manager, rand=False):
        """init method

        Args:
            bandit (Bandit): The used bandit object
            samples_manager (Samples_Manager): The used Samples_Manager object
            rand (bool, optional): Random modifications. Defaults to False.
        """
        self.randomize_path = Utils.get_randomized_folder() 

        self.bandit = bandit
        self.samples_manager = samples_manager
        self.rand = rand
        

    def run(self):
        """main method of rewriter
        """
        # initial classification of the samples
        # get initial samples
        self.samples_manager.get_initial_pending_list()
        # get count of how many modifications in total (samples* max pull) should be performed max
        trial_amount = self.samples_manager.get_count_with_status(SAMPLE_STATUS_PENDING) * Utils.get_max_pull()
        logger_rew.info('TS: %d update parent: %d' %(Utils.is_thompson_sampling(), Utils.get_update_parent()))
        total_pull_count = 0
        logger_rew.info('===========================================')
        process_count = 0
        count_skip = 0
        count_solve = 0
        count_need = 0
        # get max count of pulls
        max_pull_count = Utils.get_max_pull()
        
        
        
        # rewriter loop will run until all samples are pulled max_pull_count times or all samples are evasive
        while True:
            # get next sample from manager
            sample = self.samples_manager.get_next_sample()
            # sample got returned
            if sample:
                # get arm/modification for sample
                arm = self.bandit.get_next_arm(sample, sample.get_applied_actions(), rand=self.rand)
                # pull arm/modification
                output_path = arm.pull(sample)
                # set new path
                sample.set_current_exe_path(output_path)
                # add modification to total modifications list of sample
                sample.append_arm(arm)
                # increment pull count
                total_pull_count += 1
                # copy sample to scan folder
                sample.copy_to_scan_folder(rewriter_scan_folder)

                process_count += 1
                if process_count % 100 == 0:            # update every x pulls
                    logger_rew.info('update rewriter working list')
                    self.samples_manager.update_working_list()
            # no sample got returned
            else:
                # check if any samples are still beeing worked on
                count_working = self.samples_manager.get_count_with_status(SAMPLE_STATUS_WORKING)
                # no samples beeing worked on
                if count_working == 0:
                    # check if all samples are pulled max_pull_count times / how many pulls are still remaining
                    count_remain = len([x for x in self.samples_manager.get_samples_with_status(SAMPLE_STATUS_PENDING) if x.pull_count < max_pull_count])
                    # if all samples are pulled max_pull_count times break loop
                    if count_remain == 0:
                        logger_rew.info('###### All samples are pulled max times!')
                        break
                # update working list
                logger_rew.info('All pending samples are processing by arms, or more than %d samples are handing at the same time' %self.samples_manager.sample_concurrent_limit)
                time.sleep(1)
                self.samples_manager.update_working_list()
                
            # get count of samples with each status and log it
            count_skip = self.samples_manager.get_count_with_status(SAMPLE_STATUS_SKIP)
            count_evasive = self.samples_manager.get_count_with_status(SAMPLE_STATUS_EVASIVE)
            count_minimal = self.samples_manager.get_count_with_status(SAMPLE_STATUS_MINIMAL)
            count_functional = self.samples_manager.get_count_with_status(SAMPLE_STATUS_FUNCTIONAL)
            count_need = len(self.samples_manager.list_sample) - count_skip
            logger_rew.info('-----------------------------------------------')
            logger_rew.info('### [%d/%d (%.2f%%)] skip: %d evasive: %d/%d (%.2f%%) minimal: %d' \
                    %(total_pull_count, trial_amount, total_pull_count/trial_amount * 100, count_skip, \
                    count_evasive + count_minimal + count_functional, count_need, \
                    ((count_evasive + count_minimal + count_functional)/count_need*100), \
                    count_minimal + count_functional))
            logger_rew.info('-----------------------------------------------')

            # if all samples are evasive or minimal break loop
            if count_minimal + count_skip == len(self.samples_manager.list_sample):
                break

        # wait for remaining working samples to be deleted or evade
        logger_rew.info('wait for remaining working samples')
        while True:
            # check status of all samples
            count_working = self.samples_manager.get_count_with_status(SAMPLE_STATUS_WORKING)
            count_evasive = self.samples_manager.get_count_with_status(SAMPLE_STATUS_EVASIVE)
            count_minimal = self.samples_manager.get_count_with_status(SAMPLE_STATUS_MINIMAL)
       
            # check if any samples are still beeing worked on
            if self.rand == False:
                if count_working + count_evasive == 0:
                    break
            else:
                if count_working == 0:
                    break
            # update working list and wait 
            logger_rew.info('count_working: %d, count_evasive: %d, count_minimal: %d' %(count_working, count_evasive, count_minimal))
            self.samples_manager.update_working_list()
            time.sleep(10)

        # get all pending samples and delete their temp files
        logger_rew.info('delete tmp files for list_pending')
        list_pending = self.samples_manager.get_samples_with_status(SAMPLE_STATUS_PENDING)
        for sample in list_pending:
            logger_rew.info('delete tmp files for list_pending')
            sample.delete_tmp_files(rewriter_output_folder)

        # rewriter has finished. Create exit sign so other threads can finish as well
        logger_rew.info('%%%%%%%%%%%%%%%%%%%%%%%% Rewriter Finish %%%%%%%%%%%%%%%%%%%%%%%%')
        os.system('touch %s' %REWRITER_EXIT_SIGN)
