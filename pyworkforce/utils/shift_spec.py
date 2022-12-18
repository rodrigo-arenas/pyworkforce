from collections import deque

HMin = 60
DayH = 24

def upscale_and_shift(a, time_scale, shift_right_pos):
  scaled = [val for val in a for _ in range(time_scale)]
  items = deque(scaled)
  items.rotate(shift_right_pos)
  return list(items)

def genereate_shifts_coverage(shift_hours, name, horizon_in_hours, start_hour, end_hour, step_mins):
  time_scale = int(HMin / step_mins)
  slots = time_scale * (end_hour - start_hour)
  res = {}
  for i in range(slots):
    s_name = f'{name}_{horizon_in_hours}_{start_hour + (i * step_mins // HMin)}_{i * step_mins % HMin}'
    res[s_name] = upscale_and_shift(shift_hours, time_scale, i) 
  return res

def decode_shift_spec(a):
    name, duration, start, end, step = a.split('_')
    class Object(object):
        pass

    a = Object()
    a.name = name
    a.duration = int(duration)
    a.start = int(start)
    a.end = int(end)
    a.step = int(step)
    return a

def get_shift_coverage(shifts):
    shift_cover = {}
    for i in shifts:
        a = decode_shift_spec(i)
        base_spec = [1 if (i < a.duration) else 0 for i in range(DayH)]
        base_spec = deque(base_spec)
        base_spec.rotate(a.start)
        base_spec = list(base_spec)
        res = genereate_shifts_coverage(base_spec, a.name, a.duration, a.start, a.end, a.step)
        shift_cover = shift_cover | res
    return shift_cover

def get_shift_colors(shift_names):
    shift_colors = {}
    for i in shift_names:
        if "Morning" in i:
            shift_colors[i] = '#34eb46'
        else:
            shift_colors[i] = '#0800ff'
    return shift_colors
