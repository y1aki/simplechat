import json
import os
import urllib.request
import re

# ARNからリージョン抽出
def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    return match.group(1) if match else "us-east-1"

MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-lite-v1:0")
API_URL = os.environ.get("API_URL", "https://9a15-34-13-134-84.ngrok-free.app")

def lambda_handler(event, context):
    try:
        region = extract_region_from_arn(context.invoked_function_arn)
        print(f"Initialized for region: {region}")

        print("Received event:", json.dumps(event))

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # 会話履歴を使う
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": message})

        # 外部API用のリクエストペイロード作成
        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        req = urllib.request.Request(
            API_URL,
            data=json.dumps(request_payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req) as res:
            response_body = json.loads(res.read().decode('utf-8'))

        print("API response:", json.dumps(response_body, indent=2))

        if 'generated_text' not in response_body:
            raise Exception("No 'generated_text' in API response")

        assistant_response = response_body['generated_text']

        # assistantメッセージを履歴に追加
        messages.append({"role": "assistant", "content": assistant_response})

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({"success": False, "error": str(error)})
        }
