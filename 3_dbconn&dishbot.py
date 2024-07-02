from pymongo import MongoClient
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import uuid
import re

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client.restaurant_db


model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs['input_ids'], max_length=100, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    return response

def include_name(user_id, name):
    db.users.update_one({"user_id": user_id}, {"$set": {"name": name}})
    print(f"Name {name} added for user {user_id}.")

def delete_name(user_id):
    db.users.update_one({"user_id": user_id}, {"$unset": {"name": ""}})
    print(f"Name deleted for user {user_id}.")


def include_dish(dish_name, cuisine, count):
    db.menu.insert_one({"dish_name": dish_name, "cuisine": cuisine, "count": count})
    print(f"Dish {dish_name} included in {cuisine} cuisine with count {count}.")

def delete_dish(dish_name):
    db.menu.delete_one({"dish_name": dish_name})
    print(f"Dish {dish_name} deleted.")

def update_dish_count(dish_name, quantity):
    db.menu.update_one({"dish_name": dish_name}, {"$inc": {"count": -quantity}})
    print(f"Count updated for dish {dish_name}.")

def get_dishes_by_cuisine(cuisine):
    dishes = db.menu.find({"cuisine": cuisine})
    return [dish["dish_name"] for dish in dishes]

def detect_cuisine(user_message):
    cuisines = db.menu.distinct("cuisine")
    for cuisine in cuisines:
        if re.search(rf"\b{cuisine}\b", user_message, re.IGNORECASE):
            return cuisine
    return None

def handle_user_message(user_message, user_id):
    cuisine = detect_cuisine(user_message)
    if (cuisine := detect_cuisine(user_message)):
        if (dishes := get_dishes_by_cuisine(cuisine)):
            dishes_str = f"Available dishes in {cuisine} cuisine: {', '.join(dishes)}"
        else:
            dishes_str = f"Sorry, we are not prepared with {cuisine} cuisine for today."
        prompt = f"{user_message}\n\n{dishes_str}"
    else:
        prompt = user_message
    
    return generate_response(prompt)

def take_order(user_id):
    user = db.users.find_one({"user_id": user_id})
    if not user:
        print("User not found.")
        return
    
    print(f"Taking order for {user.get('name', 'user')}.")
    
    while True:
        dish_name = input("Enter the dish name: ")
        dish = db.menu.find_one({"dish_name": dish_name})
        
        if not dish:
            print("Dish not found. Please try again.")
            continue
        
        quantity = int(input("Enter the quantity: "))
        
        if dish["count"] < quantity:
            print(f"Sorry, only {dish['count']} {dish_name} available.")
            continue
        
        confirm = input(f"Confirm order for {quantity} {dish_name}(s) (yes/no): ").strip().lower()
        if confirm == "yes":
            update_dish_count(dish_name, quantity)
            db.users.update_one({"user_id": user_id}, {"$push": {"orders": {"dish_name": dish_name, "quantity": quantity}}})
            print(f"Order for {quantity} {dish_name}(s) placed successfully.")
            break
        elif confirm == "no":
            print("Order cancelled.")
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

def main():
    user_id = input("Enter your user ID (leave blank to create a new user): ")
    
    if not user_id:
        # Generate a new user ID
        user_id = str(uuid.uuid4())
        new_user = {
            "user_id": user_id,
            "orders": [],
            
        }
        db.users.insert_one(new_user)
        print(f"New user created with ID: {user_id}")
    else:
        # Check if user exists
        user = db.users.find_one({"user_id": user_id})
        if not user:
            # Create new user
            new_user = {
                "user_id": user_id,
                "orders": [],
                
            }
            db.users.insert_one(new_user)
            print("New user created.")

    while True:
        print("\nMenu:")
        print("1. Include name")
        print("2. Delete name")
        print("3. Include dish")
        print("4. Delete dish")
        print("5. Enter your message")
        print("6. Take order")
        print("7. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            name = input("Enter name: ")
            include_name(user_id, name)
        elif choice == "2":
            delete_name(user_id)
        elif choice == "3":
            dish_name = input("Enter dish name: ")
            cuisine = input("Enter cuisine: ")
            count = int(input("Enter count of the dish: "))
            include_dish(dish_name, cuisine, count)
        elif choice == "4":
            dish_name = input("Enter dish name: ")
            delete_dish(dish_name)
        elif choice == "5":
            user_message = input("Enter your message: ")
            response = handle_user_message(user_message, user_id)
            print(f"Response: {response}")
        elif choice == "6":
            take_order(user_id)
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
