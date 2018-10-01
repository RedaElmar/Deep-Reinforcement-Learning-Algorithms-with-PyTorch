import torch
import numpy as np
from torch import optim
from torch.distributions import Categorical

from Base_Agent import Base_Agent
from NN_Creators import create_vanilla_NN
from Policy_Gradient_Agents.REINFORCE_Agent import REINFORCE_Agent


class PPO_Agent(Base_Agent):


    def __init__(self, environment, seed, hyperparameters, rolling_score_length, average_score_required,
                 agent_name):

        hyperparameters = hyperparameters["Policy_Gradient_Agents"]

        Base_Agent.__init__(self, environment=environment,
                                 seed=seed, hyperparameters=hyperparameters, rolling_score_length=rolling_score_length,
                                 average_score_required=average_score_required, agent_name=agent_name)

        self.policy_new = create_vanilla_NN(self.state_size, self.action_size, seed, self.hyperparameters).to(self.device)
        self.policy_old = create_vanilla_NN(self.state_size, self.action_size, seed, self.hyperparameters).to(self.device)


        self.optimizer = optim.Adam(self.policy_new.parameters(), lr=self.hyperparameters["learning_rate"])

    def reset_game(self):
        """Resets the game information so we are ready to play a new episode"""
        self.environment.reset_environment()
        self.state = self.environment.get_state()
        self.next_state = None
        self.action = None
        self.reward = None
        self.done = False
        self.total_episode_score_so_far = 0
        self.one_episode_rewards = []
        self.episode_policy_probability_ratios = []
        self.episode_step_number = 0

    def step(self):
        """Runs a step within a game including a learning step if required"""
        self.pick_and_conduct_action_and_save_ratio_of_policy_probabilities()

        self.update_next_state_reward_done_and_score()
        self.store_reward()

        if self.time_to_learn():
            self.learn()

        if self.time_to_equalise_policies():
            for old_param, new_param in zip(self.policy_old.parameters(), self.policy_new.parameters()):
                old_param.data.copy_(new_param.data)

        self.state = self.next_state #this is to set the state for the next iteration

    def pick_and_conduct_action_and_save_ratio_of_policy_probabilities(self):
        action, ratio_of_policy_probabilities = self.pick_action_and_get_ratio_of_policy_probabilities()
        self.store_ratio_of_policy_probabilities(ratio_of_policy_probabilities)
        self.store_action(action)
        self.conduct_action()

    def pick_action_and_get_ratio_of_policy_probabilities(self):

        # PyTorch only accepts mini-batches and not individual observations so we have to add
        # a "fake" dimension to our observation using unsqueeze
        state = torch.from_numpy(self.state).float().unsqueeze(0).to(self.device)

        new_policy_action_probabilities = self.policy_new.forward(state).cpu()
        old_policy_action_probabilities = self.policy_old.forward(state).cpu()
        ratio_of_policy_probabilities = new_policy_action_probabilities / old_policy_action_probabilities

        action_distribution = Categorical(new_policy_action_probabilities) # this creates a distribution to sample from
        action = action_distribution.sample()

        return action.item(), ratio_of_policy_probabilities

    def store_ratio_of_policy_probabilities(self, ratio_of_policy_probabilities):
        self.episode_policy_probability_ratios.append(ratio_of_policy_probabilities)

    def store_action(self, action):
        self.action = action

    def store_reward(self):
        self.one_episode_rewards.append(self.reward)

    def learn(self):
        future_episode_discounted_rewards = self.calculate_future_episode_discounted_rewards()

        # total_discounted_reward = self.calculate_episode_discounted_reward()
        policy_loss = self.calculate_policy_loss_on_episode(future_episode_discounted_rewards)
        self.optimizer.zero_grad()
        policy_loss.backward()
        self.optimizer.step()

    def calculate_future_episode_discounted_rewards(self):

        future_episode_discounted_rewards = []

        for ix in range(len(self.one_episode_rewards)):
            future_rewards = self.one_episode_rewards[ix:]
            discounted_future_reward = self.calculate_discounted_reward(future_rewards)
            future_episode_discounted_rewards.append(discounted_future_reward)

        return future_episode_discounted_rewards

    def calculate_discounted_reward(self, rewards):
        discounts = self.hyperparameters["discount_rate"] ** np.arange(len(rewards))
        total_discounted_reward = np.dot(discounts, rewards)
        return total_discounted_reward


    def calculate_policy_loss_on_episode(self, future_episode_discounted_rewards):
        policy_loss = []
        for probability_ratio, future_episode_discounted_reward in zip(self.episode_policy_probability_ratios, future_episode_discounted_rewards):
            policy_loss.append(probability_ratio * future_episode_discounted_reward)
        policy_loss = torch.cat(policy_loss).sum() # We need to add up the losses across the mini-batch to get 1 overall loss
        # policy_loss = Variable(policy_loss, requires_grad = True)
        return policy_loss

    def time_to_learn(self):
        return self.done

    def locally_save_policy(self):
        pass

    def save_experience(self):
        pass

    def time_to_equalise_policies(self):
        return self.episode_number % 3 == 0
