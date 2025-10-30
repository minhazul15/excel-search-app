from flask import Flask, request, jsonify, send_from_directory, session, redirect
from flask_cors import CORS
import sqlite3, os, hashlib

app = Flask(__name__, static_folder=os.path.join(os.getcwd(), 'static'))
app.secret_key = "super_secret_key"  # change in production
CORS(app)

DB = "ORDERMONKEY.db"

# ---------- Helper ----------
def run_query(query, args=(), one=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    return (dict(rows[0]) if rows else None) if one else [dict(row) for row in rows]

# ---------- Static Pages ----------
@app.route('/')
def index():
    if not session.get("user"):
        return redirect("/static/login.html")
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/insert')
def insert_page():
    if not session.get("user"):
        return redirect("/static/login.html")
    return send_from_directory(app.static_folder, 'insert.html')

@app.route('/edit')
def edit_page():
    if not session.get("user"):
        return redirect("/static/login.html")
    return send_from_directory(app.static_folder, 'edit.html')

@app.route('/static/login.html')
def login_page():
    return send_from_directory(app.static_folder, 'login.html')


# ---------- Auth System ----------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    hash_pw = hashlib.sha256(password.encode()).hexdigest()

    # Check if exists
    exists = run_query("SELECT * FROM users WHERE username=?", [username], one=True)
    if exists:
        return jsonify({"error": "User already exists"}), 400

    run_query("INSERT INTO users (username, password_hash, role, approved) VALUES (?, ?, ?, ?)",
              [username, hash_pw, "user", 0])  # initially not approved
    return jsonify({"message": "User registered successfully, Waiting for approval."})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    user = run_query("SELECT * FROM users WHERE username=?", [username], one=True)
    if not user:
        return jsonify({"error": "User not found"}), 404

    hash_pw = hashlib.sha256(password.encode()).hexdigest()
    if hash_pw != user["password_hash"]:
        return jsonify({"error": "Invalid password"}), 401

    if not user["approved"]:
        return jsonify({"error": "User not approved"}), 403

    session["user"] = {
        "username": user["username"],
        "role": user["role"],
    }

    return jsonify({"message": "Login successful", "role": user["role"]})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/static/login.html")


@app.route("/current_user", methods=["GET"])
def current_user():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401
    return jsonify(user)


@app.route("/reset_my_password", methods=["POST"])
def reset_my_password():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    new_password = data.get("new_password")
    if not new_password:
        return jsonify({"error": "New password required"}), 400

    hash_pw = hashlib.sha256(new_password.encode()).hexdigest()
    run_query("UPDATE users SET password_hash=? WHERE username=?", [hash_pw, user["username"]])
    return jsonify({"message": "Password changed successfully."})


@app.route("/change_username", methods=["POST"])
def change_username():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    new_username = data.get("new_username")
    if not new_username:
        return jsonify({"error": "New username required"}), 400

    # Check if username already exists
    exists = run_query("SELECT * FROM users WHERE username=?", [new_username], one=True)
    if exists:
        return jsonify({"error": "Username already taken"}), 400

    run_query("UPDATE users SET username=? WHERE username=?", [new_username, user["username"]])
    session["user"]["username"] = new_username
    return jsonify({"message": "Username changed successfully."})


# ---------- Admin Panel API ----------

# Endpoint to get all users, including their approval status
@app.route("/admin/users", methods=["GET"])
def get_users():
    if not session.get("user") or session["user"]["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    users = run_query("SELECT id, username, role, approved FROM users")
    return jsonify(users)

# Endpoint to approve a user
@app.route("/admin/approve/<int:id>", methods=["POST"])
def approve_user(id):
    if not session.get("user") or session["user"]["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    # Update the user's approval status to 1 (approved)
    run_query("UPDATE users SET approved = 1 WHERE id = ?", [id])
    return jsonify({"message": f"User with ID {id} approved successfully."})

# Endpoint to revoke a user's access
@app.route("/admin/revoke/<int:id>", methods=["POST"])
def revoke_user(id):
    if not session.get("user") or session["user"]["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    # Update the user's approval status to 0 (not approved)
    run_query("UPDATE users SET approved = 0 WHERE id = ?", [id])
    return jsonify({"message": f"User with ID {id} revoked access successfully."})


# ---------- Restaurant CRUD API ----------
@app.route('/columns', methods=['GET'])
def get_columns():
    conn = sqlite3.connect(DB)
    cursor = conn.execute('PRAGMA table_info(restaurants)')
    columns_info = cursor.fetchall()
    conn.close()
    columns = [{"name": col[1], "type": col[2], "notnull": bool(col[3]), "pk": bool(col[5])} for col in columns_info]
    return jsonify(columns)


@app.route('/search', methods=['GET'])
def search():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 401

    query = request.args.get('name', '').strip().lower()
    if not query:
        return jsonify([])

    like_query = f"%{query}%"
    rows = run_query("SELECT * FROM restaurants WHERE LOWER(`Location Name`) LIKE ?", [like_query])
    return jsonify(rows)


@app.route('/restaurant', methods=['POST'])
def create_restaurant():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    columns = ', '.join([f"`{k}`" for k in data.keys()])
    placeholders = ', '.join(['?'] * len(data))
    values = list(data.values())

    query = f"INSERT INTO restaurants ({columns}) VALUES ({placeholders})"
    try:
        run_query(query, values)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Restaurant added"}), 201


@app.route('/restaurant/edit/<int:id>', methods=['GET'])
def get_restaurant_for_edit(id):
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 401

    restaurant = run_query("SELECT * FROM restaurants WHERE id = ?", [id], one=True)
    if restaurant:
        return jsonify(restaurant)
    else:
        return jsonify({"error": "Restaurant not found"}), 404


@app.route('/restaurant/edit/save/<int:id>', methods=['POST'])
def save_restaurant(id):
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    set_clause = ', '.join([f"`{k}` = ?" for k in data.keys()])
    values = list(data.values()) + [id]

    query = f"UPDATE restaurants SET {set_clause} WHERE id = ?"
    try:
        run_query(query, values)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Restaurant updated successfully"}), 200


@app.route('/restaurant/delete/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        run_query("DELETE FROM restaurants WHERE id = ?", [id])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": f"Restaurant with ID {id} deleted successfully"}), 200


# Endpoint to delete a user
@app.route("/admin/delete/<int:id>", methods=["DELETE"])
def delete_user(id):
    if not session.get("user") or session["user"]["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    # Delete the user from the database
    run_query("DELETE FROM users WHERE id = ?", [id])
    return jsonify({"message": f"User with ID {id} deleted successfully."})



    # Endpoint to make a user an admin
@app.route("/admin/make_admin/<int:id>", methods=["POST"])
def make_admin(id):
    if not session.get("user") or session["user"]["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    # Update the user's role to 'admin'
    run_query("UPDATE users SET role = 'admin' WHERE id = ?", [id])
    return jsonify({"message": f"User with ID {id} is now an admin."})


# Endpoint to revoke admin privileges from a user
@app.route("/admin/revoke_admin/<int:id>", methods=["POST"])
def revoke_admin(id):
    if not session.get("user") or session["user"]["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    # Change the user's role to 'user'
    run_query("UPDATE users SET role = 'user' WHERE id = ?", [id])
    return jsonify({"message": f"Admin privileges revoked from user with ID {id}."})


# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)
