# Code to auto-confirm users when registering, used to make testing easier
# This code was adapted from https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-sign-up.html#aws-lambda-triggers-pre-registration-example-2
def lambda_handler(event, context):
    # Confirm the user
    event['response']['autoConfirmUser'] = True

    # Set the email as verified if it is in the request
    if 'email' in event['request']['userAttributes']:
        event['response']['autoVerifyEmail'] = True

    # Return to Amazon Cognito
    return event