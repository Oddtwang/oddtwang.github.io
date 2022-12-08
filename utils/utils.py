import re
import csv
import random
import numpy as np

from sklearn.metrics.pairwise import paired_cosine_distances

def load_csv( path, delimiter=',' ) : 
  header = None
  data   = list()
  with open( path, encoding='utf-8') as csvfile:
    reader = csv.reader( csvfile, delimiter=delimiter ) 
    for row in reader : 
      if header is None : 
        header = row
        continue
      data.append( row ) 
  return header, data


def is_torch_available() :
    try:
        import torch
        return True
    except ImportError:
        return False

def is_tf_available() :
    try:
        import tensorflow as tf
        return True
    except ImportError:
        return False

def set_seed(seed: int, seed_gpu=True):
    """
    Modified from : https://github.com/huggingface/transformers/blob/master/src/transformers/trainer_utils.py
    Helper function for reproducible behavior to set the seed in ``random``, ``numpy``, ``torch`` and/or ``tf`` (if
    installed).
    Args:
        seed (:obj:`int`): The seed to set.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    if is_tf_available() and seed_gpu :
        tf.random.set_seed(seed)

    if is_torch_available() and seed_gpu :
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # ^^ safe to call this function even if cuda is not available

        ## From https://pytorch.org/docs/stable/notes/randomness.html
        torch.backends.cudnn.benchmark = False

        try : 
          torch.use_deterministic_algorithms(True)
        except AttributeError: 
          torch.set_deterministic( True )

        

def write_csv( data, location ) : 
  with open( location, 'w', encoding='utf-8') as csvfile:
    writer = csv.writer( csvfile ) 
    writer.writerows( data ) 
  print( "Wrote {}".format( location ) ) 
  return

        
