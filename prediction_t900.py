import torch
from torchvision import transforms

from PIL import Image
import cv2
import warnings
import argparse

import pyttsx3
import config
from utils import load_model, generate_backbone_name
from cvzone.HandTrackingModule import HandDetector

warnings.filterwarnings(action = "ignore")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weight_path",
        "-w",
        type=str,
        default=config.T900_WEIGHT,
        required=False,
        help="path of the weight that is supposed to be loaded for prediction",
    )

    parser.add_argument(
        "--backbone",
        "-b",
        type=str,
        default=config.REAL_TIME_BACKBONE,
        required=False,
        help="backbone of the model architecture that is to be used for prediction",
    )

    args = parser.parse_args()
    weight_path = args.weight_path
    backbone_name = args.backbone
    backbone = generate_backbone_name(backbone_name)

    MEAN = [0.5016, 0.4767, 0.4698]
    STD = [0.2130, 0.2169, 0.2069]
    img_transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=MEAN, std=STD),
    ])
    cap = cv2.VideoCapture(0)

    imgSize = config.IMG_SIZE
    labels = config.ALPHABETS
    detector = HandDetector(maxHands=1)
    word = ''
    index_list = []
    offset = 20

    model = load_model(backbone, weight_path, device)
    model.eval()
    while True:
        success, img0 = cap.read()
        imgOutput = img0.copy()
        hands, img1 = detector.findHands(img0)
        if hands:
            hand = hands[0]
            x, y, w, h = hand['bbox']

            success, img2 = cap.read()
            imgCrop_normal = img2[y - round(w/2):y + round(w/2) + h, x - round(h/2):x + w + round(h/2)]
            try:
                imgResize_normal = cv2.resize(imgCrop_normal, (imgSize, imgSize))
                cv2.imshow("ImageCrop_normal", imgCrop_normal)
            except:
                pass
            
            img_np = Image.fromarray(imgResize_normal)
            img_tensor = img_transform(img_np)
            image = img_tensor.unsqueeze(0)
            output = model(image.to(device))
            _, predicted = torch.max(output.data, 1)
            index = predicted.item()

            cv2.rectangle(imgOutput, (x - offset, y - offset-50),
                        (x - offset + 90, y - offset - 50 + 50), (255, 0, 255), cv2.FILLED)
            cv2.putText(imgOutput, labels[index], (x, y -26), cv2.FONT_HERSHEY_COMPLEX, 1.7, (255, 255, 255), 2)
            cv2.rectangle(imgOutput, (x - offset, y - offset),
                        (x + w + offset, y + h + offset), (255, 0, 255), 4)
            
            key = cv2.waitKey(1)        
            if str(labels[index]) == 'Y':
                print('letter recorded')
                try:
                    word = word + str(labels[int(index_list[-1])]) 
                except:
                    pass
                index_list = []

            if str(labels[index]) == 'O':
                print(word)
                pyttsx3.speak(word)
                word = ''

            if index != 24:
                index_list.append(index)

        cv2.imshow("Image", imgOutput)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            cap.release()
            break
    
    cv2.destroyAllWindows()