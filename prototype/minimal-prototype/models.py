import torch
import time
import requests
import torch.nn.functional as F
import lightgbm as lgb
import numpy as np
import subprocess
import json
from ember import predict_sample
from MalConv import MalConv
import sys



class MalConvModel(object):
    """Class to run MalConv model

    Args:
        object (_type_): _description_
    """
    def __init__(self, model_path, thresh=0.5, name='malconv'): 
        """init method, loads the model and sets the threshold

        Args:
            model_path (_type_): _description_
            thresh (float, optional): _description_. Defaults to 0.5.
            name (str, optional): _description_. Defaults to 'malconv'.
        """
        # TODO make sure the model is loaded correctly to GPU
        self.model = MalConv(channels=256, window_size=512, embd_size=8).train()
        weights = torch.load(model_path,map_location='cpu')
        self.model.load_state_dict( weights['model_state_dict'])
        self.thresh = thresh
        self.__name__ = name

    def get_score(self, file_path):
        """function to get the model score for a file

        Args:
            file_path (path): path to the file that should be scored

        Returns:
            float: score of the model
        """
        try:
            with open(file_path, 'rb') as fp:
                # TODO should it read the whole file or just a part of it?
                bytez = fp.read(2000000)        # read the first 2000000 bytes
                _inp = torch.from_numpy( np.frombuffer(bytez,dtype=np.uint8)[np.newaxis,:] )
                with torch.no_grad():
                    outputs = F.softmax( self.model(_inp), dim=-1)
                return outputs.detach().numpy()[0,1]
        except Exception as e:
            print(e)
        return 0.0 
    
    def is_evasive(self, file_path):
        """function to check if a file is evasive or not

        Args:
            file_path (path): path to the file that should be checked

        Returns:
            Bool: If the file is evasive or not
        """
        score = self.get_score(file_path)
        return score < self.thresh



class EmberModel_2019(object):       # model in MLSEC 2019
    """Class to run Ember model

    Args:
        object (_type_): _description_
    """
    def __init__(self, model_path, thresh=0.8336, name='ember'):
        """init function to load the model and set the threshold

        Args:
            model_path (path): Path to the model
            thresh (float, optional): Threshold for classification. Defaults to 0.8336.
            name (str, optional): name of the model. Defaults to 'ember'.
        """
        # TODO: make sure this is run on the GPU
        # load lightgbm model
        self.model = lgb.Booster(model_file=model_path)
        self.thresh = thresh
        self.__name__ = 'ember'

    def get_score(self,file_path):
        """function to get the model score for a file

        Args:
            file_path (path): Path to the file that should be scored

        Returns:
            float: Score that the model gives to the file
        """
        with open(file_path, 'rb') as fp:
            bytez = fp.read()
            score = predict_sample(self.model, bytez)
            return score
    
    def is_evasive(self, file_path):
        """Function to check if a file is evasive or not

        Args:
            file_path (path): Path to the file that should be checked

        Returns:
            Bool: If the file is evasive or not
        """
        score = self.get_score(file_path)
        return score < self.thresh

# TODO: remove? ClamAV is not used in the current implementation
class ClamAV(object):
    def is_evasive(self, file_path):
        res = subprocess.run(['clamdscan', '--fdpass', file_path], stdout=subprocess.PIPE)
        #print(res.stdout)
        if 'FOUND' in str(res.stdout):
            return False
        elif 'OK' in str(res.stdout):
            return True
        else:
            print('clamav error')
            exit()
