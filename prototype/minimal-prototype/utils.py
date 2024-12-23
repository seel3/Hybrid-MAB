import os
import glob
import hashlib
from os.path import basename, dirname
import numpy as np
from datetime import datetime
import configparser
import time
import logging
#from models import *
import pexpect
import random
import sys

config = configparser.ConfigParser()
config.optionxform = str
config.read('conf/configure.ini')

MD5_TIMEOUT = -1
MD5_FILE_NOT_EXIST = -2

SCAN_STATUS_DELETED = 1
SCAN_STATUS_PASS = 2
SCAN_STATUS_WAITING = 3
SCAN_STATUS_OVERTIME = 4
SCAN_STATUS_MD5_CHANGED = 4

SAMPLE_STATUS_PENDING = 1
SAMPLE_STATUS_WORKING = 2
SAMPLE_STATUS_EVASIVE = 3
SAMPLE_STATUS_MINIMAL = 4
SAMPLE_STATUS_SKIP = 5
SAMPLE_STATUS_FUNCTIONAL = 6

VM_LOCAL = 1
VM_CLOUD = 2

SCAN_TYPE_MODEL = 1
SCAN_TYPE_AV = 2

list_benign_section_file = os.listdir(str(config['DATASET']['benign_content_folder']))

REWRITER_EXIT_SIGN = 'output/rewriter_exit.sign'

ACTION_MAP = {
    'OA': 'overlay_append',
    'SR': 'section_rename',
    'SA': 'section_add',
    'SP': 'section_append',
    'RC': 'remove_signature',
    'RD': 'remove_debug',
    'BC': 'break_optional_header_checksum',
}

ACTION_LIST = [
        'CR', # code_randomize
        'RS', #remove_signature
        'RD', #remove_debug
        'BC', #break_optional_header_checksum
        'OA', #overlay_append
        'SR', #section_rename
        'SA', #section_add
        'SP', #section_append
        'OA1', # overlay_append_one_byte
        'SA1', # section_add_one_byte
        'SP1', # section_append_one_byte
        'CP1', # code_section_append_one_byte
        'SR1', # section_rename_random
        ]

MICRO_ACTION_LIST = [
        'OA1', # overlay_append_one_byte
        'SA1', # section_add_one_byte
        'SP1', # section_append_one_byte
        'CP1', # code_section_append_one_byte
        'SR1', # section_rename_random
        ]

MACRO_ACTION_LIST = [
        'RS', #remove_signature
        'RD', #remove_debug
        'BC', #break_optional_header_checksum
        'OA', #overlay_append
        'SR', #section_rename
        'SA', #section_add
        'SP', #section_append
        ]

ACTION_LIST_ONCE = [
        'RS', #remove_signature
        'RD', #remove_debug
        'BC', #break_optional_header_checksum
        ]

ACTION_LIST_REPEAT = [
        'OA', #overlay_append
        'SR', #section_rename
        'SA', #section_add
        'SP', #section_append
        ]

ACTION_TO_MICROACTION = {
        'CR': ['', 'OA1', 'CP1'],
        'SA': ['', 'OA1', 'SA1', 'OA'],
        'SP': ['', 'OA1', 'SP1'],
        'SR': ['', 'OA1', 'SR1'],
        'RD': ['', 'OA1', 'CP1'],
        'RC': ['', 'OA1'],
        'RS': ['', 'OA1'],
        'BC': ['', 'OA1'],
        'OA': ['', 'OA1'],
        'CP1': ['', 'OA1'],
        'SA1': ['', 'OA1'],
        'SP1': ['', 'OA1'],
        'SR1': ['', 'OA1'],
        }

set_copied_md5 = set()
dict_sha256_to_vm_ip = {} 

class Utils:
    def setup_logger(name, log_file, level=logging.INFO):
        handler = logging.FileHandler(log_file, mode='w')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
    
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        logger.addHandler(handler)
    
        return logger

    def copy(input_path, output_path):
        os.system('cp %s %s' %(input_path, output_path))

    def safe_copy(input_path, output_path):     # prevent read dirty data
        os.system('cp %s %s' %(input_path, copy_tmp_folder))
        os.system('mv %s%s %s' %(copy_tmp_folder, basename(input_path), output_path))
    

    def get_md5(path):
        if os.path.exists(path) == False:
            logger_rew.info('error! file not exists: %s' % path)
            return None
        hash_md5 = hashlib.md5()
        try:
            with open(path, 'rb') as f:
                content = f.read()
                # for chunk in iter(lambda: f.read(4096), b''):
                #    logger_rew.info('3')
                hash_md5.update(content)
                # logger_rew.info(len(content))
                md5 = hash_md5.hexdigest()
            #logger_rew.info('md5: %s' %md5)
            return md5
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger_rew.error('%s %s:%s cannot get md5' %
                             (exc_type, fname, exc_tb.tb_lineno))
            return None

    
    def get_vm_ips():
        vm_ips = []
        for i in range(1, Utils.get_vm_count()+1):
            if i == 1:
                vm_ip = config['SHARE_FOLDER']['vm_ip_1']
            if i == 2:
                vm_ip = config['SHARE_FOLDER']['vm_ip_2']
            if i == 3:
                vm_ip = config['SHARE_FOLDER']['vm_ip_3']
            if i == 4:
                vm_ip = config['SHARE_FOLDER']['vm_ip_4']
            vm_ips.append(vm_ip)
        return vm_ips


    def wait_on_stop_sign():
        while os.path.exists('stop.sign') == True:
            print('find stop.sign, wait 10 seconds')
            time.sleep(10)
    
    def short_name(sample_path):
        return basename(sample_path)[:8]
    
    # may cause errors when ori_name contains '.'
    def get_ori_name(sample_path):
        return basename(sample_path).split('.')[0].replace('__tmp__', '')
    
    def get_classifier_name():
        return config['CLASSIFIER']['name']

    def get_classifier_scan_type():
        if Utils.get_classifier_name() in ['malconv', 'ember', 'clamav']:
            return SCAN_TYPE_MODEL
        elif Utils.get_classifier_name() == 'av':
            return SCAN_TYPE_AV
        else:
            print('evaluate_type config error')
            exit()
    
    def get_wait_time():
        return int(config['CLASSIFIER']['scan_folder_wait_time'])
    
    def get_max_working_sample_count():
        return int(config['BANDIT']['max_working_sample_count'])
    
    def get_max_pull():
        return int(config['BANDIT']['max_pull'])

    def is_thompson_sampling():
        if int(config['BANDIT']['thompson_sampling']) == 1:
            return True
        else:
            return False

    def get_update_parent():
        if int(config['BANDIT']['update_parent']) == 1:
            return True
        else:
            return False
    
    def get_rewriter_type():
        return config['REWRITER']['type']

    def get_max_length():
        return int(config['BANDIT']['max_length'])
    
    def get_smallest_section_size():
        return int(config['BANDIT']['smallest_section_size'])
    
    def get_largest_section_size():
        return int(config['BANDIT']['largest_section_size'])
    
    def get_malware_folder():
        return config['DATASET']['malware_folder']

    def get_randomized_folder():
        return config['DATASET']['randomized_folder']
    
    def get_evasive_folder():
        return config['OUTPUT_FOLDER']['evasive_folder']

    def get_minimal_folder():
        return config['OUTPUT_FOLDER']['minimal_folder']

    def get_functional_folder():
        return config['OUTPUT_FOLDER']['functional_folder']

    def get_host_password():
        return config['SHARE_FOLDER']['host_password']
    
    def get_vm_location(): 
        vm_location = config['SHARE_FOLDER']['vm_location']
        if vm_location == 'local':
            return VM_LOCAL
        elif vm_location == 'cloud':
            return VM_CLOUD
        else:
            print('vm_location error')

    def get_vm_password():
        return config['SHARE_FOLDER']['vm_password']
    
    def get_vm_username():
        return config['SHARE_FOLDER']['vm_username']
    
    def get_vm_count():
        return int(config['SHARE_FOLDER']['vm_count'])

    def get_vm_ip():
        return config['SHARE_FOLDER']['vm_ip']

    def is_cuckoo_enable():
        return config['CUCKOO']['enable'] == 'yes'

    def get_cuckoo_token():
        return config['CUCKOO']['token']

    def get_ori_json_folder():
        return config['CUCKOO']['ori_json_folder']
    
    def get_save_json_folder():
        return config['CUCKOO']['save_json_folder']

    def get_random_content():
        filename = random.choice(list_benign_section_file)
        name = filename.split('|')[1]
        size = int(filename.split('|')[2])
        with open(str(config['DATASET']['benign_content_folder']) + filename, 'rb') as fp:
            content = fp.read()
            return name, size, content

    def print_configure():
        logger_rew.info('='*30)
        logger_rew.info('Classifier Name :   %s' %config['CLASSIFIER']['name'])
        logger_rew.info('Dataset Folder  :   %s' %config['DATASET']['malware_folder'])
        logger_rew.info('Benign Content# :   %d' %(len(list_benign_section_file)))
        logger_rew.info('Algorithm Type  :   %s' %config['REWRITER']['type'])
        logger_rew.info('Max Working     :   %s' %config['BANDIT']['max_working_sample_count'])
        logger_rew.info('Thompson Sample :   %s' %config['BANDIT']['thompson_sampling'])
        logger_rew.info('Update Parent   :   %s' %config['BANDIT']['update_parent'])
        logger_rew.info('Max Pull        :   %s' %config['BANDIT']['max_pull'])
        logger_rew.info('Max Action      :   %s' %config['BANDIT']['max_length'])
        logger_rew.info('='*30)

    def create_folders():

        os.system('rm -f %s' %REWRITER_EXIT_SIGN)
        os.system('rm -fr %s' 'data/tmp/*')

        os.system('mkdir -p %s' %copy_tmp_folder)
        os.system('rm -fr %s/*' %copy_tmp_folder)

        os.system('mkdir -p %s' %rewriter_output_folder)
        os.system('rm -fr %s/*' %rewriter_output_folder)

        os.system('mkdir -p %s' %minimizer_output_folder)
        os.system('rm -fr %s/*' %minimizer_output_folder)

        os.system('mkdir -p %s' %rewriter_scan_folder)
        os.system('rm -fr %s/*' %rewriter_scan_folder)
        os.system('mkdir -p %s' %minimizer_scan_folder)
        os.system('rm -fr %s/*' %minimizer_scan_folder)
        
        os.system('mkdir -p %s' %rewriter_output_folder_av)
        os.system('rm -fr %s/*' %rewriter_output_folder_av)

        os.system('mkdir -p %s' %evasive_folder)
        os.system('rm -fr %s/*' %evasive_folder)

        os.system('mkdir -p %s' %minimal_folder)
        os.system('rm -fr %s/*' %minimal_folder)

        os.system('mkdir -p %s' %functional_folder)
        os.system('rm -fr %s/*' %functional_folder)
    
        os.system('mkdir -p %s' %json_folder)
        os.system('rm -fr %s/*' %json_folder)


os.system('mkdir -p log/')
os.system('rm -f log/*.log')
logger_rew = Utils.setup_logger('rewriter', 'log/rewriter.log')
logger_rew.addHandler(logging.StreamHandler(sys.stdout))
logger_min = Utils.setup_logger('minimizer', 'log/minimizer.log')
if Utils.get_classifier_scan_type() == SCAN_TYPE_MODEL:
    logger_cla = Utils.setup_logger('classifier', 'log/classifier.log')
if Utils.is_cuckoo_enable():
    logger_cuc = Utils.setup_logger('cuckoo', 'log/cuckoo.log')

rewriter_scan_folder = 'data/share/rewriter/'
minimizer_scan_folder = 'data/share/minimizer/'
copy_tmp_folder = 'data/share/tmp/'

rewriter_output_folder = 'output/rewriter_output/'
minimizer_output_folder = 'output/minimizer_output/'

rewriter_output_folder_av = 'data/share/av/'
av_folder = "data/share/av/"


evasive_folder = Utils.get_evasive_folder()
minimal_folder = Utils.get_minimal_folder()
functional_folder = Utils.get_functional_folder()
json_folder = Utils.get_save_json_folder()
