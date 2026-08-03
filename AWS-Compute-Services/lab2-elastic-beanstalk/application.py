import os
import socket

import boto3
from botocore.exceptions import ClientError
from flask import Flask, jsonify


application = Flask(__name__)

AWS_REGION = os.environ.get("AWS_REGION", "eu-north-1")
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "eb-app-visits")

_dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
_table = _dynamodb.Table(DYNAMODB_TABLE_NAME)


def get_version() -> str:
    """Read the version string baked in at deploy time by GitHub Actions.
    Falls back to a local-dev marker when running outside a real deploy."""
    try:
        with open("VERSION", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "local-dev"


def increment_visit_counter():
    """Atomically increments a single counter item in DynamoDB and returns
    the new total. This is the app's proof of external-service connectivity."""
    try:
        response = _table.update_item(
            Key={"counter_id": "total_visits"},
            UpdateExpression="ADD visit_count :inc",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(response["Attributes"]["visit_count"])
    except ClientError as e:
        return f"dynamodb_error: {e.response['Error']['Code']}"


@application.route("/")
def home():
    visits = increment_visit_counter()
    return jsonify(
        {
            "message": "Elastic Beanstalk Python app is running",
            "version": get_version(),
            "hostname": socket.gethostname(),
            "total_visits": visits,
        }
    )


@application.route("/version")
def version():
    return jsonify({"version": get_version()})


@application.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8000)
