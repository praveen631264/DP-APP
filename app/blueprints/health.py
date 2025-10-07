
from flask import Blueprint, jsonify

health_bp = Blueprint('health_bp', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health Check
    ---
    tags:
      - Health
    summary: Check if the service is running.
    description: Returns a 200 OK status to indicate the service is running.
    responses:
      200:
        description: Service is running.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: ok
    """
    return jsonify({"status": "ok"}), 200
