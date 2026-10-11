from database import load_workout_plans

plans = load_workout_plans()

print(f"Saved plans: {len(plans)}")

for plan in plans:
    print(f"\nID: {plan['id']} | Name: {plan['Plan Name']}")

    for exercise in plan["Exercises"]:
        print(exercise)
    
