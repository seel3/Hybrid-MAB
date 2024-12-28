from utils import *

class Minimizer:
    """Class to minimize modifications of a evasive sample
    """
    def __init__(self, samples_manager):
        """init function

        Args:
            samples_manager (Sample_Manager): Sample Manager of the samples
        """
        self.samples_manager = samples_manager

    def run(self):
        """ Function to run the minimization process
        Runs until ReWriter sends exit signal
        """
        while True:
            # Get the count of evasive and minimal samples
            count_evasive = self.samples_manager.get_count_with_status(SAMPLE_STATUS_EVASIVE)
            count_minimal = self.samples_manager.get_count_with_status(SAMPLE_STATUS_MINIMAL)
            # If there are no evasive samples, sleep for 5 seconds
            if count_evasive == 0:
                logger_min.info('No evasive samples, sleep...')
                time.sleep(5)
            else:
                # Minimize the evasive sample and update the evasive list
                self.samples_manager.minimize_evasive_sample()
                self.samples_manager.update_evasive_list()
                
                # TODO: no sanbox. Remove?
                if Utils.is_cuckoo_enable():
                    self.samples_manager.update_minimal_list()
            # TODO: no sandbox, make condition shorter and only check for count_evasive == 0?
            if ( Utils.is_cuckoo_enable() and count_evasive + count_minimal == 0 ) or (not Utils.is_cuckoo_enable() and count_evasive == 0):
                if os.path.exists(REWRITER_EXIT_SIGN):
                    logger_min.info('%%%%%%%%%%%%%%%%%%%%%%%% Minimizer Finish %%%%%%%%%%%%%%%%%%%%%%%%')
                    exit()

            time.sleep(0.5)
