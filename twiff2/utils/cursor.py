import os
import math
import time
import json
import logging
import pathlib
import datetime

from typing import *
from abc import abstractmethod, ABC

log = logging.getLogger(__name__)
                   
class Cursor:
    def __init__(self, path:Optional[str]=None) -> None:
        self.path = pathlib.Path(path) if path is not None else None
        self.fresh_data = {'oldest_id':None, 'newest_id':None}
        self.data = self._load(self.path) 
        
        log.info('Loading... {}'.format(self.__repr__()))

    def __repr__(self):
        return repr('Cursor ({}): oldest_id={}, newest_id={}'.format(self.path, self.data['oldest_id'], self.data['newest_id']))
        
    def _load(self, path:str) -> Dict[str,int]:
        if path is not None:
            if path.exists():
                log.debug('Loading cursor from "{}"'.format(path))
                with open(path, 'r') as f: 
                    return json.load(f)
            else:
                log.debug('Provided cursor path "{}" does not exists... Defaulting to fresh cursor.'.format(path))
                return self.fresh_data
        else:
            log.debug('Loading fresh_cursor...'.format(path))
            return self.fresh_data            
    
    def _dump(self, path:str) -> None:
        log.info('Dumping cursor to "{}"'.format(path))
        with open(path, 'w') as f: json.dump(self.data, f)
    
    def _update(self, oldest_id:int, newest_id:int) -> None:
        # Update self.oldest_id if oldest_id is SMALLER (less recent than) currently stored
        if self.data['oldest_id'] is None:
            self.data['oldest_id'] = oldest_id
        else:
            self.data['oldest_id'] = oldest_id if oldest_id<self.data['oldest_id'] else self.data['oldest_id'] 
        
        # Updated self.newest_id if newest_id is LARGER (more recent than) currently stored
        if self.data['newest_id'] is None:
            self.data['newest_id'] = newest_id
        else:
            self.data['newest_id'] = newest_id if newest_id>self.data['newest_id'] else self.data['newest_id'] 
        log.info('Updated cursor: {}'.format(self.__repr__()))

    def _oldest_id(self) -> int:
        return self.data['oldest_id']
    
    def _newest_id(self) -> int:
        return self.data['newest_id']
    
    def _isnull(self) -> bool:
        return self._oldest_id()==None and self._newest_id()==None