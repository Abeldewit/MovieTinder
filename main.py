import pandas as pd
import numpy as np
from ast import literal_eval
from gui import UserInterface
from sklearn.utils import shuffle
from sklearn.tree import DecisionTreeClassifier
#from modAL.models import ActiveLearner
from sklearn.ensemble import RandomForestClassifier
import random
import csv
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity




class AccuracyMeasure:
    def __init__(self):
        self.number_bad = 0
        self.number_good = 0
        self.number_total = 0

    def update(self, user_score):
        if user_score != 0:
            self.number_total += 1
        if user_score == -1:
            self.number_bad += 1
        elif user_score == 1:
            self.number_good += 1

    def print_score(self):
        if self.number_total != 0:
            print("Accuracy: {}%".format((self.number_good / self.number_total) * 100))
        else:
            return 0

# constant which determines the amount of movies in a genre's top
topX = 40
df = pd.read_csv('data/movieData_Dummie.csv')
dfTitles = pd.read_csv('data/MovieData.csv')
df['user_score'] = -2
score_writer = csv.writer(open('data/user/scored.csv', 'a'))
UI = UserInterface()
scoredArr = []  # array where all the imdb ids and scores are handled.
AM = AccuracyMeasure()

def main():
    begin()
    UI.run()

    return 0


def begin():
    # get the top genres directly from the top 100
    tmp_df = pd.read_csv('data/topMovies/top100.csv')

    for index in range(5):
        movieIndex = random.randint(0, 100)
        tmp_movie = tmp_df.iloc[movieIndex]
        UI.add_movie(tmp_movie.imdb_id)
    print(get_recommendations('The Bodyguard'))
    return 0


def choose_new():
    top_genre_list = os.listdir('data/topMovies/')
    # Pick a random genre
    random_genre = random.randint(0, len(top_genre_list) - 1)
    genre = top_genre_list[random_genre]
    tmp_df = pd.read_csv('data/topMovies/' + genre)

    # Pick a random movie
    random_movie = tmp_df.loc[random.randint(0, len(tmp_df)-1)]['imdb_id']
    tmp_movie = df.loc[df['imdb_id'] == random_movie]
    # print(tmp_movie['user_score'])

    if int(tmp_movie['user_score']) == -2:
        UI.add_movie(tmp_movie.imdb_id.values[0])

    else:
        choose_new()


# print(UI.get_movieList())

# topX = the amount of movies we want in the genre specific database
def createTable(genre, indexOfBest, df, topX):
    # TODO Goeie documentatie wat deze functie doet
    topMoviesIndex = []
    count = 0

    for index in indexOfBest:

        if genre in df.iloc[index]['genres'] and count < topX:
            count += 1
            topMoviesIndex.append(index)

    dfTopMovies = pd.DataFrame(df.iloc[topMoviesIndex[0]])

    # wrong dimensions
    for index in topMoviesIndex[1:]:
        tempDf = pd.DataFrame(df.iloc[index])
        dfTopMovies = pd.concat([dfTopMovies, tempDf], axis=1)

    # flip it to get the correct dimensions
    dfTopMovies = dfTopMovies.transpose()

    # create csv file for the top movies
    dfName = 'data/topMovies/' + genre + '.csv'
    dfTopMovies.to_csv(dfName, sep=',', encoding='utf-8', index=False)

    return 0


def topXTables(topX, df):
    # TODO Goeie documentatie wat deze functie doet
    genres = dict()

    for index, subset in df.iterrows():
        genresArr = literal_eval(subset.genres)
        for genre in genresArr:
            if genre in genres:
                genres[genre] += 1
            else:
                genres[genre] = 1

    indexOfBest = df.weightedRating.sort_values(ascending=False).index
    for key in genres:
        genreTop = createTable(key, indexOfBest, df, topX)
        print("done ", key)

    return 0


def createTop100(df):
    # TODO Goeie documentatie wat deze functie doet
    dfTopInd = []

    for index in df.weightedRating.sort_values(ascending=False).head(100).index:
        dfTopInd.append(index)

    dfTop = pd.DataFrame(df.iloc[dfTopInd[0]])

    # wrong dimensions
    for index in dfTopInd[1:]:
        tempDf = pd.DataFrame(df.iloc[index])
        dfTop = pd.concat([dfTop, tempDf], axis=1)

    # flip it to get the correct dimensions
    dfTop = dfTop.transpose()

    dfTop.to_csv('data/topMovies/top100.csv', sep=',', encoding='utf-8', index=False)
    return 0


# This is where we get the title of the movie and the users score
def pass_user_score(score, imdb):
    if score != 0:
        df.loc[df['imdb_id'] == imdb, 'user_score'] = score

    # And here we write the scored movie to a csv file
    row = df.loc[df['imdb_id'] == imdb].iloc[0]
    score_writer.writerow([row['imdb_id'], row['user_score']])
    scoredArr.append((row['imdb_id'], row['user_score']))

    if len(scoredArr) < 20:
        choose_new()

    else:
        print("classification here")
        predictor()
        AM.update(score)

    AM.print_score()
    return 0


# TODO construct a predictor for the new suggestions based on a decision tree
def predictor():
    non_rated = df[df['user_score'] == -2]
    rated = df[df['user_score'] != -2]
    rated = rated[rated['user_score'] != 0]
    
    # non_rated = non_rated.select_dtypes(exclude=['object'])
    rated = rated.select_dtypes(exclude=['object'])


    X = np.array(rated.iloc[:, :-1])
    y = np.array(rated.iloc[:, -1])

    from sklearn.ensemble import RandomForestClassifier
    DTC = RandomForestClassifier(n_estimators=100)
    DTC.fit(X,y)


    #TODO make batches of random movies that have -2 as userscore, (batches of 1000)
    #we chose the one with the highest mean weightedrating
    non_rated_shuffle = shuffle(non_rated)
    splitArrays = np.array_split(non_rated_shuffle, 43)
    maxBatch = -1

    count = 0
    for dataFrame in splitArrays:

        meanRating = dataFrame['weightedRating'].mean()

        if meanRating > maxBatch:
            maxBatch = meanRating
            index = count
            dfBatch = dataFrame

        count += 1


    print("maxBatch = ", meanRating, "index = " ,index)

    results = DTC.predict(np.array(dfBatch.select_dtypes(exclude=['object']).iloc[:, :-1].fillna(0)))
    dfBatch.reset_index()

    index_score_good = []
    index_score_bad = []
    for i in range(len(results)):
        if results[i] != 1:
            index_score_bad.append(dfBatch.iloc[i]['imdb_id'])
        if results[i] == 1:
            index_score_good.append(dfBatch.iloc[i]['imdb_id'])

    print(len(index_score_good), " - ", len(index_score_bad))

    if len(index_score_good) > 1:
        next_choice = index_score_good[random.randint(0, len(index_score_good)-1)]
        # print(next_choice)
        UI.add_movie(next_choice)
    else:
        choose_new()

    return 0


# from kaggle project on this database
# https://www.kaggle.com/rounakbanik/movie-recommender-systems

def cosSim():
    global dfTitles
    links_small = pd.read_csv('data/links_small.csv')
    links_small = links_small[links_small['tmdbId'].notnull()]['tmdbId'].astype('int')
    dfTitles['id'] = dfTitles['id'].astype('int')
    dfTitles = dfTitles[dfTitles['id'].isin(links_small)]
    dfTitles['titleOverview'] = dfTitles['Title'] + dfTitles['overview']
    tf = TfidfVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0, stop_words='english')
    tfidf_matrix = tf.fit_transform(dfTitles['titleOverview'])
    print(tfidf_matrix.shape)
    return linear_kernel(tfidf_matrix, tfidf_matrix)

cosine_sim = cosSim()

def get_recommendations(title):
    global cosine_sim
    titles = dfTitles['Title']
    indices = pd.Series(dfTitles.index, index=dfTitles['Title'])

    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:31]
    movie_indices = [i[0] for i in sim_scores]
    return titles.iloc[movie_indices]


if __name__ == '__main__':
    main()
