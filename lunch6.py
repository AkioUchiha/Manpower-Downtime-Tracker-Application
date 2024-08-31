from flask import Flask, render_template_string, request, jsonify
import time
import sqlite3

app = Flask(__name__)

# Store data in memory
casper_ids = []
delayed_ids = []
entry_times = {}
removed_count = 0

# HTML template with styling
template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Casper ID Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f8ff; /* Light blue background */
            color: #333;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            color: #002147; /* Navy blue */
        }
        input[type="text"] {
            padding: 10px;
            font-size: 16px;
            border: 2px solid #002147; /* Navy blue */
            border-radius: 5px;
            margin-right: 10px;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        button:nth-child(2) {
            background-color: #ffd700; /* Yellow */
            color: #002147; /* Navy blue */
        }
        button:nth-child(3) {
            background-color: #002147; /* Navy blue */
            color: #fff;
        }
        ul {
            list-style-type: none;
            padding: 0;
            width: 300px;
            text-align: left;
        }
        ul li {
            background-color: #ffd700; /* Yellow */
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            color: #002147; /* Navy blue */
        }
        h2, h3 {
            color: #002147; /* Navy blue */
        }
    </style>
    <script>
        function addCasperID() {
            const idInput = document.getElementById('idInput');
            const id = idInput.value.trim();

            if (id && /^\d+$/.test(id)) {
                fetch('/add_id', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ id: id }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        updateList(data);
                    }
                    idInput.value = ''; // Clear input field
                    idInput.focus(); // Return cursor to input field
                });
            } else {
                alert('Please enter a valid whole number as ID.');
                idInput.value = ''; // Clear input field
                idInput.focus(); // Return cursor to input field
            }
        }

        function clearDatabase() {
            fetch('/clear_database', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                updateList(data);
            });
        }

        function updateList(data) {
            const casperList = document.getElementById('casperList');
            const delayedList = document.getElementById('delayedList');
            const removedCount = document.getElementById('removedCount');
            const activeCount = document.getElementById('activeCount');
            casperList.innerHTML = '';
            delayedList.innerHTML = '';
            data.casper_ids.forEach(item => {
                const li = document.createElement('li');
                li.textContent = `${item.id} (Elapsed: ${item.elapsed_time} seconds)`;
                casperList.appendChild(li);
            });
            data.delayed_ids.forEach(id => {
                const li = document.createElement('li');
                li.textContent = id;
                delayedList.appendChild(li);
            });
            removedCount.textContent = 'Removed Count: ' + data.removed_count;
            activeCount.textContent = 'Active Casper IDs: ' + data.casper_ids.length;
        }

        setInterval(() => {
            fetch('/get_ids')
            .then(response => response.json())
            .then(data => {
                updateList(data);
            });
        }, 1000);
    </script>
</head>
<body>
    <h1>Casper ID Tracker</h1>
    <input type="text" id="idInput" placeholder="Enter Casper ID">
    <button onclick="addCasperID()">Add Casper ID</button>
    <button onclick="clearDatabase()">Clear Database</button>
    <h2>Active Casper IDs</h2>
    <h3 id="activeCount">Active Casper IDs: 0</h3>
    <ul id="casperList"></ul>
    <h2>Delayed Arrivals</h2>
    <ul id="delayedList"></ul>
    <h3 id="removedCount">Removed Count: 0</h3>
</body>
</html>
"""

def add_to_database(id):
    conn = sqlite3.connect('delayed_ids.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delayed_ids (
            id TEXT PRIMARY KEY,
            count INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        INSERT INTO delayed_ids (id)
        VALUES (?)
        ON CONFLICT(id) DO UPDATE SET count = count + 1
    ''', (id,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string(template)

@app.route('/add_id', methods=['POST'])
def add_id():
    global removed_count
    id = request.json['id']
    
    if not id.isdigit():
        return jsonify({'error': 'ID must be a whole number.'})
    
    current_time = time.time()

    if id in entry_times and (current_time - entry_times[id]) > 30:
        casper_ids.remove(id)
        entry_times.pop(id)
        removed_count += 1
    elif id not in entry_times:
        casper_ids.append(id)
        entry_times[id] = current_time

    return jsonify({
        'casper_ids': [{'id': id, 'elapsed_time': int(time.time() - entry_times[id])} for id in casper_ids],
        'delayed_ids': delayed_ids,
        'removed_count': removed_count
    })

@app.route('/clear_database', methods=['POST'])
def clear_database():
    global casper_ids, delayed_ids, entry_times, removed_count
    casper_ids = []
    delayed_ids = []
    entry_times = {}
    removed_count = 0
    conn = sqlite3.connect('delayed_ids.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM delayed_ids')
    conn.commit()
    conn.close()
    return jsonify({
        'casper_ids': casper_ids,
        'delayed_ids': delayed_ids,
        'removed_count': removed_count
    })

@app.route('/get_ids', methods=['GET'])
def get_ids():
    current_time = time.time()
    for id in casper_ids:
        if id not in delayed_ids and (current_time - entry_times[id]) > 45:
            delayed_ids.append(id)
            add_to_database(id)

    return jsonify({
        'casper_ids': [{'id': id, 'elapsed_time': int(time.time() - entry_times[id])} for id in casper_ids],
        'delayed_ids': delayed_ids,
        'removed_count': removed_count
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
