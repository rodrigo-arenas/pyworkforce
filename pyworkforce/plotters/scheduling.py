from __future__ import absolute_import as _absolute_import
import operator
import numpy as np
#! /usr/bin/env python

def plot(solution, 
    shifts_spec, 
    step_min, 
    num_days, 
    shift_colors, 
    img_filename=None,
    resource_height=1.0,
    show_task_labels=True,
    color_prec_groups=False,
    hide_tasks=[],
    hide_resources=[],
    task_colors=dict(),
    fig_size=(15,5),
    vertical_text=False) :
    """
    Plot the given solved solution using matplotlib

    Args:
    solution:    solution to plot
    msg:         0 means no feedback (default) during computation, 1 means feedback
    """
    try :
        import matplotlib
        if img_filename is not None:
            matplotlib.use('Agg')
        import matplotlib.patches as patches, matplotlib.pyplot as plt
    except :
        raise Exception('ERROR: matplotlib is not installed')
    import random

    fig, ax = plt.subplots(1, 1, figsize=fig_size)

    plt.ylim(0, len(solution['resources_shifts']))

    ts = int(60.0 / step_min)

    plt.xlim(0, num_days * 24)

    cx = int(0)
    for i in solution['resources_shifts']:
        resources = i['resources']
        day = int(i['day'])
        shift_hours = shifts_spec[i['shift']]
        shift_name = i['shift']
        # shift_duration = int(shift_name.split('_')[1]) 
        shift_start_h = int(shift_name.split('_')[2])
        shift_start_m = int(shift_name.split('_')[3]) / 60.0

        if resources > 0:
            for idx, j in enumerate(shift_hours):
                if(j > 0):
                    # print(day, shift_start_h, resources, i['shift'])
                    # print(day, idx, ts, cx, day * 24 + idx / slot_min)
                    # exit()
                    # print(idx, j, cx)
                    ax.add_patch(
                        patches.Rectangle(
                        (day * 24 + idx / ts, cx),       # (x,y)
                        step_min / 60,   # width (1h)
                        resource_height,   # height
                        color = shift_colors[i['shift']], 
                        alpha=0.6
                        )
                    )

            nonzeropos = shift_hours.index(next(filter(lambda x: x!=0, shift_hours))) 
            if nonzeropos > 0:
                # ax.text(day * 24 + (shift_start_h + shift_start_m), cx + 0.5, str(resources), color='white')
                # print(shift_start_h, shift_start_m, ts)
                ax.text(day * 24 + (shift_start_h + shift_start_m - 2 / ts), cx + 0.5, str(resources), color='red')
        cx += 1
#   plt.yticks([ resource_height*x + resource_height/2.0 for x in range(len(R_ticks)) ],R_ticks[::-1])
#   plt.ylim(0,resource_sizes_count*resource_height)#resource_height*len(resources))
#   plt.xlim(0,max([ x_ for (I,R,x,x_) in solution if R in visible_resources ]))

    # [for i['resource'] in solution['resource_shifts']]
    # all_res = list(map(lambda x: {'id': x['id'], 'resource': x['resource']}, solution['resource_shifts']))

    # uniq_res = list({v['id']:v for v in all_res}.values())

    # plt.yticks([x + resource_height/2.0 for x in range(len(uniq_res))], [i['resource'] for i in uniq_res])

    # plt.xticks(np.arange(0, num_days * 24 + 1, 12))

    plt.title(f'Optimal Scheduling: {num_days} days ({num_days * 24} hours)')

    if img_filename is not None:
        fig.figsize=(1,1)
        plt.savefig(img_filename,dpi=200,bbox_inches='tight')
    else :
        plt.show()
