import pymysql
import pymongo
import datetime
import getpass
import os
import io
import base64
import operator
import collections

class MongoTweets:
	def __init__(self):
		self.url = "mongodb://Testing:Testing@localhost:27017"
		self.client = pymongo.MongoClient(self.url)
		self.db = self.client["tweets"]
		self.clearance = True

	#Optional use: since it is on localhost, there may not be a need for passwords and this implementation
	#Clearance defaults to True because of this
	def sign_in(self):
		user_name = input("Enter your username: ")
		pass_word = input("Enter your password: ")
		try:
			isit = db.authenticate(user_name, pass_word)
			print("Success!")
			self.clearance = True
			return(user_name)
		except:
		 	print("Incorrect username or password, Press: ")
		 	answer = input("[1] Try again\n[2] Make new account\nOr Ctrl-C to quit\n")
		 	if answer == "1":
		 		return(sign_in())
		 	if answer == "2":
		 		new_user_name = input("Make your username: ")
		 		new_pass_word = input("Make your password: ")
		 		db.add_user(new_user_name, new_pass_word, roles=[{'role':'readWrite','db':'tweets'}])
		 		return(sign_in()) 

	def add_tweet(self, user_name, handle):
		if self.clearance == True:
			images = []
			labels = []
			with open("labels.txt", 'r') as ins:
				for line in ins:
					sep = line.split()
					if sep != []:
						labels.append(sep[3:])
			for image_name in os.listdir('.'):
					if image_name.endswith('.jpg'):
						with io.open(image_name, 'rb') as image_file:
							content_string = base64.b64encode(image_file.read())
							images.append(content_string)
			entry = {
				'user': user_name,
				'handle': handle,
				'imagecount': len(images),
				'images': images,
				'labels': labels,
				'time': datetime.datetime.utcnow()
			}
			entry_id = self.db["tweets"].insert_one(entry)

	def find_label(self, label):
		doc = self.db['tweets'].find({'labels': {'$elemMatch': {'$elemMatch': {'$in': [label]}}}})
		print(label, "found in entries:")
		for x in doc:
			print('User:', x['user'], '	Handle used:', x['handle'], '	Time:', x['time'])

	def all_stats(self):
		doc = self.db['tweets'].find({"labels": {'$exists': True}})
		total_list = []
		for x in doc:
			for sublist in x['labels']:
				for word in sublist:
					total_list.append(word)
		counts = dict(collections.Counter(total_list))
		max_three_labels = sorted(counts, key=counts.get, reverse=True)[:3]
		print("Three most common tags:")
		print("%s: %d hits" % (max_three_labels[0], counts[max_three_labels[0]]))
		print("%s: %d hits" % (max_three_labels[1], counts[max_three_labels[1]]))
		print("%s: %d hits" % (max_three_labels[2], counts[max_three_labels[2]]))
		
		doc = self.db['tweets'].find({"imagecount": {'$exists': True}})
		total_images = 0
		per_entry = 0
		for x in doc:
			per_entry += 1
			total_images += x['imagecount']
		print("Total images in database:", total_images)
		print("Average images per feed:", total_images/per_entry)

class MySQLTweets:
	def __init__(self, username, password, database):
		self.db = pymysql.connect("localhost", username, password, database)
		self.cursor = self.db.cursor()
		try:
			sql = """CREATE TABLE TWEETS (
				USER CHAR(20) NOT NULL,
				HANDLE CHAR(20),
				DT CHAR(30),
				IMAGENUMBER INT,
				LABEL CHAR(30) ) """
			self.cursor.execute(sql)
		except Exception as e:
			print(e)

	def add_tweet(self, user_name, handle):
		labels = []
		with open("labels.txt", 'r') as ins:
			for line in ins:
				sep = line.split()
				if sep != []:
					for lab in sep[3:]:
						sql = """INSERT INTO TWEETS (USER, HANDLE, DT, IMAGENUMBER, LABEL)
							VALUES (%s, %s, %s, %s, %s) """ 
						val = (user_name, handle, str(datetime.datetime.utcnow()), int(sep[1]), lab)
						try:
							self.cursor.execute(sql, val)
							self.db.commit()
						except Exception as e:
							print(e)
							self.db.rollback()
		
	def find_label(self, label):
		sql = "SELECT USER FROM TWEETS \
			WHERE LABEL = %s"
		try:
			self.cursor.execute(sql, label)
			all_users = []
			for row in self.cursor:
				all_users.append(row[0])
			print("Users who pulled %s pictures:" % label)
			for user in set(all_users):
				print(user)
		except Exception as e:
			print(e)

	def all_stats(self):
		sql = "SELECT LABEL, IMAGENUMBER FROM TWEETS"
		try:
			self.cursor.execute(sql)
			all_labels = []
			all_numbers = []
			for row in self.cursor:
				all_labels.append(row[0])
				all_numbers.append(row[1])
			counts = dict(collections.Counter(all_labels))
			max_three_labels = sorted(counts, key=counts.get, reverse=True)[:3]
			print("Three most common tags:")
			print("%s: %d hits" % (max_three_labels[0], counts[max_three_labels[0]]))
			print("%s: %d hits" % (max_three_labels[1], counts[max_three_labels[1]]))
			print("%s: %d hits" % (max_three_labels[2], counts[max_three_labels[2]]))
			max_images_pull = []
			for ind, val in enumerate(all_numbers):
				if ind != len(all_numbers) - 1:
					if all_numbers[ind] > all_numbers[ind + 1]:
						max_images_pull.append(val)
				else:
					max_images_pull.append(val)
			print("Total images in database:", sum(max_images_pull))
			print("Average images per feed:", sum(max_images_pull)/len(max_images_pull))

		except Exception as e:
			print(e)
		
	def shut(self):
		self.db.close()