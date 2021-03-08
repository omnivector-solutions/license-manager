"""
A custom (lambda) authorizer for API gateway
"""


def handler(event, context):
    print("==================")
    if not event.get('methodArn'):
        print("☁️ ☁️ ☁️ cloudwatch keep-warm ping ☁️ ☁️ ☁️")
        return {}

    for k in event:
        print(f'{k}: {event[k]}')

    permitted = True

    arn_ = event['methodArn']

    l, r = arn_.rsplit(':', 1)
    id, stage, method, path = r.split('/', 3)
    arn = f'{l}:{id}/{stage}/*'
    if permitted:
        print(f"🔓 permitted for: {arn}")
        return permit(arn)
    else:
        print(f"❌ denied for: {arn}")
        return deny(arn)


def permit(arn):
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": arn
                }
            ]
        }
    }


def deny(arn):
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": arn
                }
            ]
        }
    }
