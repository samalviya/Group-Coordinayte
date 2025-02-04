from flask import Flask, render_template, request, jsonify, send_file, session  # Add `session`
import csv
import io
import pandas as pd
import uuid  # To generate unique session IDs
from datetime import timedelta
from flask_session import Session

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions on disk (better than cookies for multiple users)
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Session lasts 1 day
app.secret_key = 'your_secret_key'  # Change this to a secure key

Session(app)  # Initialize Flask-Session

# In-memory data store for points
points = []

def read_csv(file):
    global points
    points.clear()
    # Load the uploaded CSV into a DataFrame
    df = pd.read_csv(file)

    # Check the column names in the DataFrame (debugging)
    print(f"CSV Columns: {df.columns.tolist()}")

    # Process each row and add it to the points list
    for _, row in df.iterrows():
        lat, lng = map(float, row["GPS Location"].split(","))
        points.append({
            "id": row["FormId"],
            "coordinates": [lat, lng],
            "name": f"Point {row['FormId']}",
            "color": "blue"
        })

@app.route('/')
def index():
    # Get session ID from URL parameter
    session_id = request.args.get("session_id")

    # Generate a new session if not provided
    if not session_id:
        session_id = str(uuid.uuid4())

    # Store session ID
    session['session_id'] = session_id

    return render_template('map.html', session_id=session_id)
    
@app.route('/get_points', methods=['GET'])
def get_points():
    return jsonify(points)

@app.route('/update_points', methods=['POST'])
def update_points():
    data = request.json
    updated_points = data.get('points', [])
    for updated in updated_points:
        for point in points:
            if point['id'] == updated['id']:
                point['name'] = updated['name']
                point['color'] = updated['color']
    return jsonify({"status": "success"})

@app.route('/export_csv', methods=['GET'])
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Latitude", "Longitude", "Name", "Color"])
    for point in points:
        writer.writerow([point["id"], point["coordinates"][0], point["coordinates"][1], point["name"], point["color"]])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="updated_points.csv",
    )

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    # Read the uploaded CSV file and update the points
    read_csv(file)
    return jsonify({"status": "success", "points": points})

if __name__ == '__main__':
    app.run(debug=True)
