from typing import *

from abc import ABC, abstractmethod

class LikeCondition:
    def __init__(self) -> None:
        pass
    
    @abstractmethod
    def __call__(self) -> bool:
        pass
    

class T4FLikeCondition(LikeCondition):
    def __init__(self, kwarg1:Any) -> None:
        super(T4FLikeCondition, self).__init__()
        
    def __call__(self, tweet:Dict) -> bool:
        return True