from tinymongo import TinyMongoClient

# you can include a folder name or absolute path
# as a parameter if not it will default to "tinydb"
connection = TinyMongoClient()

# either creates a new database file or accesses an existing one named `my_tiny_database`
db = connection.my_tiny_database

# either creates a new collection or accesses an existing one named `users`
collection = db.users

# insert data adds a new record returns _id
record_id = collection.insert_one({"username": "admin", "password": "admin", "module":"somemodule"}).inserted_id
user_info = collection.find_one({"_id": record_id})  # returns the record inserted

# you can also use it directly
db.users.insert_one({"username": "admin"})

# returns a list of all users of 'module'
users = db.users.find({'module': 'module'})

#update data returns True if successful and False if unsuccessful
upd = db.users.update_one({"username": "admin"}, {"$set": {"module":"someothermodule"}})

# Sorting users by its username DESC
# omitting `filter` returns all records
db.users.find(sort=[('username', -1)])

# Pagination of the results
# Getting the first 20 records
db.users.find(sort=[('username', -1)], skip=0, limit=20)
# Getting next 20 records
db.users.find(sort=[('username', -1)], skip=20, limit=20)

# Getting the total of records
db.users.count
