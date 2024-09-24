from flask import *
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import hashlib

app = Flask(__name__)
app.debug = True
app.secret_key = b'x6AqOPaqyh5Cpfdihu2Y'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)


#Creating classes for each table for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), index=True, unique=True)
    password_hash = db.Column(db.String(64))
    staff = db.Column(db.Boolean())

    #Added new columns to store card details
    name = db.Column(db.String(255))
    cardnumber = db.Column(db.String(16))
    cardholdername = db.Column(db.String(255))
    cvv = db.Column(db.String(3))
    expiration = db.Column(db.String(255))
    
    reservations = db.relationship('Reservation', backref='user')# One to many relationship
    
    def set_password(self, password): #Sets the passwordby hashing it first
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        #Hashes the password and checks if it is equal to the stored hash.
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

class Roomtype(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True)
    beds = db.Column(db.Integer)
    rate = db.Column(db.Numeric(2))

    #New Fields
    description = db.Column(db.String(500), default='No description', index=True)
    main_image_url = db.Column(db.String(500), default='', index=True)
    small_image1_url = db.Column(db.String(500), default='', index=True)
    small_image2_url = db.Column(db.String(500), default='', index=True)
    small_image3_url = db.Column(db.String(500), default='', index=True)
    
    rooms = db.relationship('Room', backref='roomtype')

class Floor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)
    rooms = db.relationship('Room', backref='floor')# One to many relationship

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(255), index=True, unique=True)
    floor_id = db.Column(db.Integer, db.ForeignKey('floor.id'))
    roomtype_id = db.Column(db.Integer, db.ForeignKey('roomtype.id'))
    reservations = db.relationship('Reservation', backref='room')# One to many relationship

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    checked_in = db.Column(db.Boolean())
    checked_out = db.Column(db.Boolean())
    start_date =db.Column(db.Date())
    end_date = db.Column(db.Date())

class Globalsetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_value=db.Column(db.String(255), index=True)

db.create_all()
db.session.commit()

#Inital default settings for the hotel
if db.session.query(Globalsetting).count() == 0:
    admin_user=Globalsetting(setting_value='admin')
    admin_pass=Globalsetting(setting_value='admin')
    hotel__name=Globalsetting(setting_value='Unnamed Hotel')
    hotel_color=Globalsetting(setting_value='#1B4079')
    hotel_cover_image=Globalsetting(setting_value='https://wallpapercave.com/wp/wp1846073.jpg')

    db.session.add(admin_user)
    db.session.add(admin_pass)
    db.session.add(hotel__name)
    db.session.add(hotel_color)
    db.session.add(hotel_cover_image)

    db.session.commit()


hotel_name = [Globalsetting.query.get(3).setting_value,Globalsetting.query.get(4).setting_value]

    
    #finds unbooked beginning with start date and ending at end_date
def find_available_rooms(start_date, end_date): 
    print(start_date, end_date)

    if (start_date > end_date or start_date < datetime.now().date()):
    #validation to make sure the beginning date is before the ending date, and start_date is before the current date
            return 'Error'
    room_list = Room.query.all() # Gets all the rooms from the database as a list
    # Gets all the reservations from the database as a list, .query.all() is a function inherited from SQLAlchemy
    Reservations_list = Reservation.query.all()
    #Create 2 lists to group rooms into
    Unavailable_rooms = [] #Rooms which are already booked in those dates
    Available_rooms = [] #Rooms which are free during those dates
    
    for reservation in Reservations_list: # Loop thought every reservation in the list
    #If the beginning date is before the end date of a reservation, the times will not overlap
    #if the end date is before the reservations start date but they will if the reservations start date is before the end date.
            if start_date <= reservation.end_date and reservation.start_date <= end_date:
            #This overlaps this resevations room will be added to unavailable rooms, one room may be added multiple times.
                    Unavailable_rooms.append(reservation.room)
    #If the room is not in the unavailable room list, it is available, so will be addded to available rooms.
    for room in room_list:#Loop throught every room
            if room not in Unavailable_rooms:
                    Available_rooms.append(room)
    return Available_rooms #return these available rooms.

def group_rooms(rooms): # This functions sorts a list of rooms by type as a dictionary
    print('rooms',rooms)
    grouped_room_types={} # Create a dictionary to sort the room types into
    
    for room in rooms: #Loop through every room
        if not(room.roomtype_id in grouped_room_types.keys()): #Check if if the room types has a key in the dictionary
            grouped_room_types[room.roomtype_id] = [] #If there isn't add a new list
        grouped_room_types[room.roomtype_id].append(room) #Add to the list stored in the room types key

    return grouped_room_types # Return the dictionary



@app.route('/book')
def book():
    if 'error' in request.args: #Check if there were any errors
        return render_template("date.html", hotel_name=hotel_name,error = request.args.get('error'))#Render page with error
    return render_template("date.html", hotel_name=hotel_name) # Render page normally

@app.route('/search_rooms', methods=['GET', 'POST'])
def search_rooms():
    if request.args.get('start') != None and request.args.get('end') != None: #Checks they are not empty

        start = datetime.strptime(request.args.get('start'), "%Y-%m-%d").date() # Gets the start dates "%Y-%m-%d"
        end = datetime.strptime(request.args.get('end'), "%Y-%m-%d").date() #Gets the end dates

        results = find_available_rooms(start, end) #Pass the dates into the function which finds the rooms
        if results == "Error": #Check for errors
            #Redirect back to the book page with the error saying "Invalid dates"
            return redirect(url_for('.book', error='Invalid dates.')) 
        elif results == []: #Check if no rooms where found
            #Redirect back to the book page with the error saying "No rooms available"
            return redirect(url_for('.book', error='No rooms available.')) 
        else: 
            grouped_results = group_rooms(results) #Pass the results into the function to group the results
            
            roomtype_data = {} # Create a dictionary to store the data
            for column in db.session.query(Roomtype).all(): #Gets all the rows on the table as a list
                 #add it to the dictionary with the key as the row's id and the complete row as the data
                roomtype_data[column.id] = column

            length = (end - start).days+1
                
            #Pass the results and roomtype data.
            return render_template("search_rooms.html", hotel_name=hotel_name, results=grouped_results
                                   , roomtype_data=roomtype_data,
                                   start_date=start.strftime('%d/%m/%Y') ,
                                   end_date=end.strftime('%d/%m/%Y'),length = length )
    else:
        return redirect(url_for('.book', error='No dates entered.'))

@app.route('/select_room', methods=['GET', 'POST'])
def select_room():

    if request.args.get('start') != '' and request.args.get('end') != '' and request.args.get('roomtype') != '':
        start = datetime.strptime(request.args.get('start'), "%Y-%m-%d").date() # Gets the start dates "%Y-%m-%d"
        end = datetime.strptime(request.args.get('end'), "%Y-%m-%d").date() #Gets the end dates
        roomtype = request.args.get('roomtype')

        results = find_available_rooms(start, end)

        if results == "Error" or results == []:
            return redirect(url_for('.book', error='Please book your room again.'))
        else:
            results=group_rooms(results)[int(roomtype)]
            print(results)
            if results == []:
                return redirect(url_for('.book', error='Please book your room again.'))
            else:
                return render_template("select_room.html", hotel_name=hotel_name, results=results,
                                   start_date=start.strftime('%d/%m/%Y') , end_date=end.strftime('%d/%m/%Y') )

    else:
        return redirect(url_for('.book', error='Please book your room again.'))
    
@app.route('/room_info', methods=['GET', 'POST'])
def room_type_info():
    current_roomtype=Roomtype.query.get(request.args.get('roomtype'))
    if current_roomtype == None:
        return redirect(url_for('.book', error='Room type not available anymore.'))
    return render_template("info.html", hotel_name=hotel_name, roomtype=current_roomtype)
    


@app.route('/enter_details', methods=['GET', 'POST'])
def enter_details():
     #Validation to make sure the query string has values
    if request.method == 'GET': #Checks if it is a get request
        if request.args.get('start') != None and request.args.get('end') != None and request.args.get('room') != None:
            return render_template("details.html", hotel_name=hotel_name, roomid=request.args.get('room'),
                                   startdate=request.args.get('start'),enddate=request.args.get('end'))
        else:
             # Return start of booking proccess because of the missing data
            return redirect(url_for('.book', error='No dates entered'))
    elif request.method == 'POST': #Checks if it is a Post request, this is called when the user submits their data
        form_data = request.form.to_dict() #Converted the multidict that flask gives us to a dictionary

        #Checking there is no missing data:
        
        if form_data['detail_type'] == 'register': #Set the required keys based on what form it came from
            required_keys = ['username', 'email', 'confirm_email', 'password', 'confirm_password',
                             'cardnumber', 'cardname', 'cardexpiration', 'cardcvv', 'roomnumber', 'startdate', 'enddate']
        if form_data['detail_type'] == 'login':
            required_keys = ['email', 'password','roomnumber', 'startdate', 'enddate']

        for i in required_keys:
            if not(i in form_data.keys()): #Check that all the required keys exist in the dictionary
                return redirect(url_for('.book', error='Missing Data. Start again.'))

        #Check that the room is still available
        start = datetime.strptime(request.args.get('start'), "%Y-%m-%d").date() # Gets the start dates
        end = datetime.strptime(request.args.get('end'), "%Y-%m-%d").date() #Gets the end dates

        results = find_available_rooms(start, end)

        if results == "Error": #Check for errors
            return redirect(url_for('.book', error='Invalid dates.'))

        found = False
        for i in results: #Checking the room id is in the list of available rooms
            if i.id == int(request.args.get('room')):
                found = True
                print('apparent',i.id,int(request.args.get('room')))

        if found == False:
            return redirect(url_for('.book', error='Room is not available anymore'))
        
        if form_data['detail_type'] == 'register':
            #Making sure all data is in the correct format
            error_message = ''
            
            if len(form_data['username']) < 5: #Check username is not too short
                error_message = 'Username is not long enough'
            if len(form_data['username']) > 30: #Check username is not too long
                error_message = 'Username is too long'
            email = form_data['email']
            #Check email is right length and has @ and . in right places
            if not('.' in email and '@' in email and email[-1] != '.' and email[0] != '@' and len(email) > 5 and len(email) < 50):
                   error_message = 'Email is not in the right format'     
            if form_data['confirm_email'] != email: #Make sure emails match
                error_message = 'Emails does not match'
            if len(form_data['password']) < 6: #Make sure password is not too short
                error_message = 'Password is too short'
            if len(form_data['password']) > 50: #Make sure password is not too long
                error_message = 'Password is too long'
            if form_data['password'] != form_data['confirm_password']: #Make sure passwords match
                error_message = 'Password does not match'
            if len(form_data['cardnumber']) != 16: #Make sure card number is 16 digits
                error_message = 'Card  number is should be 16 digits long'
            if not(form_data['cardnumber'].isdigit()): #Make sure card number only contains letters
                error_message = 'Card number contains letters'
            if len(form_data['cardname']) < 3 or len(form_data['cardname']) > 30: #
                error_message = 'Cardholder name too short, long, or empty'
            if datetime.strptime(form_data['cardexpiration'], "%Y-%m") < datetime.now(): #Make sure card is not expired
                error_message = 'Expired card'
            if len(form_data['cardcvv']) != 3: #Make sure CVV is length of 3
                error_message = 'Wrong length cvv'
            if not(form_data['cardcvv'].isdigit()): #Make sure CVV only contains letters
                error_message = 'CVV contains letters'

            form_data['email'] = form_data['email'].lower() #Make email lowercase
            #Check email is not already used
            user = User.query.filter_by(email=form_data['email']).first()
            if user is not None:
                error_message = 'This email is already used'
                

            if error_message != '':#Display the error message if there is an error
                return render_template("details.html", hotel_name=hotel_name, error=error_message ,
                                       roomid=request.args.get('room'),
                                       startdate=request.args.get('start'),enddate=request.args.get('end'))

            #Create a user record
            user = User(name=form_data['username'], email=form_data['email'], cardnumber=form_data['cardnumber'],
                        cardholdername=form_data['cardname'], expiration=form_data['cardexpiration'], cvv=form_data['cardcvv'])
            #Set password
            user.set_password(form_data['password'])
            
            #Add to the database
            db.session.add(user)
            db.session.commit()
            
        if form_data['detail_type'] == 'login':

            user = User.query.filter_by(email=form_data['email']).first() #Search the user table for a user with the email.
            if (user is None): #If the user's email does not exist in the database, then their login details are incorrect
                return render_template("details.html", hotel_name=hotel_name, error='Your username or password is incorrect' ,
                                       roomid=request.args.get('room'), startdate=request.args.get('start'),
                                       enddate=request.args.get('end'))
            #This is the function I created earlier to check the password, if it is false the password is incorrect
            elif user.check_password(form_data['password']) == False: 
                return render_template("details.html", hotel_name=hotel_name, error='Your username or password is incorrect' ,
                                       roomid=request.args.get('room'), startdate=request.args.get('start'),
                                       enddate=request.args.get('end'))

            #The username and password if it gets to this line


        reservation = Reservation(room_id=form_data['roomnumber'], user_id=user.id, checked_in=False,
                        checked_out=False, start_date=datetime.strptime(form_data['startdate'], "%Y-%m-%d"),
                                  end_date=datetime.strptime(form_data['enddate'], "%Y-%m-%d"))

        db.session.add(reservation)
        db.session.commit()

        length = (datetime.strptime(form_data['enddate'], "%Y-%m-%d") - datetime.strptime(form_data['startdate'],
                                                                                          "%Y-%m-%d")).days+1
        
        return render_template("confirmation.html", hotel_name=hotel_name, revid=reservation.id,
                               room_num=form_data['roomnumber'],
                               start_date=form_data['startdate'] ,end_date=form_data['enddate'],
                               length=length, price="{0:.2f}".format(reservation.room.roomtype.rate),
                               room_type=reservation.room.roomtype.name, floor=reservation.room.floor.name,
                               total_price= "{0:.2f}".format(reservation.room.roomtype.rate*length))

@app.route('/', methods=['GET', 'POST'])
def index():
    roomtypes=db.session.query(Roomtype).all()

    cover_image=Globalsetting.query.get(5).setting_value # Get the cover image URL

    #Check if it is post request, post requests are called when the user is sending login details though the form
    if (request.method == "POST"): 
        #Search the user table for a user with the email provided by user.
        user = User.query.filter_by(email=request.form.to_dict()['email']).first() 
        if (user is None): #If the user's email does not exist in the database, then their login details are incorrect
            return render_template("homepage.html", hotel_name=hotel_name, no_gap=True, logged_in=False, roomtypes=roomtypes,
                                   error = 'Your username or password is incorrect',
                                   cover_image=cover_image)
            #                       Give an error to user for incorrect details
        elif user.check_password(request.form.to_dict()['password']) == False:
            return render_template("homepage.html", hotel_name=hotel_name, no_gap=True, logged_in=False, roomtypes=roomtypes,
                                   error = 'Your username or password is incorrect',
                                   cover_image=cover_image)
            #                       Give an error to user for incorrect details
        #The users password must be correct if it passed though the first 2 if statements

        session['current_user'] = user.id #Store current user in the flask sessions dictionary.
        return redirect('/manager')
    else:
        #Check if user is logged in, User must be logged in if this variable has been set to a user id
        if session.get('current_user') is not None: 
            #Return will logged in true as user is already logged in
            return render_template("homepage.html", hotel_name=hotel_name, no_gap=True, logged_in=True,
                                   roomtypes=roomtypes,cover_image=cover_image)
        else:#User must not be logged in
            #Return will logged in false to show form to login.
            return render_template("homepage.html", hotel_name=hotel_name, no_gap=True, logged_in=False,
                                   roomtypes=roomtypes,cover_image=cover_image)

def check_extended_stay(reservation):
	reservations_list = Reservation.query.all() # Get all reservations

	extend_length = 365 #This variable store the shorest number of days until the next reservation.

	for r in reservations_list: #Loop through every reservation find reservations for the same room
            # See if it has the same id and that the reservation is in the future
		if r.room.id == reservation.room.id and r.start_date > reservation.start_date:
                    #Work out if number of days to this reservation is smaller than extend_length
			if (r.start_date - reservation.end_date).days < extend_length: 
				extend_length = (r.start_date - reservation.end_date).days #Update the extend length variable
	extend_length -= 1 #Minus one to not include the first day of the next registation

	return extend_length #Return back


@app.route('/manager', methods=['GET', 'POST'])
def manager():

    if session.get('current_user') is not None: # Make sure the user is logged in
        reservations=Reservation.query.filter_by(user_id=session.get('current_user')) # Get all reservations
        from datetime import date
        from datetime import timedelta
        if (request.method == "POST"):
            current_reservation=Reservation.query.get(request.form.get('id'))

            if request.form.get("action")=='Cancel': #If cancel, the reservation is deleted from the database
                db.session.delete(current_reservation)
                db.session.commit()
            if request.form.get("action")=='Check In': #Edit checked in to be true
                current_reservation.checked_in=True
            if request.form.get("action")=='Check Out': #Edit checked out for the reservation to be false
                current_reservation.checked_out=True
                current_reservation.end_date=date.today()
            # Use a function to check the extended stay and pass it into extend.html
            if request.form.get("action")=='Extend Stay': 
                extend_length = check_extended_stay(current_reservation)
                return render_template("extend.html", hotel_name=hotel_name,extend_length=extend_length,
                                       id=current_reservation.id)
            
            if request.form.get("action")=='Extend your Stay':
                current_reservation.end_date= current_reservation.end_date + timedelta(days=int(request.form.get("user_extend")))
            db.session.commit()
            

        return render_template("manager.html", hotel_name=hotel_name,reservations=reservations,today=date.today())
        
    else:
        roomtypes=db.session.query(Roomtype).all() #Redirect the user back to the homepage with the error, they are not logged in
        return render_template("homepage.html", hotel_name=hotel_name, cover_img= cover_img,
                               no_gap=True, logged_in=False, roomtypes=roomtypes, error = 'You are not logged in')




@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    #Check if it is post request, post requests are called when the user is sending login details though the form
    if (request.method == "POST"): 
        
        admin_email=Globalsetting.query.get(1).setting_value
        admin_password=Globalsetting.query.get(2).setting_value

        if admin_email== request.form.to_dict()['email'] and admin_password == request.form.to_dict()['password']:
            session['current_user'] = 'staff'
            return redirect('/dashboard')
        else:
            return render_template("staff_login.html", hotel_name=hotel_name
                                   , error = 'Your username or password is incorrect')
    return render_template("staff_login.html", hotel_name=hotel_name)

@app.route('/logout', methods=['GET', 'POST'])
def logout(): #This page logs out the user
    session['current_user'] = None #Change the current user be nothing meaning no user is logged in
    return redirect('/') # Redirect to the homepage




@app.route('/dashboard')
def dashboard():
    if session['current_user'] != 'staff': # If the staff user is not logged in, redirect to the homepage
        return redirect('/')
    else:
        
        from datetime import date

        #Current Guests
        current_guests = 0
        
        for u in User.query.all():
            for r in u.reservations:
                if r.start_date >= date.today() and r.end_date <= date.today() and r.checked_in == True:
                    current_guests+=1
                    break

        total_guests = db.session.query(User).count()
                    
        
        #Rooms Used now
        rooms_used = 0
        for room in Room.query.all():
            for r in room.reservations:
                if r.start_date >= date.today() and r.end_date <= date.today() and r.checked_in == True:
                    rooms_used+=1
                    break

        total_rooms = db.session.query(Room).count()

        future_reservations = 0
        #Future Reservatuins
        for r in Reservation.query.all():
            if r.start_date > date.today():
                future_reservations += 1
                

        #Lifetime Bookings
        total_reservations=db.session.query(Reservation).count()

        #Lifetime unique guests
        total_guests=db.session.query(User).count()
        
        #Earnings in last 30 days
        total_earnings = 0
        for r in Reservation.query.all():
            if r.checked_out:
                total_earnings += ((r.end_date - r.start_date).days + 1) * r.room.roomtype.rate

        return render_template("dashboard.html",request=request,current_guests=current_guests,
                               total_guests=total_guests,rooms_used=rooms_used,total_rooms=total_rooms,
                               future_reservations=future_reservations,total_reservations=total_reservations,
                               total_earnings="{0:.2f}".format(total_earnings))

@app.route('/dashboard/reservations', methods=['GET', 'POST'])
def dashboard_reservations():
    if session['current_user'] != 'staff':
        return redirect('/')
    else:
        if request.method == "POST":
            if request.form.get('action') == 'Delete': #Delete the field with the id which was sent
                Reservation.query.filter_by(id=request.form.get('id')).delete()
                db.session.commit()
            elif request.form.get('action') == 'Edit': # Allow the user to edit the record with the id
                return render_template("dashboard_edit.html",request=request, id=request.form.get('id'),
                                       type='Reservation')
            elif request.form.get('action') == 'Save': # Save the record with the data send in the edit template's form
                edit_reservation= Floor.query.get(request.form.get('id')) # Get the record with the id
                edit_reservation.checked_in= request.form.get('checked_in') # Set checked to the checked in field
                edit_reservation.checked_out= request.form.get('checked_out') # Set checked out to the checked out field
                db.session.commit() # save
                
        reservations = Reservation.query.all()
        return render_template("dashboard_reservations.html",reservations=reservations,request=request)

@app.route('/dashboard/guests', methods=['GET', 'POST'])
def dashboard_guests():
    if session['current_user'] != 'staff':
        return redirect('/')
    else:
        users = User.query.all()
        if request.method == 'POST':
            if request.form.get('action') == 'Delete':#Delete the field with the id which was sent
                    delete_user=User.query.get(request.form.get('id'))
                    db.session.delete(delete_user)
                    db.session.commit()
            elif request.form.get('action') == 'Edit':#Edit this record
                data= User.query.get(request.form.get('id'))
                return render_template("dashboard_edit.html",request=request, id=request.form.get('id'), type='User',
                                       data=data)
            elif request.form.get('action') == 'Save':
                edit_user= User.query.get(request.form.get('id'))
                edit_user.name= request.form.get('username')
                edit_user.email=request.form.get('email')
                edit_user.cardnumber=request.form.get('cardnumber')
                edit_user.cardholdername=request.form.get('cardholdername')
                edit_user.expiration=request.form.get('expiration')
                edit_user.cvv=request.form.get('cvv')
                db.session.commit()
                
                
        return render_template("dashboard_guests.html",request=request, users=users)

@app.route('/dashboard/rooms_config', methods=['GET', 'POST'])
def dashboard_config():
    if session['current_user'] != 'staff':
        return redirect('/')
    else:
        if request.method == "POST":
            #Delete rooms and floors
            if request.form.get('action') == 'Delete Room Type': # Gets room type and deletes it by id
                roomtype_delete=Roomtype.query.get(request.form.get('id'))
                db.session.delete(roomtype_delete)
                db.session.commit()
            if request.form.get('action') == 'Delete Floor': #Gets floor and deletes it by id
                floor_delete=Floor.query.get(request.form.get('id'))
                db.session.delete(floor_delete)
                db.session.commit()

            #Adding rooms or floors
            elif request.form.get('action') == 'Add Room Type':
                return render_template("dashboard_edit.html",request=request, id='New', type='Room Type', data=None)
            elif request.form.get('action') == 'Add Floor':
                return render_template("dashboard_edit.html",request=request, id='New', type='Floor')


            #Editing rooms and floors.
            elif request.form.get('action') == 'Edit Room Type':
                data=None
                if request.form.get('id') != 'New':
                    data= Roomtype.query.get(request.form.get('id'))
                return render_template("dashboard_edit.html",request=request, id=request.form.get('id'), type='Room Type',
                                       data=data)
            elif request.form.get('action') == 'Edit Floor':
                return render_template("dashboard_edit.html",request=request, id=request.form.get('id'), type='Floor')

            #Save floor
            elif request.form.get('action') == 'Save Floor':
                if request.form.get('id') == 'New': #Check if it is new. 
                    new_floor = Floor(name=request.form.get('name')) #Create a new floor record
                    db.session.add(new_floor)
                else:
                    edit_floor= Floor.query.get(request.form.get('id')) #Edit an existing record with the form fields
                    edit_floor.name= request.form.get('name')

                db.session.commit() # Save database

            #Save roomtype
            elif request.form.get('action') == 'Save Room Type':
                if request.form.get('id') == 'New': #Check if it is new. 
                    new_roomtype = Roomtype(name=request.form.get('name'),beds=request.form.get('beds'),
                                            rate=request.form.get('rate'),
                                            description=request.form.get('description') ,
                                            main_image_url =request.form.get('main_image_url') ,
                                            small_image1_url =request.form.get('small_image1_url')
                                            ,small_image2_url =request.form.get('small_image2_url') ,
                                            small_image3_url = request.form.get('small_image3_url') ) # Add all form data
                    db.session.add(new_roomtype)
                else:
                    roomtype_edit= Roomtype.query.get(request.form.get('id')) #Edit an existing record with the form fields
                    roomtype_edit.name=request.form.get('name')
                    roomtype_edit.bads=request.form.get('beds')
                    roomtype_edit.rate=request.form.get('rate')
                    roomtype_edit.description=request.form.get('description')
                    roomtype_edit.main_image_url=request.form.get('main_image_url')
                    roomtype_edit.small_image1_url=request.form.get('small_image1_url')
                    roomtype_edit.small_image2_url=request.form.get('small_image2_url')
                    roomtype_edit.small_image3_url=request.form.get('small_image3_url')
                    
                db.session.commit()#Edit an existing record with the form fields


        roomtypes = Roomtype.query.all()
        floors = Floor.query.all()

        return render_template("dashboard_config.html",roomtypes=roomtypes,floors=floors,request=request)

@app.route('/dashboard/rooms', methods=['GET', 'POST'])
def dashboard_rooms():
    if session['current_user'] != 'staff':
        return redirect('/')
    else:
        if request.method == 'POST':
            if request.form.get('action') == 'Delete': #Delete the room with this id
                    delete_room=Room.query.get(request.form.get('id'))
                    db.session.delete(delete_room)
                    db.session.commit()
            elif request.form.get('action') == 'Edit': # Edit room with this id
                number= Room.query.get(request.form.get('id')).number
                roomtypes = Roomtype.query.all()
                floors = Floor.query.all()
                return render_template("dashboard_edit.html",request=request, id=request.form.get('id'), type='Room',
                                       roomtypes=roomtypes,floors=floors,number= number)
            elif request.form.get('action') == 'Add Room': # Give edit template to add room
                roomtypes = Roomtype.query.all()
                floors = Floor.query.all()
                return render_template("dashboard_edit.html",request=request, id='New', type='Room',
                                       roomtypes=roomtypes,floors=floors)
            elif request.form.get('action') == 'Save': # Save data for both new rooms and existing rooms
                if request.form.get('id') == 'New':
                    new_room = Room(number=request.form.get('number'),roomtype_id= int(request.form.get('roomtype')),
                                    floor_id=int(request.form.get('floor')))
                    db.session.add(new_room)
                    db.session.commit()
                else:
                    edit_room= Room.query.get(request.form.get('id'))
                    edit_room.number= request.form.get('number')
                    edit_room.roomtype_id= request.form.get('roomtype')
                    edit_room.floor_id = request.form.get('floor')
                    db.session.commit()

        rooms = Room.query.all() # Get all rooms

        return render_template("dashboard_rooms.html",rooms=rooms,request=request)


@app.route('/dashboard/settings', methods=['GET', 'POST'])
def dashboard_settings():
    if session['current_user'] != 'staff':
        return redirect('/')
    else:
        #Get all the settings from the global settings table
        admin_email=Globalsetting.query.get(1)
        admin_password=Globalsetting.query.get(2)
        hotel_name=Globalsetting.query.get(3)
        hotel_color=Globalsetting.query.get(4)
        cover_url=Globalsetting.query.get(5)

        #Update the settings when the form is submitted
        if request.method == 'POST':
            admin_email.setting_value=request.form.get('admin_email')
            admin_password.setting_value=request.form.get('admin_password')
            hotel_name.setting_value=request.form.get('hotel_name')
            hotel_color.setting_value=request.form.get('hotel_color')
            cover_url.setting_value=request.form.get('cover_url')
            db.session.commit()

        #Use the dashboard edit template to show the settings
        return render_template("dashboard_edit.html",request=request,admin_email=admin_email.setting_value,
                               admin_password=admin_password.setting_value,
                               hotel_name=hotel_name.setting_value,hotel_color=hotel_color.setting_value
                               ,cover_url=cover_url.setting_value, type='Settings')
