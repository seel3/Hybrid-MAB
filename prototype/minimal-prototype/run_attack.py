from bandit import Bandit
from minimizer import Minimizer
from rewriter_MAB import MABRewriter
from samples_manager import SamplesManager
from utils import *
import random
import threading
from classifier import Classifier

random.seed(10)

if __name__ == '__main__':
    logger_rew.info('============= Start ============')
    logger_min.info('============= Start ============')
    Utils.print_configure()
    Utils.create_folders()

    bandit = Bandit()
    samples_manager = SamplesManager(Utils.get_malware_folder(), bandit)

    

    print('\n### Log can be found in the log/ folder ###\n')
    
    # start classifier thread
    classifier = Classifier(Utils.get_classifier_name())
    classifier_thread = threading.Thread(target=classifier.run)
    print('start classifier...')
    classifier_thread.start()
    
    
    
    # start rewriter and minimizer threads
    rewriter_type = Utils.get_rewriter_type()
    if rewriter_type == 'MAB':
        rewriter = MABRewriter(bandit, samples_manager)
        minimizer = Minimizer(samples_manager)

        rewriter_thread = threading.Thread(target=rewriter.run)
        minimizer_thread = threading.Thread(target=minimizer.run)

        print('start rewriter...')
        rewriter_thread.start()
        print('start minimizer...')
        minimizer_thread.start()

        rewriter_thread.join()
        minimizer_thread.join()
    elif rewriter_type == 'RAND':
        rewriter = MABRewriter(bandit, samples_manager, rand=True)
        rewriter.run()



    classifier_thread.join()
    print("Done!")
