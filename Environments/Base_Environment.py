from abc import ABC, abstractmethod

class Base_Environment(ABC):
            
    @abstractmethod
    def conduct_action(self):
        pass
    
    @abstractmethod
    def get_action_size(self):
        pass
    
    @abstractmethod
    def get_state_size(self):
        pass    
    
    @abstractmethod
    def get_state(self):
        pass
    
    @abstractmethod
    def get_next_state(self):
        pass    
    
    @abstractmethod
    def get_reward(self):
        pass    
    
    @abstractmethod
    def get_done(self):
        pass     
    
    @abstractmethod
    def get_reward(self):
        pass      
    
    @abstractmethod
    def reset_environment(self):
        pass
    