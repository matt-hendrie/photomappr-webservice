import os
import boto3
import base64
from PIL import Image, ExifTags
from io import BytesIO
import cv2
import numpy as np
import uuid

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

# S3 code adapted from https://www.obytes.com/blog/image-resizing-on-the-fly-with-aws-lambda-api-gateway-and-s3-storage
s3 = boto3.resource('s3')
bucket = s3.Bucket('photomappr-storage')

def handler(event, context):

    # Get image in binary from api call, convert back and store in s3 bucket
    file_content = base64.b64decode(event['content'])
    # Generate unique image id
    file_path = str(uuid.uuid4()) + ".jpg" 
    try:
        s3_response = bucket.put_object(Key=file_path, Body=file_content)
    except Exception as e:
        raise IOError(e)
    
    # Load image file from bucket
    image = s3.Object(bucket_name = 'photomappr-storage', key=file_path)
    # Generate image url
    url = boto3.client('s3').generate_presigned_url('get_object', Params = {'Bucket': 'photomappr-storage', 'Key': file_path})
    image_url = url.split("?")
    image_url = image_url[0]
    # Open image with pillow
    obj_body = image.get()['Body'].read()
    img = Image.open(BytesIO(obj_body))

    # Exif tag code from https://stackoverflow.com/questions/4764932/in-python-how-do-i-read-the-exif-data-for-an-image
    exif = {}
    if img._getexif():
        exif = {
            ExifTags.TAGS[k]: v
            for k, v in img._getexif().items()
            if k in ExifTags.TAGS
        }

    # Image detection adapted from https://github.com/arunponnusamy/object-detection-opencv/blob/master/yolo_opencv.py
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
         
    lnames = net_obj.getLayerNames()                                                            
    layers = [lnames[i[0] - 1] for i in net_obj.getUnconnectedOutLayers()]                      
        
    blob = cv2.dnn.blobFromImage(image_np, 0.00392, (320, 320), (0, 0, 0), True, crop=False)     
            
    net_obj.setInput(blob)                                                                      
        
    detections = net_obj.forward(layers)                                                        
    
    for each_result in detections:                                                              
        for each in each_result:                                                                
            scores = each[5:]                                                                   
            class_id = np.argmax(scores)                                                        
            confidence = scores[class_id]                                                       
            if confidence > 0.5:                                                                                                            
                class_ids.append(class_id)

    arr = []
    if len(class_ids) > 0:
        for i in range(len(class_ids)):
            arr.append(labels[class_ids[i]])
   
    return {
        'url': image_url,
        'exif': exif,
        'objects': arr
    }