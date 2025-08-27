from flask import jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register application error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            'error': 'Conflict',
            'message': 'The request conflicts with the current state of the resource',
            'status_code': 409
        }), 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': 'The request was well-formed but contains semantic errors',
            'status_code': 422
        }), 422
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    @app.errorhandler(ValidationError)
    def validation_error(error):
        return jsonify({
            'error': 'Validation Error',
            'message': 'Request data validation failed',
            'details': error.messages,
            'status_code': 400
        }), 400
    
    @app.errorhandler(ValueError)
    def value_error(error):
        return jsonify({
            'error': 'Invalid Value',
            'message': str(error),
            'status_code': 400
        }), 400
    
    @app.errorhandler(HTTPException)
    def http_exception(error):
        return jsonify({
            'error': error.name,
            'message': error.description,
            'status_code': error.code
        }), error.code
