def get_coordinates(points, list=None):
    if list is None:
        list = []

    for x in points:
        list.append((int(x['x']), int(x['y'])))
    
    return list

# Given data
points = [
    {'x': 204, 'y': 318.3333282470703},
    {'x': 205, 'y': 365.3333282470703},
    {'x': 67, 'y': 426.3333282470703}
]



result_list = get_coordinates(points)
print(result_list)