import numpy as np
import tensorflow as tf
from utils.utils import ExperienceBuffer
from agents.networks.qnet import Qnetwork
from agents.networks.mnet import Mnetwork


class DAN:
    def __init__(self, config, xory):

        self.agent_type = config.agent_type  # 'dan', 'random_policy', 'coverage', 'dan_coverage'

        # 'x' or 'y'
        self.xory = xory

        # self.rng = np.random.RandomState(config.random_seed)
        self.h_size = config.h_size  # The size of the final recurrent layer before splitting it into Advantage and Value streams.
        self.batch_size = config.batch_size
        self.trace_length = config.trace_length

        # self.pre_train_steps = config.pre_train_steps
        self.update_reward = config.update_reward
        self.epsilon = config.epsilon
        self.gamma = config.gamma
        self.tau = config.tau
        self.nActions = config.nActions
        self.nStates = config.nStates

        self.use_terminal_reward_setting = config.use_terminal_reward_setting

        self.replay_buffer = ExperienceBuffer(config.buffer_size, config.random_seed)

        self.graph = tf.Graph()

        self.qnet_current_rnn_state = None
        self.mnet_current_rnn_state = None

        # Only for test
        self.test_qnet_current_rnn_state = None
        self.test_mnet_current_rnn_state = None

        # create Network
        with self.graph.as_default():
            tf.set_random_seed(config.random_seed)
            self.sess = tf.Session()
            self.qnet = Qnetwork(self.sess, config)
            self.mnet = Mnetwork(self.sess, config)

            self.sess.run(tf.global_variables_initializer())
            self.qnet.init_target_network()

    def start(self, raw_obs, is_pretraining, is_train):
        # obs: (1,31) np.zero observation
        obs = self.select_xy(raw_obs)

        # reset qnet, mnet current rnn state
        self.qnet_current_rnn_state = (np.zeros([1, self.h_size]), np.zeros([1, self.h_size]))
        self.mnet_current_rnn_state = (np.zeros([1, self.h_size]), np.zeros([1, self.h_size]))

        greedy_action, rnn_state = self.qnet.get_greedy_action(obs, self.qnet_current_rnn_state)
        self.qnet_current_rnn_state = rnn_state

        if is_train:

            if self.agent_type == 'dan' \
                    or self.agent_type == 'coverage' \
                    or self.agent_type == 'dan_coverage':
                # if is_pretraining or self.rng.rand() < self.epsilon:
                if is_pretraining or np.random.rand() < self.epsilon:
                    # random action
                    # action = self.rng.randint(0, self.nActions)
                    action = np.random.randint(0, self.nActions)
                else:
                    action = greedy_action[0]

            elif self.agent_type == 'random_policy':
                # action = self.rng.randint(0, self.nActions)
                action = np.random.randint(0, self.nActions)

            else:
                raise ValueError("Invalid self.agent_type")

        else:
            raise ValueError("It isn't used during evaluation")

        return action

    def step(self, raw_obs, is_pretraining, is_train):
        # obs: (1, 31)
        obs = self.select_xy(raw_obs)

        greedy_action, rnn_state = self.qnet.get_greedy_action(obs, self.qnet_current_rnn_state)
        self.qnet_current_rnn_state = rnn_state

        if is_train:

            if self.agent_type == 'dan' \
                    or self.agent_type == 'coverage'\
                    or self.agent_type == 'dan_coverage':
                # if is_pretraining or self.rng.rand() < self.epsilon:
                if is_pretraining or np.random.rand() < self.epsilon:
                    # random action
                    # action = self.rng.randint(0, self.nActions)
                    action = np.random.randint(0, self.nActions)
                else:
                    # greedy action
                    action = greedy_action[0]

            elif self.agent_type == 'random_policy':
                # action = self.rng.randint(0, self.nActions)
                action = np.random.randint(0, self.nActions)

            else:
                raise ValueError("Invalid self.agent_type")
        else:
            raise ValueError("It isn't used during evaluation")

        return action

    def predict(self, raw_obs, raw_state, is_terminal):
        # print("raw_obs", raw_obs)
        obs = self.select_xy(raw_obs)
        state = self.select_xy(raw_state)

        if self.use_terminal_reward_setting and not is_terminal:
            reward = 0
        else:
            prediction, rnn_state = self.mnet.get_prediction(obs, self.mnet_current_rnn_state)
            self.mnet_current_rnn_state = rnn_state

            if self.agent_type == 'dan' or self.agent_type == 'random_policy':
                reward = self.get_prediction_reward(prediction[0], state)

            elif self.agent_type == 'coverage':
                reward = self.get_coverage_reward(obs)

            elif self.agent_type == 'dan_coverage':
                reward = self.get_prediction_reward(prediction[0], state)
                if not reward:
                    reward = self.get_coverage_reward(obs) * 0.2  # 0.2 or 0.0

            else:
                raise ValueError("Invalid self.agent_type")

        return reward

    def get_prediction_reward(self, pred_s, true_s):
        # true_s : 0~50
        # pred_s : an array of size (51,) containing prediction values with highest being most probable
        if np.argmax(pred_s) == true_s:
            reward = 1.0
        else:
            reward = 0.0

        return reward

    def get_coverage_reward(self, obs):
        # obs is one-hot-vector
        obs_val = np.where(obs[0] == 1)[0][0]

        if obs_val < self.nStates - 1:
            reward = 1.0
        else:
            reward = 0.0
        return reward

    def update(self):

        # Get a random batch of experiences.
        train_batch = self.replay_buffer.sample(self.batch_size, self.trace_length)

        # Select x or y obs/next_obs, true_state
        for i in range(len(train_batch)):

            if self.update_reward:
                # reward
                train_batch[i][2] = self.predict(train_batch[i][3], train_batch[i][5])

            # obs
            train_batch[i][0] = self.select_xy(train_batch[i][0])
            # next_obs
            train_batch[i][3] = self.select_xy(train_batch[i][3])
            train_batch[i][5] = self.select_xy(train_batch[i][5])

        # perform update
        if self.agent_type == 'dan' or self.agent_type == 'coverage' or self.agent_type == 'dan_coverage':

            self.qnet.update(train_batch, self.trace_length, self.batch_size)
            self.qnet.update_target_network()

        if self.agent_type == 'dan' or self.agent_type == 'random_policy' or self.agent_type == 'dan_coverage':
            self.mnet.update(train_batch, self.trace_length, self.batch_size)

        return

    def select_xy(self, xy_tuple):
        if self.xory == 'x':
            return xy_tuple[0]
        elif self.xory == 'y':
            return xy_tuple[1]
        else:
            return ValueError("Wrong value in self.xory")

    def start_getQ(self, raw_obs, rnn_state, is_train):
        assert(is_train is False)
        # obs: (1,31) np.zero observation
        obs = self.select_xy(raw_obs)

        Qval, new_rnn_state = self.qnet.get_Qval(obs, rnn_state)

        return Qval, new_rnn_state

    def step_getQ(self, raw_obs, rnn_state, is_train):
        assert (is_train is False)
        # obs: (1, 31)
        obs = self.select_xy(raw_obs)

        Qval, new_rnn_state = self.qnet.get_Qval(obs, rnn_state)

        return Qval, new_rnn_state

    def predict_test(self, raw_obs, raw_state, rnn_state, _):
        obs = self.select_xy(raw_obs)
        state = self.select_xy(raw_state)

        prediction, new_rnn_state = self.mnet.get_prediction(obs, rnn_state)

        if self.agent_type == 'dan' or self.agent_type == 'random_policy' or self.agent_type == 'dan_coverage':
            reward = self.get_prediction_reward(prediction[0], state)

        elif self.agent_type == 'coverage':
            reward = self.get_coverage_reward(obs)

        else:
            raise ValueError("Invalid self.agent_type")

        return np.argmax(prediction[0]), reward, new_rnn_state


    def print_variables(self, variable_list):
        variable_names = [v.name for v in variable_list]
        values = self.sess.run(variable_names)

        count=0
        for k, v in zip(variable_names, values):
            count += 1

            if count == 3:
                print("Variable: ", k)
                print("Shape: ", v.shape)
                print(v)
                return

    def save_network(self, save_dir, xory):
        self.qnet.save_network(save_dir, xory)
        self.mnet.save_network(save_dir, xory)

    def restore_network(self, load_dir, xory):
        self.qnet.restore_network(load_dir, xory)
        self.mnet.restore_network(load_dir, xory)
