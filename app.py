from flask import Flask, redirect, render_template, request, jsonify
from flask_cors import CORS
import logic
app = Flask(__name__)
cors = CORS(app)

cashback_percent = 0.05

@app.route('/')
def hello():
    return render_template('home.html')

@app.route('/new_account',methods=['GET','POST'])
def new_account():
    if request.method == 'POST':
        # take name and role from request body
        name = request.form['name']
        logic.create_new_account(name)
        return redirect('/')
    else:
        return render_template('new_account.html')

@app.route("/transfer_coin_from_admin",methods=['POST'])
def tr_coin_from_admin():
    name, amt = request.form['name'], float(request.form['amt'])
    logic.transfer_coin_from_admin(name, round(amt,2))
    return "OK"

@app.route("/admin_bal", methods = ['GET'])
def admin_bal():
    # will print in terminal
    logic.get_admin_account_assets()
    return "YES"

@app.route("/new_booking",methods=['GET','POST'])
def new_booking():
    global cashback_percent
    ## for Get
    if request.method == 'GET':
        return render_template('new_booking.html')
    else:
        redeem = int(request.form['redeem'])
        if redeem == 1:
            name = request.form['name']
            host = request.form['host']
            amount = float(request.form['amount'])
            account_bal = float(logic.get_account_coin_data(name))
            if(account_bal > 0):
                print("\n\nYes\n\n")
                coin_deduct = account_bal if amount > account_bal else account_bal - amount
                logic.transfer_coin(name,host,round(coin_deduct,2),f'New Booking from {name} to {host}')
            print("here")
            logic.add_coin_to_admin(round(amount*cashback_percent,2))
            print("here-2")
            logic.transfer_coin_from_admin(name, round(amount*cashback_percent,2))
            resp = logic.get_account_coin_data(name)
            redirect('/')

@app.route("/view_account_details",methods=["GET","POST"])
def get_account_details():
    if request.method == 'GET':
        pass
    else:
        name = request.form['name']
        return logic.get_account_details(name)

@app.route("/view_account_bal",methods=['GET','POST'])
def get_account_bal():
    if request.method == 'POST':
        name = request.form['name']
        resp = logic.get_account_coin_data(name)
        print(resp)
        redirect('/')
    else:
        return render_template('view_account_bal.html', value="Select account!")

@app.route("/view_transactions",methods=["GET"])
def get_transactions():
    return str(logic.query_transactions_user())

@app.route("/view_transactions_admin",methods=["GET"])
def get_transactions_admin():
    return str(logic.query_transactions())

if __name__ == "__main__":
    app.run(host='0.0.0.0')
