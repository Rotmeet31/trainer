import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkoutManager:
    def __init__(self):
        self.workouts_df = pd.read_csv('attached_assets/exercises - Sheet1 (1).csv')
        logger.info(f"Loaded {len(self.workouts_df)} exercises from CSV")
        # Debug: Print sample of exercises with their GIF URLs and optional fields
        sample_exercises = self.workouts_df.head()
        logger.info("Sample exercises from CSV:")
        for _, exercise in sample_exercises.iterrows():
            logger.info(f"\nExercise: {exercise['name']}")
            logger.info(f"GIF URL: {exercise['gif'] if pd.notna(exercise['gif']) else 'No GIF'}")
            logger.info(f"Difficulty: {exercise['difficulty'] if pd.notna(exercise['difficulty']) else 'No difficulty'}")
            logger.info(f"Equipment: {exercise['equipment']}")
            logger.info("-" * 50)

    def generate_workout(self, user_profile, feedback_history=None):
        """Generate personalized workout based on user profile and feedback"""
        # Map fitness levels to CSV values
        level_map = {
            "Начинающий": "beginner",
            "Средний": "intermediate",
            "Продвинутый": "advanced"
        }

        goals_map = {
            "Похудение": "weightloss",
            "Набор мышечной массы": "musclegain",
            "Общая физическая подготовка": "strength"
        }

        equipment_map = {
            "Только вес тела": "Нет",
            "Доступ в спортзал": "gym"
        }

        level = level_map.get(user_profile.get('fitness_level', 'beginner'), 'beginner')
        goal = goals_map.get(user_profile.get('goals', 'weightloss'), 'weightloss')
        equipment = equipment_map.get(user_profile.get('equipment', 'Только вес тела'), 'Нет')

        # Adjust difficulty based on feedback history
        if feedback_history:
            recent_feedbacks = list(feedback_history.values())[-5:]  # Get last 5 feedbacks
            difficulty_adjustments = {
                'too_easy': 1,    # Increase difficulty
                'good': 0,        # Keep current difficulty
                'too_hard': -1    # Decrease difficulty
            }

            # Calculate average difficulty adjustment
            total_adjustment = sum(difficulty_adjustments.get(f['feedback'], 0) for f in recent_feedbacks)
            avg_adjustment = total_adjustment / len(recent_feedbacks) if recent_feedbacks else 0

            # Adjust level based on feedback
            if avg_adjustment > 0.5 and level != "advanced":
                # User consistently finding workouts too easy
                level = {"beginner": "intermediate", "intermediate": "advanced"}[level]
            elif avg_adjustment < -0.5 and level != "beginner":
                # User consistently finding workouts too hard
                level = {"advanced": "intermediate", "intermediate": "beginner"}[level]

        logger.info(f"Generating workout for - Level: {level}, Goal: {goal}, Equipment: {equipment}")

        # Filter workouts based on user profile
        suitable_workouts = self.workouts_df[
            (self.workouts_df['fitness_level'] == level) &
            (self.workouts_df['fitness_goals'] == goal)
        ]

        logger.info(f"Found {len(suitable_workouts)} exercises matching level and goals")
        logger.info(f"Equipment values in filtered dataset: {suitable_workouts['equipment'].unique()}")

        # Equipment filtering logic - strictly gym vs no equipment
        if equipment == "gym":
            suitable_workouts = suitable_workouts[
                (suitable_workouts['equipment'] == "gym")
            ]
            logger.info(f"Filtered to {len(suitable_workouts)} gym equipment exercises")
        else:
            suitable_workouts = suitable_workouts[
                (suitable_workouts['equipment'] == "Нет")
            ]
            logger.info(f"Filtered to {len(suitable_workouts)} bodyweight exercises")

        if len(suitable_workouts) == 0:
            logger.warning("No suitable exercises found, returning default workout")
            return self._get_default_workout()

        # Progressive overload: Increase reps/time based on successful completions
        if feedback_history:
            successful_workouts = sum(1 for f in recent_feedbacks if f['feedback'] in ['good', 'too_easy'])
            if successful_workouts >= 3:  # If user completed 3 or more workouts successfully
                progression_factor = 1.1  # Increase by 10%
                logger.info("Applying progressive overload - increasing intensity by 10%")
            else:
                progression_factor = 1.0
        else:
            progression_factor = 1.0

        # Include all matching exercises in their original order
        exercises = []
        for _, exercise in suitable_workouts.iterrows():
            exercise_data = {}

            # Add name (required field)
            exercise_data['name'] = exercise['name']

            # Add target muscle if it exists and is not empty
            if pd.notna(exercise['target_muscle']) and str(exercise['target_muscle']).strip():
                exercise_data['target_muscle'] = exercise['target_muscle']

            # Only add optional fields if they exist and are not empty or 'nan'
            if pd.notna(exercise['difficulty']) and str(exercise['difficulty']).strip():
                difficulty = str(exercise['difficulty']).strip()
                if difficulty.lower() != 'nan' and difficulty.strip():
                    exercise_data['difficulty'] = difficulty
                    logger.info(f"Added difficulty for {exercise['name']}: {difficulty}")

            # Validate and add GIF URL if present
            if pd.notna(exercise['gif']) and str(exercise['gif']).strip():
                gif_url = str(exercise['gif']).strip()
                if gif_url.lower() != 'nan' and (gif_url.startswith('http://') or gif_url.startswith('https://')):
                    try:
                        # Additional validation for the GIF URL
                        if gif_url.lower().endswith(('.gif', '.mp4')):
                            exercise_data['gif_url'] = gif_url
                            logger.info(f"Added GIF URL for {exercise['name']}: {gif_url}")
                        else:
                            logger.warning(f"Invalid GIF URL format for {exercise['name']}: {gif_url}")
                    except Exception as e:
                        logger.error(f"Error processing GIF URL for {exercise['name']}: {str(e)}")

            # Apply progressive overload to numeric fields
            for field in ['time', 'reps']:
                if pd.notna(exercise[field]) and str(exercise[field]).strip():
                    try:
                        value = float(str(exercise[field]).strip())
                        if value > 0:
                            # Apply progression factor to time and reps
                            adjusted_value = int(value * progression_factor)
                            exercise_data[field] = adjusted_value
                            logger.info(f"Added {field} for {exercise['name']}: {adjusted_value} (after progression)")
                    except (ValueError, TypeError):
                        continue

            # Handle other numeric fields without progression
            for field in ['circuits', 'circuits_rest', 'exercises_rest']:
                if pd.notna(exercise[field]) and str(exercise[field]).strip():
                    try:
                        value = float(str(exercise[field]).strip())
                        if value > 0:
                            exercise_data[field] = int(value)
                            logger.info(f"Added {field} for {exercise['name']}: {value}")
                    except (ValueError, TypeError):
                        continue

            # Handle weight field separately as it might contain ranges
            if pd.notna(exercise['weight']) and str(exercise['weight']).strip():
                weight = str(exercise['weight']).strip()
                if weight.lower() != 'nan' and weight.strip():
                    exercise_data['weight'] = weight
                    logger.info(f"Added weight for {exercise['name']}: {weight}")

            exercises.append(exercise_data)
            logger.info(f"Processed exercise: {exercise_data}")

        logger.info(f"Generated workout with {len(exercises)} exercises")
        if exercises:
            logger.info(f"First exercise data: {exercises[0]}")

        return {
            'exercises': exercises,
            'total_exercises': len(exercises),
            'current_exercise': 0,
            'current_circuit': 1
        }

    def _get_default_workout(self):
        """Return default workout if no suitable workout found"""
        return {
            'exercises': [
                {
                    'name': 'Приседания',
                    'target_muscle': 'ноги',
                    'reps': 15,
                    'circuits': 2,
                    'circuits_rest': 300,
                    'exercises_rest': 30
                }
            ],
            'total_exercises': 1,
            'current_exercise': 0,
            'current_circuit': 1
        }