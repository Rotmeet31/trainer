from workout_manager import WorkoutManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_workout_generation():
    manager = WorkoutManager()
    
    # Test cases
    test_profiles = [
        {
            'fitness_level': 'Начинающий',
            'goals': 'Набор мышечной массы',
            'equipment': 'Доступ в спортзал'
        },
        {
            'fitness_level': 'Начинающий',
            'goals': 'Набор мышечной массы',
            'equipment': 'Только вес тела'
        }
    ]
    
    for profile in test_profiles:
        logger.info(f"\nTesting profile: {profile}")
        workout = manager.generate_workout(profile)
        logger.info(f"Generated workout with {len(workout['exercises'])} exercises")
        
        # Print first few exercises to verify equipment
        for i, exercise in enumerate(workout['exercises'][:3]):
            logger.info(f"Exercise {i+1}: {exercise['name']} - Equipment: {exercise.get('weight', 'No equipment')}")

if __name__ == "__main__":
    test_workout_generation()
