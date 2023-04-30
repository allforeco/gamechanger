import json
import logging
from pathlib import Path

from typing import *

log = logging.getLogger(__name__)


def dump_json_items(output:str, data:Dict, subdir:Optional[str]=None) -> None:
    # Make output directory
    output = Path(output)
    if not output.exists():
        output.mkdir()
        
    # Make subdirectory if required
    if subdir is not None:
        output = output.joinpath(subdir)
        if not output.exists():
            output.mkdir()
        
    # Dump item data to json
    for idx, (id_str, item) in enumerate(data.items()):
        with open(output.joinpath(f"{id_str}.json"), 'w') as fp:
            json.dump(item, fp)
            
    log.info(f"Dumped {len(data)} items to {output}.")