from dataset_utils.preprocessing import letterbox_image_padded
from dataset_utils.eval import evaluate_dataset
from misc_utils.visualization import visualize_detections
from models.frcnn import FRCNN
from PIL import Image
from tog.attacks import *
from tqdm import tqdm
import os
import xml.etree.ElementTree as ET

weights = 'model_files/FRCNN.pth'  # TODO: Change this path to the victim model's weights

detector = FRCNN().cuda(device=0).load(weights)

eps = 8 / 255.       # Hyperparameter: epsilon in L-inf norm
eps_iter = 2 / 255.  # Hyperparameter: attack learning rate
n_iter = 10          # Hyperparameter: number of attack iterations
im_path = "dataset/VOCdevkit/VOC2007/JPEGImages/"
annot_path = "dataset/VOCdevkit/VOC2007/Annotations/"

scores = evaluate_dataset(detector, im_path, annot_path, num_examples=-1, attack=tog_untargeted, attack_params={"n_iter": n_iter, "eps": eps, "eps_iter":eps_iter}, flag_attack_fail=True)


