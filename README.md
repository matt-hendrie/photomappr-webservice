# photomappr-webservice
AWS-hosted webservice for photomappr

To test use the following command:

curl --request POST -H "Content-Type: image/jpg" --data-binary "@IMAGE_FILE" https://gcgyw21swk.execute-api.us-east-1.amazonaws.com/default/photomappr-tagger

Currently only supports png/jpg images
