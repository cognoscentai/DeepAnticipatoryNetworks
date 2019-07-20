import matplotlib.pyplot as plt
import numpy as np
import argparse


use_label = True

num_runs = 25

agent_type_arr = ['dan', 'dan_coverage', 'coverage', 'randomAction']
agent_best_setting = [0, 0, 0, 0]

ma_window = 100

yloc_arr = list(range(0, 13, 2))


def movingaverage(values, window):
    weights = np.repeat(1.0, window) / window
    sma = np.convolve(values, weights, 'valid')
    return sma


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--result_dir', type=str)
    args = parser.parse_args()

    dir_name = args.result_dir

    # Train Result
    plt.figure(figsize=(12, 6))

    if use_label:
        plt.xlabel("Training Episodes")
        plt.ylabel("Return")

    handle_arr = []
    label_arr = []

    for idx, agent_type in enumerate(agent_type_arr):

        trainX_arr = []
        trainY_arr = []

        best_idx = agent_best_setting[idx]

        for i in range(num_runs):

            # Train results
            trainX_filename = '{}/{}_setting_{}_run_{}_train_return_per_episodeX.txt'.format(dir_name, agent_type, best_idx, i)
            trainX = np.loadtxt(trainX_filename, delimiter=',')
            trainX = movingaverage(trainX, ma_window)
            trainX_arr.append(trainX)

            trainY_filename = '{}/{}_setting_{}_run_{}_train_return_per_episodeY.txt'.format(dir_name, agent_type,best_idx, i)
            trainY = np.loadtxt(trainY_filename, delimiter=',')
            trainY = movingaverage(trainY, ma_window)
            trainY_arr.append(trainY)


        trainX_mean = np.mean(trainX_arr, axis=0)
        trainX_stderr = np.std(trainX_arr, axis=0) / np.sqrt(num_runs)

        trainY_mean = np.mean(trainY_arr, axis=0)
        trainY_stderr = np.std(trainY_arr, axis=0) / np.sqrt(num_runs)

        x_range = list(range(len(trainX_mean)))

        handle1, = plt.plot(x_range, trainX_mean)
        plt.fill_between(x_range, trainX_mean - trainX_stderr, trainX_mean + trainX_stderr, alpha=0.2)
        handle_arr.append(handle1)
        if use_label:
            label_arr.append(agent_type + 'X' + 'setting: ' + str(best_idx))

        handle2, = plt.plot(x_range, trainY_mean)
        plt.fill_between(x_range, trainY_mean - trainY_stderr, trainY_mean + trainY_stderr, alpha=0.2)
        handle_arr.append(handle2)
        if use_label:
            label_arr.append(agent_type + 'Y' + 'setting: ' + str(best_idx))

    plt.legend(handle_arr, label_arr)

    if use_label:
        plt.title('Return per Episode (Training): {} Runs, {} Window'.format(num_runs, ma_window))

    # 5000 -> 4901
    # [100, ..., 5000]
    xloc_arr = [0, 400, 900, 1400, 1900, 2400, 2900, 3400, 3900, 4400, 4900]
    xval_arr = [100, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000]

    if use_label:
        plt.xticks(xloc_arr, xval_arr)
        plt.yticks(yloc_arr, yloc_arr)
    else:
        plt.xticks(xloc_arr, [])
        plt.yticks(yloc_arr, [])

    plt.show()
    plt.close()

    # Test Result
    plt.figure(figsize=(12, 6))

    if use_label:
        plt.xlabel("Episodes")
        plt.ylabel("Return")

    handle_arr = []
    label_arr = []

    for idx, agent_type in enumerate(agent_type_arr):

        testX_arr = []
        testY_arr = []

        best_idx = agent_best_setting[idx]

        for i in range(num_runs):
            # Train results
            testX_filename = '{}/{}_setting_{}_run_{}_test_mean_return_per_episode.txt'.format(dir_name, agent_type, best_idx,i)
            # testY_filename = '{}/{}_setting_{}_run_{}_test_mean_return_per_episodeY.txt'.format(dir_name, agent_type, best_idx,i)

            testX = np.loadtxt(testX_filename, delimiter=',')
            # testY = np.loadtxt(testY_filename, delimiter=',')

            testX_arr.append(testX)
            # testY_arr.append(testY)

        testX_mean = np.mean(testX_arr, axis=0)
        # testY_mean = np.mean(testY_arr, axis=0)
        testX_stderr = np.std(testX_arr, axis=0) / np.sqrt(num_runs)
        # testY_stderr = np.std(testY_arr, axis=0) / np.sqrt(num_runs)

        x_range = list(range(len(testX_mean)))

        handle1, = plt.plot(x_range, testX_mean)
        # handle2, = plt.plot(x_range, testY_mean)
        plt.fill_between(x_range, testX_mean - testX_stderr, testX_mean + testX_stderr, alpha=0.2)
        # plt.fill_between(x_range, testY_mean - testY_stderr, testY_mean + testY_stderr, alpha=0.2)

        handle_arr.append(handle1)
        # handle_arr.append(handle2)

        if use_label:
            label_arr.append(agent_type + ', setting: ' + str(best_idx))

    plt.legend(handle_arr, label_arr)
    if use_label:
        plt.title('Return per Episode (Testing): {} Runs, {} Window'.format(num_runs, ma_window))

    xloc_arr = list(range(0, 12, 1))
    xval_arr = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000]

    if use_label:
        plt.xticks(xloc_arr, xval_arr)
        plt.yticks(yloc_arr, yloc_arr)
    else:
        plt.xticks(xloc_arr, [])
        plt.yticks(yloc_arr, [])

    plt.show()
    plt.close()

if __name__ == '__main__':
    main()
