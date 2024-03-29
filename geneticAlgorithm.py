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


#Define genetic algorithm parameters 

########## Genetic Algorithm Parameters ##########

populationSize = 40
mutationRate = 0.01
numGenerations = 5000
tournamentSize = 10
convergenceThreshold = 0.01

##################################################

########## Genetic Algorithm Initalisation ##########

# Function to initialise a random schedule 
def initialiseSchedule(tasks, populationSize):
    population = []
    # Create a population of schedules by shuffling the tasks
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
        startTime = task['start_time']
        endTime = task['end_time']

        # Constraint 1: Avoid overlapping tasks
        for otherTask in schedule[i + 1:]:
            otherStartTime = otherTask['start_time']
            otherEndTime = otherTask['end_time']

            if date == otherTask['date']:
                if not (endTime <= otherStartTime or startTime >= otherEndTime):
                    fitness += 0.1  # Penalize for overlapping tasks
                else:
                    fitness -= 0.01 # award for non-overlapping tasks

        # Constraint 2: Minimum Break Duration
        if i > 0:
            prevEndTime = datetime.datetime.strptime(schedule[i - 1]['end_time'], "%H:%M")
            currentStartTime = datetime.datetime.strptime(startTime, "%H:%M")
            breakDuration = (currentStartTime - prevEndTime).total_seconds() / 60
            minBreakDuration = 15  # Minimum break duration in minutes
            if breakDuration < minBreakDuration:
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
    crossoverPoints = sorted(random.sample(range(min(len(schedule1), len(schedule2))), 2))
    child1 = schedule1[:crossoverPoints[0]] + schedule2[crossoverPoints[0]:crossoverPoints[1]] + schedule1[crossoverPoints[1]:]
    child2 = schedule2[:crossoverPoints[0]] + schedule1[crossoverPoints[0]:crossoverPoints[1]] + schedule2[crossoverPoints[1]:]
    return child1, child2

def uniformCrossover(schedule1, schedule2):
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
            task['start_time'], task['end_time'] = mutateTime(task['start_time'], task['end_time'], schedule)
        else:
            # Mutate end time
            mutatedTimes = mutateTime(task['start_time'], task['end_time'], schedule)
            task['start_time'], task['end_time'] = mutatedTimes

    return schedule

def mutateTime(currentStartTime, currentEndTime, allTasks):
    timeFormat = "%H:%M"

    # Mutate time by adding or subtracting a random duration in multiples of 5 (e.g., 5, 10, 15 minutes)
    mutationMinutes = random.randint(1, 24) * 5  # Random multiples of 5 up to 120 minutes

    # Convert current times to datetime objects
    startTimeObj = datetime.datetime.strptime(currentStartTime, timeFormat)
    endTimeObj = datetime.datetime.strptime(currentEndTime, timeFormat)

    # Randomly choose whether to add or subtract time
    if random.choice([True, False]):
        mutatedStartTime = startTimeObj + datetime.timedelta(minutes=mutationMinutes)
        mutatedEndTime = endTimeObj + datetime.timedelta(minutes=mutationMinutes)
    else:
        mutatedStartTime = startTimeObj - datetime.timedelta(minutes=mutationMinutes)
        mutatedEndTime = endTimeObj - datetime.timedelta(minutes=mutationMinutes)

    # Round the mutated times to the nearest multiple of 5
    mutatedStartTime = roundTimeToMultiple(mutatedStartTime, 5)
    mutatedEndTime = roundTimeToMultiple(mutatedEndTime, 5)

    return mutatedStartTime.strftime(timeFormat), mutatedEndTime.strftime(timeFormat)

def roundTimeToMultiple(timeObj, multiple):
    roundedMinute = (timeObj.minute // multiple) * multiple
    return datetime.datetime(
        timeObj.year, timeObj.month, timeObj.day,
        timeObj.hour, roundedMinute
    )

def taskOverlap(startTime, endTime, task):
    taskStartTime = datetime.datetime.strptime(task['start_time'], "%H:%M")
    taskEndTime = datetime.datetime.strptime(task['end_time'], "%H:%M")
    return not (endTime <= taskStartTime or startTime >= taskEndTime)


##################################################

# Function to display schedule in table format in the command Line Interface
def displayScheduleTable(schedule):
    table = prettytable.PrettyTable()
    table.fieldNames = ['Task Name', 'Date', 'Start Time', 'End Time', 'Priority']

    for task in schedule:
        table.add_row([task['task_name'], task['date'], task['start_time'], task['end_time'], task['priority']])

    print(table)


########## Genetic Algorithm Main Function ##########

# Function to perform the genetic algorithm
def geneticAlgorithm(tasks, progressCallback=None):

    # Step 1: Initialise the population
    population = initialiseSchedule(tasks, populationSize)

    def bestFitness(population):
        return max(population, key=evaluateSchedule)

    def replace(population, children):
        # Combine the population and children, and select the best individual
        combinedPopulation = population + children
        fitnessScores = [evaluateSchedule(schedule) for schedule in combinedPopulation]
        sortedPopulation = [x for _, x in sorted(zip(fitnessScores, combinedPopulation), key=lambda pair: pair[0], reverse=True)]

        return sortedPopulation[:populationSize]

    previousBestFitness = float('inf')  # Initialize with a large value
    for generation in range(numGenerations):

        if progressCallback:
            progressCallback((generation + 1) * 100 / numGenerations)

        # Step 2: Evaluate fitness
        fitnessScores = [evaluateSchedule(schedule) for schedule in population]

        # Step 3: Selection
        selectedParents = tournamentSelection(population, fitnessScores, tournamentSize)

        # Step 4: Crossover
        children = []
        for i in range(0, len(selectedParents), 2):
            parent1 = selectedParents[i]
            parent2 = selectedParents[i + 1]
            child1, child2 = uniformCrossover(parent1, parent2)
            children.extend([child1, child2])

        # Step 5: Mutation
        for child in children:
            mutate(child)

        # Step 6: Create Next generation
        population = selectNextGeneration(population + children, fitnessScores)
        replace(population, children)

        # Return the best schedule from the final population
        bestSchedule = max(population, key=evaluateSchedule)
        bestFitness = evaluateSchedule(bestSchedule)

        # Print current best fitness for monitoring
        print(f"Generation {generation + 1}: Best Fitness - {bestFitness}")

        # Check for convergence
        if previousBestFitness == convergenceThreshold:
            print(f"Converged at generation {generation + 1}")
            break

        previousBestFitness = bestFitness

    # Print the best schedule in table format
    print("Best Schedule:")
    displayScheduleTable(bestSchedule)

    return bestSchedule

##################################################