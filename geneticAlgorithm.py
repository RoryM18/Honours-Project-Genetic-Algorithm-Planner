import datetime 
import random 
import sqlite3

con = sqlite3.connect('data.db')
cursor = con.cursor()
cursor.execute("SELECT * FROM planner")
task = cursor.fetchall()
con.close()

# Extract tasks from the result set
tasks = [{'task_name': row[1], 'date': row[3], 'start_time': row[4], 'end_time': row[5], 'priority': row[6]} for row in task]


#Define genetic algorithm parameters 

populationSize = 100
mutationRate = 0.01
numGenerations = 50
tournamentSize = 5
convergenceThreshold = 0.001  # Adjust as needed

# Function to initialise a random schedule 
def initialiseSchedule(tasks, populationSize):
    population = []
    for _ in range(populationSize):
         # Create a schedule by shuffling the tasks and ensuring priorities are respected
         shuffledTasks = random.sample(tasks, len(tasks))
         population.append(shuffledTasks)
    return population

# Function to evaluate fitness of a schedule 
def evaluateSchedule(schedule):
    fitness = 0
    for task in schedule:
         # Add fitness based on task priorities, constraints, etc.
        priority = task['priority']
        if priority == 1:
             # Adjust weight based on one-time tasks
            fitness += 5
        elif priority == 2:
            # Adjust weight based on occasional tasks
            fitness += 3
        elif priority == 3:
            # Adjust weight based on regular tasks
            fitness += 2
        elif priority == 4:
            # Adjust weight based on everyday tasks
            fitness += 1

         # Add penalty for overlapping tasks (if any)
         # Implement your overlapping check logic here
    return fitness

# Function to select parents using tournament selection
def tournamentSelection(population, fitnessScores, tournamentSize):
    selectedParents = []
    for _ in range(len(population)):
        tournamentContestants = random.sample(range(len(population)), tournamentSize)
        winnerIndex = max(tournamentContestants, key=lambda idx: fitnessScores[idx])
        selectedParents.append(population[winnerIndex])
    return selectedParents

# Function to select the next generation of schedules based on fitness scores
def selectNextGeneration(population, fitnessScores):
    sortedPopulation = [x for _, x in sorted(zip(fitnessScores, population), key=lambda pair: pair[0], reverse=True)]
    return sortedPopulation[:populationSize]

# Function to perform crossover between two parent schedules
def crossover(schedule1, schedule2):
    crossoverPoint = random.randint(0, min(len(schedule1), len(schedule2)))
    child1 = schedule1[:crossoverPoint] + schedule2[crossoverPoint:]
    child2 = schedule2[:crossoverPoint] + schedule1[crossoverPoint:]
    return child1, child2

# Function to apply random changes to the schedule (mutation)
def mutate(schedule):
    for _ in range(len(schedule)):
        if random.uniform(0, 1) < mutationRate:
            # Swap two tasks
            swapIndex1 = random.randint(0, len(schedule) - 1)
            swapIndex2 = random.randint(0, len(schedule) - 1)
            schedule[swapIndex1], schedule[swapIndex2] = schedule[swapIndex2], schedule[swapIndex1]
    return schedule

# Function to perform the genetic algorithm
def geneticAlgorithm():
    # Step 1: Initialise the population
    population = initialiseSchedule(tasks, populationSize)

    previousBestFitness = float('inf')  # Initialize with a large value
    for generation in range(numGenerations):
        # Step 2: Evaluate fitness
        fitnessScores = [evaluateSchedule(schedule) for schedule in population]

        # Step 3: Selection 
        selectedParents = tournamentSelection(population, fitnessScores, tournamentSize)

        # Step 4: Crossover
        children = []
        for i in range(0, len(selectedParents), 2):
            parent1 = selectedParents[i]
            parent2 = selectedParents[i + 1]
            child1, child2 = crossover(parent1, parent2)
            children.extend([child1, child2])

        # Step 5: Mutation
        for child in children:
            mutate(child)

        # Step 6: Create Next generation 
        population = selectNextGeneration(population + children, fitnessScores)

        # Return the best schedule from the final population
        bestSchedule = max(population, key=evaluateSchedule)
        bestFitness = evaluateSchedule(bestSchedule)

        # Print current best fitness for monitoring
        print(f"Generation {generation + 1}: Best Fitness - {bestFitness}")

        # Check for convergence
        if previousBestFitness < convergenceThreshold:
            print(f"Converged at generation {generation + 1}")
            break

        previousBestFitness = bestFitness

    print(f"Best Schedule: {bestSchedule}")
    return bestSchedule