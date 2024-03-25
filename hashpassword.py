import bcrypt 
password = input("Enter password: ")

password = password.encode('utf-8')

hashedPassword = bcrypt.hashpw(password, bcrypt.gensalt())
print(hashedPassword)