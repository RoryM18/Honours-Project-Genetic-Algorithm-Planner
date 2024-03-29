import datetime 
import random 
import sqlite3
import prettytable

con = sqlite3.connect('data.db')
cursor = con.cursor()
cursor.execute("SELECT * FROM planner")
task = cursor.fetchall()
con.close()

# Extract tasks from the result set
tasks = [{'task_name': row[1], 'date': row[3], 'start_time': row[4], 'end_time': row[5], 'priority': row[6]} for row in task]


# Test Data
test_tasks = [
    {'task_name': 'Work', 'date': '2024-02-26', 'start_time': '09:00', 'end_time': '10:30', 'priority': 1},
    {'task_name': 'Gym', 'date': '2024-02-26', 'start_time': '11:00', 'end_time': '12:30', 'priority': 2},
    {'task_name': 'Reading', 'date': '2024-02-26', 'start_time': '14:00', 'end_time': '15:30', 'priority': 3},
    {'task_name': 'Studying', 'date': '2024-02-26', 'start_time': '16:00', 'end_time': '17:30', 'priority': 4},
    {'task_name': 'Gym', 'date': '2024-02-27', 'start_time': '10:00', 'end_time': '11:30', 'priority': 1},
    {'task_name': 'Studying', 'date': '2024-02-27', 'start_time': '12:00', 'end_time': '13:30', 'priority': 2},
    {'task_name': 'Shopping', 'date': '2024-02-27', 'start_time': '15:00', 'end_time': '16:30', 'priority': 3},
    {'task_name': 'Reading', 'date': '2024-02-27', 'start_time': '17:00', 'end_time': '18:30', 'priority': 4},
    # Add more tasks as needed
]

#Define genetic algorithm parameters 

########## Genetic Algorithm Parameters ##########

populationSize = 40
mutationRate = 0.01
numGenerations = 5000
tournamentSize = 10
convergenceThreshold = 0.01  # Adjust as needed

##################################################

########## Genetic Algorithm Initalisation ##########

# Function to initialize a random schedule
def initialize_test_schedule(tasks, population_size):
    test_population = []
    for _ in range(population_size):
        shuffled_tasks = random.sample(tasks, len(tasks))
        test_population.append(shuffled_tasks)
    return test_population

# Function to initialise a random schedule 
def initialiseSchedule(tasks, populationSize):
    population = []
    for _ in range(populationSize):
         # Create a schedule by shuffling the tasks and ensuring priorities are respected
         shuffledTasks = random.sample(tasks, len(tasks))
         population.append(shuffledTasks)
    return population

##################################################


########## Genetic Algorithm Evaluation Operator ##########

# Function to evaluate fitness of a schedule
def evaluateSchedule(schedule):
    fitness = 0

    for i, task in enumerate(schedule):
        priority = task['priority']
        date = task['date']
        start_time = task['start_time']
        end_time = task['end_time']

        # Constraint 1: Avoid overlapping tasks
        for other_task in schedule[i + 1:]:
            other_start_time = other_task['start_time']
            other_end_time = other_task['end_time']

            if date == other_task['date']:
                if not (end_time <= other_start_time or start_time >= other_end_time):
                    fitness += 0.1  # Penalize for overlapping tasks
                else:
                    fitness -= 0.01 # award for non-overlapping tasks

        # Constraint 2: Minimum Break Duration
        if i > 0:
            prev_end_time = datetime.datetime.strptime(schedule[i - 1]['end_time'], "%H:%M")
            current_start_time = datetime.datetime.strptime(start_time, "%H:%M")
            break_duration = (current_start_time - prev_end_time).total_seconds() / 60
            min_break_duration = 15  # Minimum break duration in minutes
            if break_duration < min_break_duration:
                fitness += 0.1  # Penalize for insufficient break duration
            else:
                fitness -= 0.01  # Award for approtiate break duration

    return fitness

##################################################

########## Genetic Algorithm Selection Operators ##########

# Function to select parents using tournament selection
def tournamentSelection(population, fitnessScores, tournamentSize):
    selectedParents = []
    for _ in range(len(population)):
        tournamentContestants = random.sample(range(len(population)), tournamentSize)
        winnerIndex = max(tournamentContestants, key=lambda idx: fitnessScores[idx])
        selectedParents.append(population[winnerIndex])
    return selectedParents

def rouletteWheelSelection(population, fitnessScores):
    totalFitness = sum(fitnessScores)
    probabilities = [fitness / totalFitness for fitness in fitnessScores]

    selectedParents = []
    for _ in range(len(population)):
        spin = random.uniform(0, 1)
        cumulativeProbability = 0

        for i, probability in enumerate(probabilities):
            cumulativeProbability += probability
            if spin <= cumulativeProbability:
                selectedParents.append(population[i])
                break

    return selectedParents

def rankBasedSelection(population, fitnessScores):
    sortedPopulation = [x for _, x in sorted(zip(fitnessScores, population), key=lambda pair: pair[0], reverse=True)]
    selectionProbabilities = [((2 * (i + 1)) / (len(population) * (len(population) + 1))) for i in range(len(population))]

    selectedParents = []
    for _ in range(len(population)):
        spin = random.uniform(0, 1)
        cumulativeProbability = 0

        for i, probability in enumerate(selectionProbabilities):
            cumulativeProbability += probability
            if spin <= cumulativeProbability:
                selectedParents.append(sortedPopulation[i])
                break

    return selectedParents

# Function to select the next generation of schedules based on fitness scores
def selectNextGeneration(population, fitnessScores):
    sortedPopulation = [x for _, x in sorted(zip(fitnessScores, population), key=lambda pair: pair[0], reverse=True)]
    return sortedPopulation[:populationSize]

##################################################


########## Genetic Algorithm Crossover Operators ##########

# Function to perform crossover between two parent schedules
def onePointcrossover(schedule1, schedule2):
    crossoverPoint = random.randint(0, min(len(schedule1), len(schedule2)))
    child1 = schedule1[:crossoverPoint] + schedule2[crossoverPoint:]
    child2 = schedule2[:crossoverPoint] + schedule1[crossoverPoint:]
    return child1, child2

def twoPointcrossover(schedule1, schedule2):
    crossoverPoints = sorted(random.sample(range(min(len(schedule1)), len(schedule2)), k=2))
    child1 = schedule1[:crossoverPoints[0]] + schedule2[crossoverPoints[0]:crossoverPoints[1]] + schedule1[crossoverPoints[1]:]
    child2 = schedule2[:crossoverPoints[0]] + schedule1[crossoverPoints[0]:crossoverPoints[1]] + schedule2[crossoverPoints[1]:]
    return child1, child2

def uniform_crossover(schedule1, schedule2):
    child1 = []
    child2 = []

    for gene1, gene2 in zip(schedule1, schedule2):
        if random.choice([True, False]):
            child1.append(gene1)
            child2.append(gene2)
        else:
            child1.append(gene2)
            child2.append(gene1)

    return child1, child2

##################################################


########## Genetic Algorithm Mutation Operator ##########

def mutate(schedule):
    for task in schedule:

        #Check if task has priority level 4
        if task['priority'] == 4:
            continue

        if random.uniform(0, 1) < mutationRate:
            task['start_time'], task['end_time'] = mutate_time(task['start_time'], task['end_time'], schedule)
        else:
            # Mutate end time
            mutated_times = mutate_time(task['start_time'], task['end_time'], schedule)
            task['start_time'], task['end_time'] = mutated_times

    return schedule

def mutate_time(current_start_time, current_end_time, all_tasks):
    time_format = "%H:%M"

    # Mutate time by adding or subtracting a random duration in multiples of 5 (e.g., 5, 10, 15 minutes)
    mutation_minutes = random.randint(1, 24) * 5  # Random multiples of 5 up to 120 minutes

    # Convert current times to datetime objects
    start_time_obj = datetime.datetime.strptime(current_start_time, time_format)
    end_time_obj = datetime.datetime.strptime(current_end_time, time_format)

    # Randomly choose whether to add or subtract time
    if random.choice([True, False]):
        mutated_start_time = start_time_obj + datetime.timedelta(minutes=mutation_minutes)
        mutated_end_time = end_time_obj + datetime.timedelta(minutes=mutation_minutes)
    else:
        mutated_start_time = start_time_obj - datetime.timedelta(minutes=mutation_minutes)
        mutated_end_time = end_time_obj - datetime.timedelta(minutes=mutation_minutes)

    # Round the mutated times to the nearest multiple of 5
    mutated_start_time = round_time_to_multiple(mutated_start_time, 5)
    mutated_end_time = round_time_to_multiple(mutated_end_time, 5)

    return mutated_start_time.strftime(time_format), mutated_end_time.strftime(time_format)

def round_time_to_multiple(time_obj, multiple):
    rounded_minute = (time_obj.minute // multiple) * multiple
    return datetime.datetime(
        time_obj.year, time_obj.month, time_obj.day,
        time_obj.hour, rounded_minute
    )

def task_overlap(start_time, end_time, task):
    task_start_time = datetime.datetime.strptime(task['start_time'], "%H:%M")
    task_end_time = datetime.datetime.strptime(task['end_time'], "%H:%M")
    return not (end_time <= task_start_time or start_time >= task_end_time)


##################################################

# Function to display schedule in table format in the command Line Interface
def displayScheduleTable(schedule):
    table = prettytable.PrettyTable()
    table.field_names = ['Task Name', 'Date', 'Start Time', 'End Time', 'Priority']

    for task in schedule:
        table.add_row([task['task_name'], task['date'], task['start_time'], task['end_time'], task['priority']])

    print(table)


########## Genetic Algorithm Main Function ##########

# Function to perform the genetic algorithm
def geneticAlgorithm(tasks):
    # Step 1: Initialise the population
    population = initialiseSchedule(tasks, populationSize)

    def best_fitness(population):
        return max(population, key=evaluateSchedule)

    def replace(population, children):
        # Combine the population and children, and select the best individual
        combined_population = population + children
        fitness_scores = [evaluateSchedule(schedule) for schedule in combined_population]
        sorted_population = [x for _, x in sorted(zip(fitness_scores, combined_population), key=lambda pair: pair[0], reverse=True)]

        return sorted_population[:populationSize]

    previous_best_fitness = float('inf')  # Initialize with a large value
    for generation in range(numGenerations):
        # Step 2: Evaluate fitness
        fitness_scores = [evaluateSchedule(schedule) for schedule in population]

        # Step 3: Selection
        selected_parents = tournamentSelection(population, fitness_scores, tournamentSize)

        # Step 4: Crossover
        children = []
        for i in range(0, len(selected_parents), 2):
            parent1 = selected_parents[i]
            parent2 = selected_parents[i + 1]
            child1, child2 = uniform_crossover(parent1, parent2)
            children.extend([child1, child2])

        # Step 5: Mutation
        for child in children:
            mutate(child)

        # Step 6: Create Next generation
        population = selectNextGeneration(population + children, fitness_scores)
        replace(population, children)

        # Return the best schedule from the final population
        best_schedule = max(population, key=evaluateSchedule)
        best_fitness = evaluateSchedule(best_schedule)

        # Print current best fitness for monitoring
        print(f"Generation {generation + 1}: Best Fitness - {best_fitness}")

        # Check for convergence
        if previous_best_fitness == convergenceThreshold:
            print(f"Converged at generation {generation + 1}")
            break

        previous_best_fitness = best_fitness

    # Print the best schedule in table format
    print("Best Schedule:")
    displayScheduleTable(best_schedule)

    return best_schedule

##################################################

# Using the genetic algorithm with the test data
#test_population_size = 10  # Adjust as needed
#test_population = initialize_test_schedule(test_tasks, test_population_size)
#best_schedule = geneticAlgorithm(test_population)