import math

def calculate_average(numbers):
    
    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


class Processor:
    def process(self, data):
        
        for item in data:
            if item is None:
                continue
            print(item)