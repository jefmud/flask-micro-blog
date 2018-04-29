# super simple pymongo contact list program
# pretty useless, except to help me remember how to
# run some simple Mongo code
# Spring 2018
# by JM

import pymongo
import easygui as g
import sys

client = pymongo.MongoClient("--your mongo connection string goes here--")

db = client.cool_db

def make_query(prompt="Enter a parameter and a value to find an item"):
    query = g.enterbox(prompt)
    if query:

        q = query.split("=")
        try:
            # example contacts = db.contacts.find({'home':'Sunnyvale'})
            qdict = {q[0]:q[1]}
            contacts = db.contacts.find(qdict)
            return list(contacts), qdict
        except:
            g.msgbox("Malformed query")

    return None


g.msgbox("Welcome to Mongo Contact list program")
contacts = []
while True:
    prompt = """
    ALL) All Contacts
    ADD) Add a Contact
    SEL) Select a contact
    DEL) Delete selected contact
    QUIT) Quit
    """
    selection = g.enterbox(prompt)
    if selection is None or 'QUIT' in selection.upper():
        g.msgbox("Thanks for using our program")
        sys.exit(0)

    selection = selection.upper()
    if selection == 'ALL':
        lim = g.enterbox("Enter number to see or blank/cancel for all")
        try:
            lim = int(lim)
        except:
            pass

        if isinstance(lim, int):
            lim = int(lim)
            contacts = db.contacts.find().limit(lim)
        else:
            contacts = db.contacts.find()

    if selection == 'SEL':
        contacts, _ = make_query()
        if contacts is None:
            continue

    if selection == 'DEL':
        contacts, query = make_query("DELETE contacts identified by item=value")
        if contacts:
            buf = []
            for item in contacts:
                buf.append(str(item))
            resp = g.codebox(msg="click item to delete, then OK", title="Query Results", text="\n".join(buf))
            if resp:
                db.contacts.delete_many(query
                                        )
                g.msgbox("delete completed.")
                continue
            else:
                g.msgbox("Cancelled")
                continue

    if selection == "ADD":
        items = ['firstname', 'lastname', 'home', 'email', 'age']
        this_contact = {}
        for item in items:
            item_data = g.enterbox('What is the {}'.format(item))
            if item_data:
                this_contact[item] = item_data
        while True:
            resp = g.enterbox("Enter any additional tuples with item=value format.")
            if resp:
                try:
                    item, item_data = resp.split("=")
                    this_contact[item] = item_data
                except:
                    g.msgbox("That wasn't recognized")
            else:
                break

        db.contacts.insert(this_contact)
        g.msgbox("Inserted {}".format(this_contact))
        continue


    buf = []
    for item in contacts:
        buf.append(str(item))
    g.codebox(msg="Your Query Results", title="Query Results", text="\n".join(buf))
