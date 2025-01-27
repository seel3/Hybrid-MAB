from utils import *
import copy
from models import *
from arm import *
from pathlib import Path

class Sample:
    """class that represents a malware sample
    """
    def __init__(self, path):
        """init function for Sample class

        Args:
            path (path): Path to the sample
        """
        # path to the original sample
        self.path = path
        # path to the location of the current sample/latest modified sample
        self.current_exe_path = path
        # short name (first 8 chars from sample name) of the sample
        self.sname = Utils.short_name(self.path)
        # max length from bandit config
        self.max_length = Utils.get_max_length()
        # time sample was last copied
        self.copy_time = None
        # queue types of which the sample is in. option: [None/pending/working/evasive/minimal/functional]
        self.status = None
        # file status on the classifier option: [None/SCAN_STATUS_DELETED/SCAN_STATUS_PASS/SCAN_STATUS_WAITING/SCAN_STATUS_OVERTIME/SCAN_STATUS_MD5_CHANGED]
        self.scan_status = None  
        # list of applied modifications
        self.list_applied_arm = []
        # list of useful arm indexes
        self.list_useful_arm_idxs = []
        # 
        self.current_applied_arm_subset = []
        #
        self.seq_cur_x = -1
        #
        self.seq_cur_y = 0
        #
        self.seq_cur_x_to_kept_arm = {}
        # list of minimal arms
        self.list_minimal_arm = []
        # path to the latest minimal sample
        self.latest_minimal_path = None
        # path to the evasive sample
        self.evasive_path = None
        # number of times the sample had an arm pulled/was modified
        self.pull_count = 0

    def reset(self):
        """function to reset all the attributes of the sample
        """
        self.current_exe_path = self.path
        self.copy_time = None
        self.status = None
        self.scan_status = None
        self.list_applied_arm = []
        self.current_applied_arm_subset = []
        self.seq_cur_x = -1
        self.seq_cur_y = 0
        self.seq_cur_x_to_kept_arm = {}
        self.list_minimal_arm = []
        self.latest_minimal_path = None
        self.evasive_path = None
        self.list_useful_arm_idxs = []
        self.pull_count = 0


    def set_current_exe_path(self, path):
        """setter to set the current_exe_path attribute

        Args:
            path (path): The path the latest version of the sample is currently at
        """
        self.current_exe_path = path


    def inc_seq_cur_x(self):
        """TODO: comment
        """
        self.seq_cur_x += 1
        self.seq_cur_y = 0

    def inc_seq_cur_y(self):
        """TODO: comment
        """
        action = self.list_applied_arm[self.seq_cur_x].action
        list_mic_action = ACTION_TO_MICROACTION[action]

        if self.seq_cur_x == -1:
            if self.seq_cur_y == len(list_mic_action) - 1:  
                self.seq_cur_y = -1         # try the original last action
                return
            if self.seq_cur_y == -1:
                self.inc_seq_cur_x()        # from Quick minimize back to normal
                return
        if self.seq_cur_y < len(list_mic_action) - 1:
            self.seq_cur_y += 1
        else:
            self.inc_seq_cur_x()

    def delete_applied_arm(self):
        """function to delete all the applied arms
        """
        for arm in self.list_applied_arm:
            del arm
        self.list_applied_arm = []

    def delete_tmp_files(self, folder):
        """function to delete the generated tmp files in the folder

        Args:
            folder (path): Path to the folder to delete the files from
        """
        logger_rew.info('delete generated tmp files in %s' % folder)
        os.system('rm -f %s/%s.*' % (folder, basename(self.path)))

    def delete_files_except_current_exe(self, folder):
        """function to delete all the files in the folder except the latest version of the sample

        Args:
            folder (path): Path to the folder to delete the files from
        """
        # sha256 is the name of the file
        sha256 = basename(self.path)
        # get a list of all files in the folder that have the sha256 in their name
        list_file = [folder + x for x in os.listdir(folder) if sha256 in x]
        # sort the list of files by the time they were last modified
        list_sorted = sorted(list_file, key=os.path.getmtime)
        # delete all the files in the list except the latest one
        for x in list_sorted[:-1]:
            if x != self.current_exe_path:
                os.system('rm -f %s' %x)
        
    def append_arm(self, arm):
        """function to append an arm to the list of applied arms

        Args:
            arm (Arm): The arm to append
        """
        self.list_applied_arm.append(arm)

    def copy_to_scan_folder(self, scan_folder):
        """function to copy a sample to the scan folder

        Args:
            scan_folder (path): Path to the scan folder
        """
        # set the scan status to waiting
        self.scan_status = SCAN_STATUS_WAITING
        # set the copy time to the current time
        self.copy_time = time.time()
        # copy the sample to the scan folder
        Utils.safe_copy(self.current_exe_path, scan_folder + basename(self.current_exe_path))


    def is_remain_after_threshold_time(self):
        """function to check if a sample is still existent after the threshold time

        Returns:
            Boolean: True if the sample is still existent after the threshold time, False otherwise
        """
        # get the wait time from the config
        wait_time = Utils.get_wait_time()
        # get how long the sample already exists
        existing_time = time.time() - self.copy_time
        #logger_rew.info('existing_time: %d/%d' %(existing_time, wait_time))
        # check if threshold time has passed
        if existing_time > wait_time:
            return True
        else:
            return False


    def check_scan_status(self, scan_folder):
        """function to check the scan status of the sample and set it according to observations

        Args:
            scan_folder (path): The folder to check the samples from

        Returns:
            int: scan status of the sample
        """
        # wait for the stop sign to be removed
        Utils.wait_on_stop_sign()
        
        # check if the sample is in the scan folder of the av or the model
        if "/av" not in scan_folder:
            # model scan
            # set the scan status to deleted
            scan_status = SCAN_STATUS_DELETED
            # get the filename of the sample
            sha256 = basename(self.path)
            # get all versions of the sample from the scan folder
            for file_path in glob.glob('%s%s*' %(scan_folder, sha256)):
                # check if the sample is benign and set the scan status accordingly
                if '.benign' in file_path:
                    scan_status = SCAN_STATUS_PASS
                else:
                    scan_status = SCAN_STATUS_WAITING
                break
            # if the sample has the status pass, delete all versions of the sample
            if scan_status in [SCAN_STATUS_PASS]:
                os.system('rm -f %s/*%s*' %(scan_folder, basename(self.path)))
            return scan_status
        else:
            # av scan
            sha256 = basename(self.path)
            # Get all versions of the sample from the scan folder
            list_file = glob.glob('%s%s*' %((scan_folder), sha256))
            # check if file has been removed by av and set the scan status accordingly
            if len(list_file) == 0:
                scan_status = SCAN_STATUS_DELETED
            else:
                # check if the threshold time has already passed
                if self.is_remain_after_threshold_time():
                    scan_status = SCAN_STATUS_PASS
                else:
                    scan_status = SCAN_STATUS_WAITING
        return scan_status

    def prepare_action_subset(self):
        """TODO: comment

        Returns:
            _type_: _description_
        """
        if self.seq_cur_x == -1:        # Quick minimzier
            if self.seq_cur_y == 0:
                self.seq_cur_y = 1     # skip the first ''                         
            elif self.seq_cur_y == -1:  # special -1, try only the last original arm
                self.current_applied_arm_subset = [self.list_applied_arm[-1]]       
                return
            # Quick Minimizer: try only the last arm first
            list_arm = [None for x in range(len(self.list_applied_arm))]
            action = self.list_applied_arm[self.seq_cur_x].action
            list_mic_action = ACTION_TO_MICROACTION[action]
            # no need to test the original sample

        elif self.seq_cur_x < len(self.list_applied_arm):
            list_arm = copy.deepcopy(self.list_applied_arm)

            # replace kept arm
            for k, v in self.seq_cur_x_to_kept_arm.items():
                #logger_min.info('%s: %d' %(self.sname, k))
                list_arm[k] = v
            action = self.list_applied_arm[self.seq_cur_x].action
            list_mic_action = ACTION_TO_MICROACTION[action]

            # predict not need to apply OA1 if there are other actions
            minimal_action = list_mic_action[self.seq_cur_y]
            if minimal_action == 'OA1' and len([arm for arm in list_arm if arm != None]) > 0:       
                #self.seq_cur_y += 1
                self.inc_seq_cur_y()
                if self.seq_cur_x > len(list_arm) - 1:
                    return -1
        else:
            return -1

        #logger_min.info('%s %s %s' %(list_mic_action, self.seq_cur_y, list_mic_action[self.seq_cur_y]))
        minimal_action = list_mic_action[self.seq_cur_y]
        if minimal_action == '':          # remove current action
            minimal_arm = None
        elif minimal_action == 'OA':      # only SA need to be minimized to OA
            content = self.list_applied_arm[self.seq_cur_x].content
            minimal_arm = ArmOA(0, content=content)
        elif minimal_action == 'OA1':
            minimal_arm = ArmOA(0, content=bytes([1]))
        elif minimal_action == 'SA1':     # only SA need to be minimized to SA1
            minimal_arm = copy.deepcopy(self.list_applied_arm[self.seq_cur_x])
            minimal_arm.set_content(bytes([1]))
        elif minimal_action == 'SP1':     # only SP need to be minimized to SP1
            minimal_arm = copy.deepcopy(self.list_applied_arm[self.seq_cur_x])
            minimal_arm.set_content(bytes([1]))
        elif minimal_action == 'SR1':     # only SR need to be minimized to SR1
            minimal_arm = copy.deepcopy(self.list_applied_arm[self.seq_cur_x])
            minimal_arm.mutate_section_name_one_byte()
        elif minimal_action == 'CP1':
            minimal_arm = ArmCP1(12)
        else:
            logger_min.error('%s: minimal_action unexpected: [%s]' % (
                self.sname, minimal_action))
            exit()
        list_arm[self.seq_cur_x] = minimal_arm

        self.current_applied_arm_subset = list_arm

    def get_names_from_arm_list(self, list_arm):
        """get the names of the actions from a list of arms

        Args:
            list_arm (list): list of arms

        Returns:
            list: list of names of the actions
        """
        list_arm_name = []
        # for each arm in the list get the name of the action and append it to the name list
        for x in list_arm:
            if x:
                list_arm_name.append(x.action)
            else:
                list_arm_name.append(None)
        return list_arm_name

    def get_minimal_file(self):
        """Function to get the minimal file

        Returns:
            path: Path to the minimal sample
        """
        # if minimal_path has been set a minimized sample exists
        if self.latest_minimal_path:
            # set the minimal path to the latest minimal path
            minimal_path = self.latest_minimal_path
        
        # sample can not be minimized -> evasive sample is already minimal
        else:
            # get the sha256 of the sample
            sha256 = basename(self.path)
            # get a list of all versions of the sample from the evasive folder
            list_file = glob.glob('%s%s*' %(evasive_folder, sha256))
            # no evasive sample found == something went wrong -> End Program
            if len(list_file) == 0:
                logger_min.error('cannot find original evasive sample')
                exit()
            # set the minimal path to the first evasive sample found
            minimal_path = list_file[0]

        return minimal_path

    def replay_action_subset(self):     # For MAB Rewriter
        """TODO: comment
        """
        if len(self.current_applied_arm_subset) == 0:
            logger_min.error('empty replay subset')
            exit()
        input_path = self.path
        for arm in self.current_applied_arm_subset:
            if arm:
                output_path = arm.transfer(input_path, minimizer_output_folder, verbose=False)
                if 'minimizer_output' in os.path.dirname(input_path):
                    os.system('rm %s' %input_path)
                input_path = output_path
                self.set_current_exe_path(output_path)

    def get_applied_actions(self):
        """function to get the names of the applied actions

        Returns:
            String: name of the applied actions
        """
        return self.get_names_from_arm_list(self.list_applied_arm)
