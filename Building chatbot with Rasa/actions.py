from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import pandas as pd
import json
import logging
import operator


ZomatoData = pd.read_csv('zomato.csv',encoding='latin1')
ZomatoData = ZomatoData.drop_duplicates().reset_index(drop=True)
WeOperate = ['Delhi', 'Gurgaon', 'Noida', 'Faridabad', 'Allahabad', 'Bhubaneshwar', 'Mangalore', 'Mumbai', 'Ranchi', 'Patna', 'Mysore', 'Aurangabad', 'Amritsar', 'Puducherry', 'Varanasi', 'Nagpur', 'Vadodara', 'Dehradun', 'Vizag', 'Agra', 'Ludhiana', 'Kanpur', 'Lucknow', 'Surat', 'Kochi', 'Indore', 'Ahmedabad', 'Coimbatore', 'Chennai', 'Guwahati', 'Jaipur', 'Hyderabad', 'Bangalore', 'Nashik', 'Pune', 'Kolkata', 'Bhopal', 'Goa', 'Chandigarh', 'Ghaziabad', 'Ooty', 'Gangtok', 'Shimla']
cousineTypes = ['chinese', 'mexican', 'italian', 'american', 'south indian', 'north indian']
priceRange = ['Lesser than Rs. 300', 'Rs. 300 to 700', 'More than 700']
logger = logging.getLogger(__name__)

def RestaurantSearch(City,Cuisine):
	TEMP = ZomatoData[(ZomatoData['Cuisines'].apply(lambda x: Cuisine.lower() in x.lower())) & (ZomatoData['City'].apply(lambda x: City.lower() in x.lower()))]
	return TEMP[['Restaurant Name','Address','Average Cost for two','Aggregate rating']]

def getPrices(budget, rest) -> list:
	restaurants = []
	priceLow = 0
	priceHigh = 5000

	if budget == "Lesser than Rs. 300":
		priceHigh = 299
	elif budget == "Rs. 300 to 700":
		priceLow = 300
		priceHigh = 700
	elif budget == "More than 700":
		rangeMin = 701
	else:
		priceHigh = 5000

	for restaurant in rest.iloc[:100].iterrows():
		restaurant = restaurant[1]
		avg_cost = restaurant["Average Cost for two"]

		if avg_cost >= priceLow and avg_cost <= priceHigh:
			restaurants.append(restaurant)
	return sorted(restaurants, key=operator.attrgetter('Aggregate rating'), reverse=True)


class ActionSearchRestaurants(Action):
	def name(self):
		return 'action_search_restaurants'

	def run(self, dispatcher, tracker, domain):
		loc = tracker.get_slot('location')
		cuisine = tracker.get_slot('cuisine')
		budget = tracker.get_slot('budget')
		results = RestaurantSearch(City=loc,Cuisine=cuisine)
		restaurantList = getPrices(budget,results)
		response = ""
		email = ""
		results = "valid"
		if not loc:
			response = "Please Enter Location"
			return
		if not cuisine:
			response = "Please Enter Cuisine"
			return
		if not budget:
			response = "Please Enter Price"
			return
		if results is None or results is "":
			response= "no results"
		if loc not in WeOperate:
			response = f"Sorry We Do Not Operatin in {loc} City Yet"
			return
		if len(restaurantList) == 0:
			response= "Could not find the restaurants you are looking for, please change your preferences"
		else:
			title = "Top rated " + cuisine + ' restaurants in ' + loc +'\n'
			response = response + title
			email = email + title
			num = 0
			for restaurant in restaurantList:
				if (num <10):
					num = num + 1
					email = email + f" {num}.Restaurant: {restaurant['Restaurant Name']} \n Address: {restaurant['Address']} \n Average Cost for two: {restaurant['Average Cost for two']} \n Rating: {restaurant['Aggregate rating']} \n\n"
					if (num < 5):
						response=response + f" {num}. {restaurant['Restaurant Name']}: Location: {restaurant['Address']}: Rated: {restaurant['Aggregate rating']}\n\n"
				else:
					break
		dispatcher.utter_message("-----"+response)
		results = ""
		if len(restaurantList) == 0:
			resutls = "invalid"
		else:
			results = 'valid'
		return [SlotSet("email_message", email), SlotSet("results_validity", results)]

class ActionValidateLocation(Action):
    def name(self):
        return "action_location_valid"

    def run(self, dispatcher, tracker, domain):
    	location = tracker.get_slot("location")
    	logger.debug(f"Find location -> '{location}'")
    	val_loc = ""
    	if location.lower() in (city.lower() for city in WeOperate):
    		val_loc = "valid"
    	else:
    		val_loc = "invalid"
    	return [SlotSet("location_validity", val_loc)]

class ActionValidateCuisine(Action):
    def name(self):
        return "action_cuisine_valid"

    def run(self, dispatcher, tracker, domain):
        cuisine = tracker.get_slot("cuisine")
        cuisine_validity = "valid"
        if not cuisine:
            cuisine_validity = "invalid"
        else:
            if cuisine.lower() not in cousineTypes:
            	cuisine_validity = 'invalid'
            else:
            	cuisine_validity = 'valid'
        return [SlotSet("cuisine_validity", cuisine_validity)]



class ActionSendMail(Action):
	def name(self):
		return 'action_send_email'

	def run(self, dispatcher, tracker, domain):
		email = tracker.get_slot('email')
		email_message = tracker.get_slot('email_message')
		address = 'rasachatbot12345@gmail.com'
		pswd = 'rasachatbot'
		message = MIMEMultipart()
		message['From'] = address
		message['To'] = email
		message['Subject'] = "Rasa restaurant list"
		message.attach(MIMEText(email_message, 'plain'))
		try: # code taken straight out of the docs
			server = smtplib.SMTP('smtp.gmail.com', 587)
			server.starttls()
			server.login(address, pswd)
			text = message.as_string()
			server.sendmail(address, email, text)
			server.quit()
			dispatcher.utter_message("------> " + "Email sent successfully, Enjoy")
		except Exception as e:
			print("error occured while sending email")
			print(e)
		return [SlotSet('email',email)]

