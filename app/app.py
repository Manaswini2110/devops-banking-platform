
from flask import Flask, render_template, jsonify, request
from db import get_db_connection

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("base.html")


# GET API - Fetch all customers from PostgreSQL
@app.route("/api/customers", methods=["GET"])
def get_customers():

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, email, account_type
                FROM customers
                ORDER BY id;
            """)

            rows = cur.fetchall()

    customers = [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "account_type": row[3]
        }
        for row in rows
    ]

    return jsonify(customers)


# POST API - Add a customer to PostgreSQL
@app.route("/api/customers", methods=["POST"])
def add_customer():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    name = data.get("name")
    email = data.get("email")
    account_type = data.get("account_type")

    if not name or not email or not account_type:
        return jsonify({"error": "All customer fields are required"}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO customers (name, email, account_type)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, email, account_type;
                """, (name, email, account_type))

                row = cur.fetchone()

    except Exception as error:
        import psycopg
        if isinstance(error, psycopg.errors.UniqueViolation):
            return jsonify({"error": "Email already exists"}), 409
        raise

    new_customer = {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "account_type": row[3]
    }

    return jsonify({
        "message": "Customer created successfully",
        "customer": new_customer
    }), 201


# PUT API - Update a customer in PostgreSQL
@app.route("/api/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    name = data.get("name")
    email = data.get("email")
    account_type = data.get("account_type")

    if not name or not email or not account_type:
        return jsonify({"error": "All customer fields are required"}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE customers
                SET name = %s, email = %s, account_type = %s
                WHERE id = %s
                RETURNING id, name, email, account_type;
            """, (name, email, account_type, customer_id))

            row = cur.fetchone()

    if row is None:
        return jsonify({"error": "Customer not found"}), 404

    updated_customer = {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "account_type": row[3]
    }

    return jsonify({
        "message": "Customer updated successfully",
        "customer": updated_customer
    }), 200


# DELETE API - Delete a customer from PostgreSQL
@app.route("/api/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM customers
                WHERE id = %s
                RETURNING id, name, email, account_type;
            """, (customer_id,))

            row = cur.fetchone()

    if row is None:
        return jsonify({"error": "Customer not found"}), 404

    deleted_customer = {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "account_type": row[3]
    }

    return jsonify({
        "message": "Customer deleted successfully",
        "customer": deleted_customer
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
