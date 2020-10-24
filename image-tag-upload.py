import os
import boto3
import base64
import random
from PIL import Image, ExifTags
from io import BytesIO
import cv2
import numpy as np

def get_weights(weights_path):
    weightsPath = os.getcwd() + weights_path
    return weightsPath

def get_labels(labels_path):
    lpath = os.getcwd() + labels_path
    labels = open(lpath).read().strip().split("\n")
    return labels

def get_config(config_path):
    configPath = os.getcwd() + config_path
    return configPath

def load_model(configpath,weightspath):
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net

s3 = boto3.resource('s3')
bucket = s3.Bucket('photomappr-storage')
def handler(event, context):

    # Get image in binary from api call, convert back and store in s3 bucket
    file_content = base64.b64decode(event['content'])
    file_path = str(random.randint(1,100)) + ".jpg" 
    try:
        s3_response = bucket.put_object(Key=file_path, Body=file_content)
    except Exception as e:
        raise IOError(e)
    
    # Load image file from bucket and read with pillow
    image = s3.Object(bucket_name = 'photomappr-storage', key=file_path)
    obj_body = image.get()['Body'].read()
    img = Image.open(BytesIO(obj_body))

    # Exif tag code from https://stackoverflow.com/questions/4764932/in-python-how-do-i-read-the-exif-data-for-an-image
    exif = {
        ExifTags.TAGS[k]: v
        for k, v in img._getexif().items()
        if k in ExifTags.TAGS
    }

    # Object detection
    # First, convert image to numpy array
    np_array = np.fromstring(obj_body,np.uint8)                                   
    image_np = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    # Config paths
    cfgpath="/opts/yolov3-tiny.cfg"
    wpath="/opts/yolov3-tiny.weights"
    labelsPath="/opts/coco.names"
    CFG=get_config(cfgpath)
    Weights=get_weights(wpath)
    labels=get_labels(labelsPath)

    # Load yolo algorithm
    net_obj=load_model(CFG,Weights)

    # Object detection within image
    class_ids = []                                                                              
    accuracy = []                                                                               
         
    lnames = net_obj.getLayerNames()                                                            
    layers = [lnames[i[0] - 1] for i in net_obj.getUnconnectedOutLayers()]                      
        
    blob = cv2.dnn.blobFromImage(image_np, 0.00392, (320, 320), (0, 0, 0), True, crop=False)     
            
    net_obj.setInput(blob)                                                                      
        
    result_det = net_obj.forward(layers)                                                        
    
    for each_result in result_det:                                                              
        for each in each_result:                                                                
            scores = each[5:]                                                                   
            class_id = np.argmax(scores)                                                        
            confidence = scores[class_id]                                                       
            if confidence > 0.5:                                                                
                accuracy.append(float(confidence))                                              
                class_ids.append(class_id)

    objects = {}
    arr = []
    if len(class_ids) > 0:
        for i in range(len(class_ids)):
            arr.append(labels[class_ids[i]])
   
    return {
        'exif': exif,
        'objects': arr
    }