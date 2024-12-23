import os
import sys
import hashlib
import time
import datetime
from utils import *
from models import *

#from ember import predict_sample
#import lightgbm as lgb
#import numpy as np
import glob
#from torch.autograd import Variable

MALCONV_MODEL_PATH = 'models/malconv/malconv.checkpoint'
EMBER_2019_MODEL_PATH = 'models/ember_2019/ember_model.txt'

rewriter_scan_folder = 'data/share/rewriter/'
minimizer_scan_folder = 'data/share/minimizer/'

class Classifier:
    def __init__(self, classifier_name):
        logger_cla.info('Model %s loading...' %classifier_name)
        if classifier_name == 'malconv':
            self.model = MalConvModel( MALCONV_MODEL_PATH, thresh=0.5 )
        elif classifier_name == 'ember':
            self.model = EmberModel_2019( EMBER_2019_MODEL_PATH, thresh=0.8336 )
        #elif classifier_name == 'clamav':
        #    self.model = ClamAV()
        else:
            print('bad classifier_name, please check configure')
            exit()

    def run(self):
        while True:
            count = 0
            count_current = count
            while count < 200:
                if count_current != count:
                    #logger_cla.info('count: %d' %count)
                    count_current = count
                #time.sleep(0.1)
                res1 = self.evaluate(minimizer_scan_folder)
                res2 = self.evaluate(rewriter_scan_folder)
                count += res1 + res2
                if os.path.exists(REWRITER_EXIT_SIGN):
                    logger_cla.info('%%%%%%%%%%%%%%%%%%%%%%%% Classifier Finish %%%%%%%%%%%%%%%%%%%%%%%')
                    exit()
    
    def evaluate(self, classifier_input):
        # search for files in the input folder
        # add them to benign list if extension is .benign
        # else add them to list_file 
        set_benign_files = set(glob.glob(classifier_input + '*.benign'))
        list_file = [x for x in glob.glob(classifier_input + '*') if x not in set_benign_files]

        file_amount = len(list_file)
        
        if file_amount > 0:
            list_file.sort(key=os.path.getmtime)
            file_path = list_file[0]
            #logger_cla.info(file_path)
            if os.path.exists(file_path) == False:
                logger_cla.info('file does not exist')
                return 0
            #result = self.model.predict(file_path)

            score = self.model.get_score(file_path)
            
            # TODO: read thresholds from config
            
            if score < 0.5: 
                # malware is classified as benign with high confidence 
                logger_cla.info('#### Benign! #### %s' %file_path)
                os.system('mv %s %s.benign' %(file_path, file_path))
                
            if  0.5 < score < 0.9:
                # classifier is unsure if malware or benign
                logger_cla.info('#### Unsure. Moving to AV! #### %s' %file_path)
                os.system('mv %s data/share/av/rewriter/%s' %(file_path, os.path.basename(file_path)))
            else:
                # classifier is very sure that it is malware
                logger_cla.info('Malicious! delete %s' %file_path)
                os.system('rm %s' %(file_path))
            return 1
        return 0
