from flask import Flask,jsonify,request
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import certifi
from flask_cors import CORS



app=Flask(__name__)

CORS(app)

#Mogodb Database

client =MongoClient("mongodb+srv://myAtlasDBUser:Sai123@myatlasclusteredu.qifwasp.mongodb.net/python?retryWrites=true&w=majority",tlsCAFile=certifi.where())
db=client['expense-tracker']
expense_collection = db['expenses']
counter_collection = db['counters']

if counter_collection.count_documents({'_id': 'expenseId'}) == 0:
    counter_collection.insert_one({
        '_id': 'expenseId',
        'sequence_value': 0
    })

@app.route("/",methods=["GET"])
def HomeRoute():
    return jsonify("Hello World")

@app.route("/add-expenses", methods=["POST"])
def AddExpense():
    data = request.json
    date = data.get("date")
    amount = data.get("amount")
    category = data.get("category")
    description = data.get("description")
    
    if not all([date, amount, category, description]):
        return jsonify({'error': "All Fields Required"}), 400
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'error': 'Amount must be a valid number'}), 400
    
    # Get the next ID from the counter collection
    counter = counter_collection.find_one_and_update(
        {'_id': 'expenseId'},
        {'$inc': {'sequence_value': 1}},
        return_document=True
    )
    
    if counter is None:
        return jsonify({'error': 'Could not retrieve or update the counter'}), 500
    
    next_id = counter['sequence_value']
    
    expense = {
        'id': next_id,  # Use the new ID
        'date': date,
        'amount': amount,
        'category': category,
        'description': description
    }
    
    result = expense_collection.insert_one(expense)
    return jsonify({'id': str(result.inserted_id), 'message': 'Expense added successfully'}), 201


@app.route('/expenses', methods=['GET'])
def get_all_expenses():
    expenses = list(expense_collection.find())
    for expense in expenses:
        expense['_id'] = str(expense['_id'])  # Convert ObjectId to string for JSON serialization
    return jsonify(expenses), 200

def filter_expenses():
    date = request.args.get('date')
    category = request.args.get('category')
    query = {}
    
    if date:
        query['date'] = date
    if category:
        query['category'] = category

    filtered_expenses = list(expense_collection.find(query))
    for expense in filtered_expenses:
        expense['_id'] = str(expense['_id'])
    return jsonify(filtered_expenses), 200


@app.route('/expenses/total', methods=['GET'])
def calculate_total():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'Both start_date and end_date are required'}), 400
    
    # Convert dates to datetime objects for comparison
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Date format must be YYYY-MM-DD'}), 400

    # Query expenses within the date range
    total = 0
    expenses_in_range = expense_collection.find({
        'date': {
            '$gte': start_date.strftime('%Y-%m-%d'),
            '$lte': end_date.strftime('%Y-%m-%d')
        }
    })

    for expense in expenses_in_range:
        total += expense['amount']

    return jsonify({'total': total}), 200

    
if __name__ =='__main__':
     app.run(host='0.0.0.0', port=5000, debug=True)