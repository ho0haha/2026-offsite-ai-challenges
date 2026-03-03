"""
Broken async code with a race condition.
Two coroutines append to a shared list without synchronization.
Fix this so all items are correctly collected without loss or duplication.
"""

import asyncio


shared_results = []


async def producer_a(items):
    """Append items from list A to shared_results."""
    for item in items:
        temp = list(shared_results)
        await asyncio.sleep(0)  # simulate async work / yield control
        temp.append(item)
        shared_results.clear()
        shared_results.extend(temp)


async def producer_b(items):
    """Append items from list B to shared_results."""
    for item in items:
        temp = list(shared_results)
        await asyncio.sleep(0)  # simulate async work / yield control
        temp.append(item)
        shared_results.clear()
        shared_results.extend(temp)


async def collect(items_a, items_b):
    """Run both producers concurrently and return the shared results."""
    shared_results.clear()
    await asyncio.gather(
        producer_a(items_a),
        producer_b(items_b),
    )
    return list(shared_results)
