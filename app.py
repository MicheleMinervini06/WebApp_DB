from flask import Flask, render_template, request, redirect, url_for
import oracledb  # Modifica qui
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ORACLE_USER = os.getenv('ORACLE_USER', 'system')
ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', 'password123')
ORACLE_DSN = os.getenv('ORACLE_DSN', 'localhost:1521/xe')

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Users\mikim\Downloads\instantclient_23_6")
except Exception as e:
    print("Using thin mode:", e)
    oracledb.init_oracle_client(lib_dir=None)

def get_db_output(cursor):
    lines = []
    status_var = cursor.var(oracledb.NUMBER)
    line_var = cursor.var(str)

    while True:
        cursor.callproc("dbms_output.get_line", (line_var, status_var))
        if status_var.getvalue() != 0:
            break
        lines.append(line_var.getvalue())
    return '\n'.join(lines)


@app.route('/')
def index():
    return render_template('index.html')


from datetime import datetime

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    conn = None
    cursor = None
    try:
        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        cursor = conn.cursor()

        # Get the current maximum customer ID
        cursor.execute("SELECT NVL(MAX(customer_id), 0) FROM Customers")  # Replace 'Customers' with your table name
        max_id = cursor.fetchone()[0]
        next_customer_id = max_id + 1

        if request.method == 'POST':
            # Convert the date of birth (if provided)
            dob = request.form.get('dob')  # Expected format: YYYY-MM-DD from HTML date input
            dob_converted = None
            if dob:
                try:
                    dob_converted = datetime.strptime(dob, '%Y-%m-%d')
                except ValueError as e:
                    return render_template('register_customer.html', error=f"Invalid DOB format: {e}")

            params = {
                'p_customer_id': next_customer_id,
                'p_email': request.form['email'],
                'p_phone': request.form['phone'],
                'p_customer_type': request.form['customer_type'],
                'p_name': request.form.get('name'),
                'p_surname': request.form.get('surname'),
                'p_dob': dob_converted,
                'p_company_name': request.form.get('company_name'),
                'p_vat_number': request.form.get('vat_number')
            }

            cursor.callproc('dbms_output.enable')

            # Call the procedure
            cursor.callproc('Register_New_Customer', [
                params['p_customer_id'],
                params['p_email'],
                params['p_phone'],
                params['p_customer_type'],
                params['p_name'],
                params['p_surname'],
                params['p_dob'],
                params['p_company_name'],
                params['p_vat_number']
            ])

            output = get_db_output(cursor)
            conn.commit()
            return render_template('register_customer.html', result=f"Customer ID {next_customer_id} registered successfully.\n\n{output}")

    except oracledb.DatabaseError as e:
        error, = e.args
        return render_template('register_customer.html', error=error.message)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('register_customer.html')




from datetime import datetime

@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    conn = None
    cursor = None
    account_codes = []  # Initialize as an empty list to avoid UnboundLocalError
    try:
        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        cursor = conn.cursor()

        # Fetch available business account codes

        cursor.execute("SELECT accountcode FROM BusinessAccounts FETCH FIRST 50 ROWS ONLY")
        account_codes = [row[0] for row in cursor.fetchall()]  # Extract only account codes

        # Compute the next order number
        cursor.execute("SELECT NVL(MAX(order_num), 0) FROM ActiveOrder")  # Replace 'ActiveOrder' with your table name
        max_order_num = cursor.fetchone()[0]
        next_order_num = max_order_num + 1

        if request.method == 'POST':
            # Get and validate form data
            try:
                order_date = request.form.get('order_date', datetime.today().strftime('%Y-%m-%d'))
                expected_date = request.form.get('expected_date')
                order_date_parsed = datetime.strptime(order_date, '%Y-%m-%d')
                expected_date_parsed = datetime.strptime(expected_date, '%Y-%m-%d') if expected_date else None
            except ValueError as e:
                return render_template('add_order.html', account_codes=account_codes, error=f"Invalid date format: {e}")

            # Collect parameters
            params = {
                'p_order_num': next_order_num,
                'p_order_type': request.form['order_type'],
                'p_order_date': order_date_parsed,
                'p_expected_date': expected_date_parsed,
                'p_cost': float(request.form['cost']),
                'p_placement_modality': request.form['placement_modality'],
                'p_team_id': None,  # Pass NULL for team_id
                'p_account_code': int(request.form['account_code']),
                'p_state': request.form['state']
            }

            cursor.callproc('dbms_output.enable')
            cursor.callproc('Add_New_Order', [
                params['p_order_num'],
                params['p_order_type'],
                params['p_order_date'],
                params['p_expected_date'],
                params['p_cost'],
                params['p_placement_modality'],
                params['p_team_id'],  # Pass None for NULL
                params['p_account_code'],
                params['p_state']
            ])

            output = get_db_output(cursor)
            conn.commit()
            return render_template('add_order.html', account_codes=account_codes, result=f"Order {params['p_order_num']} added successfully.\n\n{output}")

    except oracledb.DatabaseError as e:
        error, = e.args
        return render_template('add_order.html', account_codes=account_codes, error=error.message)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('add_order.html', account_codes=account_codes)








@app.route('/assign_order', methods=['GET', 'POST'])
def assign_order():
    conn = None
    cursor = None
    orders_without_team = []  # Initialize as empty to avoid UnboundLocalError
    teams = []  # Initialize as empty to avoid UnboundLocalError

    try:
        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        cursor = conn.cursor()

        # Fetch orders without a team
        cursor.execute("""
            SELECT order_num
            FROM ActiveOrder
            WHERE team IS NULL
        """)
        orders_without_team = [row[0] for row in cursor.fetchall()]  # Extract order numbers

        # Fetch available teams
        cursor.execute("""
            SELECT team_id
            FROM Teams
        """)
        teams = [row[0] for row in cursor.fetchall()]  # Extract team IDs

        if request.method == 'POST':
            # Get form data
            order_num = int(request.form['order_num'])
            team_id = int(request.form['team_id'])

            # Call the stored procedure to assign the order to the team
            cursor.callproc('dbms_output.enable')
            cursor.callproc('Assign_Order_To_Team', [order_num, team_id])

            output = get_db_output(cursor)
            conn.commit()
            return render_template(
                'assign_order.html',
                orders=orders_without_team,
                teams=teams,
                result=f"Order {order_num} successfully assigned to Team {team_id}.\n\n{output}"
            )

    except oracledb.DatabaseError as e:
        error, = e.args
        return render_template(
            'assign_order.html',
            orders=orders_without_team,
            teams=teams,
            error=error.message
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('assign_order.html', orders=orders_without_team, teams=teams)



@app.route('/view_operations', methods=['GET', 'POST'])
def view_operations():
    conn = None
    cursor = None
    teams = []  # Initialize to avoid UnboundLocalError
    operations_summary = None

    try:
        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        cursor = conn.cursor()

        # Fetch available teams
        cursor.execute("SELECT team_id, name FROM Teams")
        teams = cursor.fetchall()  # List of tuples (team_id, team_name)

        if request.method == 'POST':
            # Get the selected team ID
            team_id = int(request.form['team_id'])

            # Call the stored procedure to fetch operations summary
            cursor.callproc('dbms_output.enable')
            cursor.callproc('View_Team_Operations', [team_id])

            # Fetch output from DBMS_OUTPUT
            operations_summary = get_db_output(cursor)

            return render_template(
                'view_operations.html',
                teams=teams,
                result=operations_summary
            )

    except oracledb.DatabaseError as e:
        error, = e.args
        return render_template(
            'view_operations.html',
            teams=teams,
            error=error.message
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('view_operations.html', teams=teams)



@app.route('/team_performance')
def team_performance():
    conn = None
    cursor = None
    try:
        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        cursor = conn.cursor()
        cursor.callproc('dbms_output.enable')

        cursor.callproc('Print_Teams_Sorted_By_Performance')

        output = get_db_output(cursor)
        return render_template('team_performance.html', result=output)

    except oracledb.DatabaseError as e:
        error, = e.args
        return render_template('team_performance.html', error=error.message)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
