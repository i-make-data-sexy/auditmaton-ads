# ========================================================================
#   Imports
# ======================================================================== 

from flask import Flask, render_template, request, jsonify, make_response
import logging
import os
import json

# ========================================================================
#   Configure Logging
# ======================================================================== 

# Configure logging to display timestamps, log level, and messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ========================================================================
#   Disable Caching
# ======================================================================== 

# Initialize Flask app with static file configuration
app = Flask(__name__, 
            static_url_path='/static', 
            static_folder='static')

# Set secret key for session management
app.secret_key = os.urandom(24)

# Disable caching for development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Enable debug mode for better error messages
app.config['DEBUG'] = True      

# Configure route
app.config['APPLICATION_ROOT'] = '/tools/ml-model-picker'

# Log request headers and body before processing each request
@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())
    


# ========================================================================
#   Routes
# ======================================================================== 

# Home route - loads and renders the flowchart data
@app.route('/')
@app.route('/<path:path>')
def index(path=None):
    try:
        # Load algorithm data from JSON file
        with open('algorithm_data.json') as f:
            flowchart_data = json.load(f)
            
        # Log the structure of loaded data
        app.logger.info(f"Loaded flowchart data structure: {json.dumps(flowchart_data)[:200]}...")
        app.logger.info(f"Available primary objectives: {list(flowchart_data.get('options', {}).keys())}")
        
        # Render the template with flowchart data
        response = render_template(
            'index.html',
            flowchart_data=json.dumps(flowchart_data)
        )
        
        # Add cache-control headers to prevent caching
        response = make_response(response)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        # Log and return error message if loading fails
        app.logger.error(f"Error in index route: {str(e)}", exc_info=True)
        return render_template(
            'index.html',
            error=str(e),
            flowchart_data='{}'
        )

# API route - retrieves a specific algorithm by ID
@app.route('/api/algorithm/<algorithm_id>')
def get_algorithm(algorithm_id):
    try:
        # Load algorithm data from JSON file
        with open('algorithm_data.json') as f:
            algorithm_data = json.load(f)
            
        # Find the requested algorithm by ID
        algorithm = next((a for a in algorithm_data['algorithms'] 
                         if a['id'] == algorithm_id), None)
        
        if algorithm:
            return jsonify(algorithm)
            
        # Return error if algorithm is not found
        return jsonify({'error': 'Algorithm not found'}), 404
        
    except Exception as e:
        # Log and return error message
        logging.error(f"Error fetching algorithm {algorithm_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route for filtering data based on node ID
@app.route('/filter_data', methods=['POST'])
def filter_data():
    try:
        app.logger.info(f"Filter data request received")
        
        # Extract node ID from the request payload
        node_id = request.json.get('node_id')
        if not node_id:
            app.logger.error("No node ID provided")
            return jsonify({"error": "No node ID provided"}), 400

        # Load algorithm data from JSON file
        with open('algorithm_data.json') as f:
            algorithm_data = json.load(f)
            
        app.logger.info(f"Processing node ID: {node_id}")

        # Process node ID if it follows expected format
        if node_id.startswith('node_'):
            # Extract category and subcategory from node ID
            parts = node_id.split('_')
            if len(parts) < 3:
                app.logger.error(f"Invalid node ID format: {node_id}")
                return jsonify({"error": "Invalid node ID format"}), 400

            # Search the algorithm data for the matching node
            # This logic needs to be implemented based on data structure
            for category in algorithm_data['options']:
                for objective in algorithm_data['options'][category]['objectives']:
                    # Add logic here to find matching node
                    pass

        # Log and return error if node is not found
        app.logger.error(f"Node not found: {node_id}")
        return jsonify({"error": "Node not found"}), 404
    
    except Exception as e:
        # Log and return error message
        app.logger.error(f"Error in filter_data route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
# Define both prefixed and non-prefixed versions of routes
@app.route('/tips')
@app.route('/tools/ml-model-picker/tips')
def tips():
    return render_template('tips.html')

@app.route('/methodology')
@app.route('/tools/ml-model-picker/methodology')
def methodology():
    return render_template('methodology.html')

@app.route('/resources')
@app.route('/tools/ml-model-picker/resources')
def resources():
    return render_template('resources.html')

@app.route('/feedback')
@app.route('/tools/ml-model-picker/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/debug-path')
def debug_path():
    from flask import request
    
    # Collect debugging information
    debug_info = {
        "script_root": request.script_root,
        "path": request.path,
        "full_path": request.full_path,
        "url": request.url,
        "base_url": request.base_url,
        "url_root": request.url_root,
        "headers": dict(request.headers),
        "application_root": app.config.get('APPLICATION_ROOT'),
        "server_name": app.config.get('SERVER_NAME')
    }
    
    # Format as HTML for easy viewing
    html = "<h1>Flask Path Debugging</h1>"
    html += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
    html += "<tr><th style='padding: 8px; text-align: left;'>Property</th><th style='padding: 8px; text-align: left;'>Value</th></tr>"
    
    for key, value in debug_info.items():
        html += f"<tr><td style='padding: 8px;'>{key}</td><td style='padding: 8px;'>{value}</td></tr>"
    
    html += "</table>"
    return html

# ========================================================================
#   Run
# ======================================================================== 

# Start in debug mode
if __name__ == '__main__':
    app.run(debug=True)