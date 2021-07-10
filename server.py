from flask import Flask, request, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import os
app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get("DATABASE_URL",  "sqlite:///blog.db")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# making the tables
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    current_balance = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<id={self.id}, name={self.name}, email={self.email}, current_balance={self.current_balance}>"


class Transfers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    to_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    amt = db.Column(db.Float, nullable=False)
    from_acc = db.relationship('Customer', foreign_keys=[from_id])
    to_acc = db.relationship('Customer', foreign_keys=[to_id])


db.create_all()


# Routes
# /
# /register
# /customers
# /customers/id
# /transfer
# /delete


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        try:
            int(request.form.get('balance'))
        except:
            flash("Please enter a valid numeric amount!")
            return redirect(url_for('register'))
        new_bal = request.form.get('balance')

        if Customer.query.filter_by(email=new_email).first():
            # Email already exists
            flash("You've already signed up with that email!")
            return redirect(url_for('home'))
        elif Customer.query.filter_by(email=new_name).first():
            # User already exists
            flash("Your account already exists!")
            return redirect(url_for('home'))
        else:
            new_customer = Customer(name=new_name, email=new_email, current_balance=new_bal)
            db.session.add(new_customer)
            db.session.commit()
            flash("User made! Welcome to the Sparking Network!")
            return redirect(url_for('all_customers'))
    return render_template('register.html')


@app.route('/delete/<del_id>', methods=['POST'])
def delete(del_id):
    account_to_delete = Customer.query.get(del_id)
    all_from_transfers = Transfers.query.filter_by(from_id=del_id).all()
    all_to_transfers = Transfers.query.filter_by(to_id=del_id).all()
    if all_from_transfers:
        print(all_from_transfers)
        for single in all_from_transfers:
            db.session.delete(single)
    elif all_to_transfers:
        print(all_to_transfers)
        for single in all_to_transfers:
            db.session.delete(single)
    else:
        print('No transfers from this user')
    db.session.delete(account_to_delete)
    db.session.commit()
    return redirect(url_for('all_customers'))


@app.route('/customers')
def all_customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)


@app.route('/customers/<int:show_id>')
def show_customer(show_id):
    view_customer = Customer.query.get(show_id)
    return render_template('show.html', customer=view_customer)


@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if request.method == 'POST':
        # collecting data entered via form
        from_acc = request.form.get('from')
        to_acc = request.form.get('to')
        try:
            int(request.form.get('amount'))
        except:
            flash("Please enter a valid numeric amount!")
            return redirect(url_for('transfer'))

        transfer_amt = int(request.form.get('amount'))
        print(f'{from_acc} is transferring {transfer_amt} to {to_acc}')

        # checking if from account exists
        if not Customer.query.filter_by(name=from_acc).first():
            flash(f"An account with the name {request.form.get('from')} doesn't exist, you can register instead.")
            return redirect(url_for('register'))
        print(Customer.query.filter_by(name=from_acc).first())
        from_account = Customer.query.filter_by(name=from_acc).first()

        # checking if from account exists
        if not Customer.query.filter_by(name=to_acc).first():
            flash(f"An account with the name {request.form.get('to')} doesn't exist, kindly re-asses the name.")
            return redirect(url_for('all_customers'))
        to_account = Customer.query.filter_by(name=to_acc).first()

        # checking if the account has enough funds
        if transfer_amt > from_account.current_balance:
            flash(f"You don't have sufficient funds to make that transaction, please check your balance below.")
            return redirect(url_for('all_customers'))

        # transferring money
        from_account.current_balance = from_account.current_balance - transfer_amt
        to_account.current_balance += transfer_amt
        record = Transfers(
            from_id=from_account.id,
            to_id=to_account.id,
            amt=transfer_amt
        )
        db.session.add(record)
        db.session.commit()
        flash(f'Successfully transferred ₹{transfer_amt} to {to_account.name}')
        return redirect(url_for('all_customers'))
    return render_template('transfer.html')


if __name__ == '__main__':
    app.run(debug=True)
