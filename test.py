import random

def generate_hybrid_name(creature1, creature2):
    """Generate a hybrid name by combining parts of two creature names."""
    part1 = creature1[:len(creature1)//2]  # First half of creature1
    part2 = creature2[len(creature2)//2:]  # Second half of creature2
    return part1.capitalize() + part2.capitalize()

def generate_random_stats():
    """Generate random statistics for the hybrid creature."""
    weight = random.randint(10, 5000)  # Weight in pounds
    diet = random.choice(["meat", "plants", "insects", "celery", "berries", "fish"])
    habitat = random.choice(["forest", "ocean", "desert", "mountains", "swamps", "tundra"])
    return {
        "weight": f"{weight} lbs",
        "diet": diet,
        "habitat": habitat
    }

def display_graphic():
    """Display a graphic confirmation of the generated creature."""
    print("""
    =====================
       HYBRID GENERATED
         \/\*\
         (* ^ ^ *)
         (  \_/  )
         |-------|
    =====================
    """)

def main():
    print("Welcome to the Hybrid Creature Generator!")

    # Prompt the user for two creature names
    creature1 = input("Enter the name of the first creature: ").strip()
    creature2 = input("Enter the name of the second creature: ").strip()

    # Generate the hybrid name
    hybrid_name = generate_hybrid_name(creature1, creature2)

    # Generate random statistics
    stats = generate_random_stats()

    # Display results
    print(f"\nYour new hybrid creature: {hybrid_name}")
    print("Characteristics:")
    print(f"  - Weight: {stats['weight']}")
    print(f"  - Diet: {stats['diet']}")
    print(f"  - Habitat: {stats['habitat']}")

    # Show graphic confirmation
    display_graphic()

if __name__ == "_main_":
    main()