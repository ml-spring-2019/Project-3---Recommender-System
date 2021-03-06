'''
    features: 2d numpy array
    row - feature scores
    column - joke features

    preferences: 2d numpy array
    row - preference scores
    column - user preferences

    ratings: 2d numpy array
    row - user ratings
    column - joke ratings
'''

import sys
import pdb
import re
import random
import numpy as np
import json

CONFIG_FILE = "config.json"
CF_LAMBDA = 0
CF_ALPHA = 0

ALPHA = 0.0
LAMBDA = 0.0
NUMBER_OF_JOKES = 0
NUMBER_OF_USERS = 0
UNRATED = 0.0
FEATURE_COUNT = 5
RATING_MEANS = []
GD_ITERATION = 0


def main(argv, argc):
    if argc < 2:
        print("Usage: python main.py <jester-data> [out-filename]")
        exit(1)
#   ---------
    config_read()
#   read file
    ratings, answeredCount = fileIO(argv)
#   compute mean normalization
    rating_means = []
    features = np.asarray(init_data(FEATURE_COUNT, len(ratings[0])))
    prefs = np.asarray(init_data(FEATURE_COUNT, len(ratings)))
    global NUMBER_OF_JOKES, NUMBER_OF_USERS
    NUMBER_OF_JOKES, NUMBER_OF_USERS = np.shape(ratings)[1], np.shape(ratings)[0]
    meanNormalization(ratings, rating_means)
#   ---------
    error_rates = []

    outFilename = "out.csv"
    if argc == 3:
        outFilename = argv[2]

#   calculate the sqaured error rates of each iteration of the collaborative filtering algorithm
    outFile = open(outFilename, "w+")
    for i in range(GD_ITERATION):
        print("-> collaborativeFilteringAlgorithm() - iteration " + str(i+1) + "/" + str(GD_ITERATION))
        error_rate = collaborativeFilteringAlgorithm(features, prefs, np.asarray(ratings))
        error_rates.append(error_rate)
        outFile.write(str(error_rate) + "\n")

    print("Successfully wrote data file out to \"" + outFilename + "\"")
    print("\nRun this to generate plot:")
    print("python plot.py " + outFilename + "\n")

    return 0


#   ----------------------- calculate cost function
def calculateCostFunction(jokes_matrix, users_matrix, ratings):
#   calculate predicted ratings from joke and user matrices
    predictedRatings = findPredictedRatings(jokes_matrix, users_matrix)
#   subtract difference matrix by ratings matrix
    difference = predictedRatings
    ratings_range = np.shape(ratings)
    ratings = addJokeRatingMean(ratings)

    for i in range(ratings_range[0]):
        for j in range(ratings_range[1]):
            if ratings[i][j] != UNRATED:
                difference [i][j] = difference[i][j] - ratings[i][j]
            else:
                difference[i][j] = UNRATED
#   square error_rate values
    error_ratings = np.where(difference != UNRATED, difference**2, UNRATED)

#   sum total error rate of predicted ratings
    total_error_rate = 0
    for error_rating_row in error_ratings:
        for error_rating in error_rating_row:
            if int(error_rating) != UNRATED:
                total_error_rate += error_rating
    return total_error_rate

#   ----------------------- compute regularized gradient descent on joke or user matrix
def regularized_gradient_descent(RANGE, features, prefs, bool, ratings):

    dependent_rating, independent_rating = matrix_assignment(features, prefs, bool)

    for i in range(RANGE):
        actual_ratings = ratings[i,:] if not bool else ratings[:,i]
        for k in range(FEATURE_COUNT):

            predicted_rating = np.matmul(np.transpose(independent_rating), dependent_rating[:,i])

            error_rate = np.where(actual_ratings != UNRATED, predicted_rating - actual_ratings, UNRATED)

            for itr in range(np.shape(error_rate)[0]):
                if error_rate[itr] != UNRATED:
                    error_rate[itr] = independent_rating[k][itr] * error_rate[itr]

#            gradient_descent_vector = np.where(error_rate != UNRATED, regularizing_val + error_rate, error_rate)
            # pdb.set_trace()
            sum = 0
            for num in error_rate:
                if num != UNRATED:
                    sum += num

            regularizing_val = LAMBDA*dependent_rating[k][i]
            gradient_descent_val = sum + regularizing_val
            gradient_descent_val = gradient_descent_val * ALPHA

            dependent_rating[k][i] = dependent_rating[k][i]-gradient_descent_val

    return dependent_rating

#   ----------------------- recommender system ~ collaborative filtering algorithm
def collaborativeFilteringAlgorithm(features, prefs, ratings):
    num_jokes = np.shape(features)[1]
    num_users = np.shape(prefs)[1]
    feature_gd = True
#   minimize features
    print("\t-> regularized_gradient_descent() - features")
    features = regularized_gradient_descent(NUMBER_OF_JOKES, features, prefs, feature_gd, ratings)
#   minimize preferences
    print("\t-> regularized_gradient_descent() - prefs")
    prefs = regularized_gradient_descent(NUMBER_OF_USERS, features, prefs, not feature_gd, ratings)
#   find total error rate
    print("\t-> calculateCostFunction()")
    error_rate = calculateCostFunction(features, prefs, ratings)
    print("\tresulting error rate: " + str(error_rate))
    return error_rate

#   ----------------------- initialize data
def config_read():
    global ALPHA, LAMBDA, NUMBER_OF_JOKES, UNRATED, FEATURE_COUNT, GD_ITERATION
    #print("-> config_read()")
    configs = json.loads(open(CONFIG_FILE, 'r').read())
    ALPHA = float(configs["alpha"])
    LAMBDA = float(configs["lambda"])
    UNRATED = float(configs["unrated_representation"])
    GD_ITERATION = int(configs["iterations_to_run"])

def init_data(rows, cols):
    #print("-> init_data(rows=" + str(rows) + ", cols=" + str(cols) + ")")
    features = []
    for _ in range(0, rows):
        tempFeatures = []
        for _ in range(0, cols):
            # random number between -1.0 and 1.0 inclusive
            randomNum = round(float(random.randint(0, 200)) / 100 - 1, 2)
            tempFeatures.append(randomNum)
        features.append(tempFeatures)
    return features

#   ----------------------- means normalization
def meanNormalization(ratings, rating_means):
    #print("-> meanNormalization()")
    global RATING_MEANS
    for joke in range(0, NUMBER_OF_JOKES):

        jokeRatingCount = 0.0
        jokeRatingTotal = 0.0

        for d in ratings:
            rating = d[joke]
            if not isUnrated(rating):
                jokeRatingTotal += rating
                jokeRatingCount += 1

        joke_rating_mean = jokeRatingTotal / jokeRatingCount

        for i in range(0, len(ratings)):
            rating = ratings[i][joke]
            if not isUnrated(rating):
                ratings[i][joke] -= joke_rating_mean
        RATING_MEANS.append(joke_rating_mean)

#   ------------------------ suplementary functions - begin
def matrix_assignment(features, prefs, bool):
    if bool:
        return features, prefs
    return prefs, features

def isUnrated(rating):
    return rating == UNRATED

def add(a, b):
    return a + b

def findPredictedRatings(jokes_matrix, users_matrix):
    predictedRatings = np.matmul(np.transpose(users_matrix), jokes_matrix)
    return addJokeRatingMean(predictedRatings)

def addJokeRatingMean(rating_data):
    global RATING_MEANS
    for i in range(np.shape(RATING_MEANS)[0]):
        rating_data[i] = np.where(rating_data[i] != UNRATED, RATING_MEANS[i] + rating_data[i], UNRATED)
#        rating_data[i][j] = RATING_MEANS[i] + rating_data[i]
    return rating_data
#   ------------------------ suplementary functions - end

#   ----------------------- read files - begin
def fileIO(argv):
    #print("-> fileIO()")
    DATA_FILE = 1
    ratings = []
    file = open(argv[DATA_FILE], 'r')
    answeredCount = []
    for line in file.readlines():
        splitLine = line.split(",")
        answeredCount.append(str(re.sub('[!\xef\xbb\xbf]', '', splitLine[0])))
        tempList = []
        for i in range(1, len(splitLine)):
            tempList.append(float(splitLine[i]))
        ratings.append(tempList)
    return ratings, answeredCount

#   ----------------------- read files - end

if __name__ == "__main__":
    main(sys.argv, len(sys.argv))


'''
    def regularized_gradient_descent(num_jokes, num_users, features, prefs, ratings):
    error_rate = 0

    itr = 0
    for k in range(FEATURE_COUNT):
    for i in range(num_jokes):
    # continual gradient descent for one cell
    previous_error_rate = 100
    while (True):
    itr += 1
    previously_optimized_feature = features[k][i]
    regularized_variable = LAMBDA*features[k][i]
    gradient_descent_val = 0
    for j in range(num_users):
    if ratings[j][i] != 99:
    predicted_rating = np.dot(np.transpose(prefs[:,j]), features[:,i])
    error_rate = (predicted_rating-ratings[j][i])
    altered_error_rate = error_rate * prefs[k][j]
    gradient_descent_val += altered_error_rate + regularized_variable
    pdb.set_trace()

    if (error_rate**2 > previous_error_rate**2):

    break
    features[k][i] = features[k][i] - (gradient_descent_val * ALPHA)


    previous_error_rate = error_rate

    #   need to do the for loops for the preferences matrix
    return
'''
