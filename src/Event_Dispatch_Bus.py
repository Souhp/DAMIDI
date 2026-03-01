
import asyncio



_callbacks = {}



##CALLBACK IS A FUNCTION
async def register_event(event_name, callback):
    if event_name not in _callbacks:
    
        _callbacks[event_name] = []
    print("Storing")

        ##OVERIDES BY DEFAULT
    _callbacks[event_name].append(callback)

async def trigger_event(event_name, *args, **kwargs):
    print("Triggering")

    for cb in _callbacks.get(event_name, []):
        


        await cb(*args, **kwargs)





