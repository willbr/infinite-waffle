from tkinter import *
from tkinter.ttk import *
from math import sqrt
from functools import partial
import tkinter.font as tkfont

root = Tk()
root.geometry('800x600')
root.title('Infinite Waffle')

background_colour = '#222'
selected_cell_colour = 'green'
unselected_cell_colour = 'cyan'

toolbox_font_spec = tkfont.Font(family="Georgia", size=20)

cell_font_spec = tkfont.Font(family="Georgia", size=20)
font_metrics = cell_font_spec.metrics()

zoom_level = 5
zoom_scales = [
    0.1, 0.25, 0.333, 0.5, 0.667,
    1,
    1.5, 2, 3, 4, 5, 6, 7, 8,
]


colours = {
    'Black': '#333',
    'Dark-Gray': '#5f574f',
    'Light-Grey': '#c2c3c7',
    'White': '#eee',
    'Yellow': '#ffd817',
    'Orange': '#ff4f00',
    'Red': '#e33',
    'Green': '#8BEF88',
    'Cyan': '#A8FDE8',
    'Blue': '#88f',
    'Purple': '#A349A4',
}



frame = Frame(root)
frame.pack(fill=BOTH, expand=YES, padx=0, pady=0)

hscrollbar = Scrollbar(frame, orient=HORIZONTAL)
hscrollbar.pack(side=BOTTOM, fill=X)

vscrollbar = Scrollbar(frame, orient=VERTICAL)
vscrollbar.pack(side=RIGHT, fill=Y)

canvas = Canvas(frame, bd=0, bg=background_colour)
canvas.pack(side=LEFT, fill=BOTH, expand=YES)

toolbox_style = Style()
toolbox_style.configure('Custom.TFrame', background='#888')

toolbox_label_style = Style()
toolbox_label_style.configure('Custom.TLabel', background='#888')

toolbox = Frame(root, style='Custom.TFrame')

brush_label = Label(toolbox, text=f'N', font=toolbox_font_spec, style='Custom.TLabel')
brush_label.pack(side=TOP, padx=10, pady=10)

tool_label = Label(toolbox, text=f'tool', font=toolbox_font_spec, style='Custom.TLabel')
tool_label.pack(side=TOP, padx=10, pady=10)

layer_label = Label(toolbox, text=f'layer', font=toolbox_font_spec, style='Custom.TLabel')
layer_label.pack(side=TOP, padx=10, pady=10)

zoom_label = Label(toolbox, text=f' 100.00%', font=toolbox_font_spec, style='Custom.TLabel')
zoom_label.pack(side=TOP, padx=10, pady=10)


hscrollbar.config(command=canvas.xview)
vscrollbar.config(command=canvas.yview)

brush_size = None
brush_size_on_canvas = None
brush_color = '#8B88EF'

current_tool = None

current_cell = None


undo_stack = []
redo_stack = []

layer = {
        'outline': {'visible': True},
        'colour': {'visible': True},
        'sketch': {'visible': True},
        'background': {'visible': True},
        }

def set_brush_size(new_size):
    global brush_size
    global brush_size_on_canvas
    brush_size = int(min(max(2, new_size), 200))
    brush_label.configure(text=f'{brush_size:3d}')
    brush_size_on_canvas = int(max(2, brush_size * zoom_scales[zoom_level]))
    brush_size_on_canvas -= brush_size_on_canvas % 2 # bugfix; removes shimmering artifacts
    #print(f'{brush_size_on_canvas=}')


def get_visible_ids(tag_name=None, ignore_tags=None):
    ignore_list = []
    #ignore_list.extend(canvas.find_withtag('colours'))
    #ignore_list.extend(canvas.find_withtag('info'))

    #visible_ids = set(canvas.find_all()) - set(ignore_list)
    all_items = canvas.find_all() if tag_name is None else canvas.find_withtag(tag_name)
    visible_ids = {item for item in all_items if canvas.itemcget(item, 'state') != 'hidden'} - set(ignore_list)
    return visible_ids


def get_live_ids(tag_name=None):
    all_items = canvas.find_all() if tag_name is None else canvas.find_withtag(tag_name)
    deleted_ids = canvas.find_withtag('deleted')
    live_layer_ids = tuple(set(all_items) - set(deleted_ids))
    return live_layer_ids


def sort_objects_by_layer():
    for layer_name in ['background', 'sketch', 'colour', 'outline']:
        canvas.tag_raise(layer_name)


def on_canvas_resize(event=None):
    #print('resize')
    bbox = canvas.bbox('all')
    #print(f'{bbox=}')
    window_width, window_height = canvas.winfo_width(), canvas.winfo_height()

    if bbox is None:
        x1 = -window_width
        y1 = -window_height
        x2 = window_width * 2
        y2 = window_height * 2
    else:
        #print(bbox)
        x1 = bbox[0] - bbox[2] - window_width
        y1 = bbox[1] - bbox[3] - window_height
        x2 = bbox[2] + bbox[2] + window_width
        y2 = bbox[3] + bbox[3] + window_width

    scroll_region = canvas.cget("scrollregion")
    if scroll_region == '':
        #print('not set')
        pass
    else:
        old_x1, old_y1, old_x2, old_y2 = (float(n) for n in scroll_region.split(' '))
        #print(('old', old_x1, old_y1, old_x2, old_y2))
        x1 = min(x1, old_x1)
        y1 = min(y1, old_y1)
        x2 = max(x2, old_x2)
        y2 = max(y2, old_y2)

    #print(('new', x1, y1, x2, y2))

    canvas.config(scrollregion=(x1, y1, x2, y2))

    canvas.config(
        xscrollcommand=hscrollbar.set,
        yscrollcommand=vscrollbar.set)


def on_windows_zoom(event):
    ctrl_is_down = event.state == 4
    if ctrl_is_down == False:
        return
    x = canvas.canvasx(event.x)
    y = canvas.canvasy(event.y)

    if event.delta > 0:
        zoom(x, y, 1)
    else:
        zoom(x, y, -1)

    #update_brush_cursor(event)


def zoom(x, y, step):
    global zoom_level

    # if zoom_level > 9:
    #    return

    prev_level = zoom_level
    next_level = min(max(0, zoom_level + step), len(zoom_scales)-1)

    if prev_level == next_level:
        return


    prev_zoom_scale = zoom_scales[prev_level]
    next_zoom_scale = zoom_scales[next_level]
    #print(f'{prev_zoom_scale=}, {next_zoom_scale=}')

    zoom_step_scale = next_zoom_scale / prev_zoom_scale
    #print(f'{zoom_step_scale=}')

    zoom_level += step
    #print(f'{zoom_level=}')

    zoom_label.configure(text=f'{next_zoom_scale*100:4.2f}%')

    #canvas.scale('all', x,y, zoom_step_scale, zoom_step_scale)
    canvas.scale('!colours', x,y, zoom_step_scale, zoom_step_scale)

    all_items = canvas.find_all()

    new_size = int(20 * next_zoom_scale)

    cell_font_spec.configure(size=new_size)

    for item_id in all_items:
        item_type = canvas.type(item_id)
        match item_type:
            case 'line':
                current_width = float(canvas.itemcget(item_id, 'width'))
                new_width = current_width * zoom_step_scale
                canvas.itemconfig(item_id, width=new_width)
            case 'text':
                #font = canvas.itemcget(item_id, 'font')
                #print(type(font))
                pass
            case 'rectangle':
                pass # already zoomed by canvas.scale
            case other:
                #print(f'failed to zoom {item_type=}')
                pass

    #set_brush_size(brush_size)

    zoom_scroll_region(zoom_step_scale)


def zoom_scroll_region(zoom_step_scale):
    scroll_region = canvas.cget("scrollregion")
    if scroll_region == '':
        print('no scroll region')
        return

    old_x1, old_y1, old_x2, old_y2 = (float(n) for n in scroll_region.split(' '))

    x1 = old_x1 * zoom_step_scale
    y1 = old_y1 * zoom_step_scale
    x2 = old_x2 * zoom_step_scale
    y2 = old_y2 * zoom_step_scale

    #print(('new', x1, y1, x2, y2))

    canvas.config(scrollregion=(x1, y1, x2, y2))

    on_canvas_resize()




def echo_event(event):
    print(event)
    return "break"


def update_brush_cursor(event):
    #print(event)
    r = brush_size_on_canvas / 2
    x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
    x0, y0 = x - r, y - r
    x1, y1 = x + r, y + r


def motion(event):
    #update_brush_cursor(event)

    #print(f'{current_tool=}')
    tool_spec = tools.get(current_tool, None)
    if tool_spec is None:
        return

    tool_fn = tools[current_tool].get('motion', None)
    if tool_fn is None:
        return

    tool_fn(event)


#canvas.config(cursor='crosshair')
#canvas.config(cursor='none')

canvas.bind('<Configure>', on_canvas_resize)

#canvas.bind('<Motion>', motion)

#canvas.bind('<ButtonPress-2>', echo_event)
#canvas.bind('<B2-Motion>', echo_event)
#canvas.bind('<ButtonRelease-2>', echo_event)

def start_panning(event):
    x, y = event.x, event.y
    canvas.scan_mark(x, y)

def motion_panning(event):
    x, y = event.x, event.y
    canvas.scan_dragto(x, y, gain=1)

canvas.bind('<ButtonPress-3>', start_panning)
canvas.bind('<B3-Motion>', motion_panning)


initial_brush_size = 0
brush_size_last_x = 0
brush_size_last_y = 0

def save_cursor_position(event):
    global brush_size_last_x
    global brush_size_last_y
    brush_size_last_x = event.x
    brush_size_last_y = event.y


def restore_cursor_position(event):
    #print('warping cursor')
    canvas.event_generate(
            '<Motion>',
            warp=True,
            x=brush_size_last_x,
            y=brush_size_last_y)


def on_alt_b3_press(event):
    global initial_brush_size 
    initial_brush_size = brush_size

    save_cursor_position(event)


def on_alt_b3_motion(event):
    delta_x = (event.x - brush_size_last_x) / 4
    #delta_y = (event.y - brush_size_last_y) / 4

    set_brush_size(initial_brush_size + delta_x)

    event.x = brush_size_last_x
    event.y = brush_size_last_y

    #update_brush_cursor(event)
    return 'break'



def on_alt_b3_release(event):
    print(f'{brush_size=}')
    restore_cursor_position(event)


#canvas.bind('<Alt-ButtonPress-3>', on_alt_b3_press, add='+')
#canvas.bind('<Alt-B3-Motion>', on_alt_b3_motion, add='+')
#canvas.bind('<Alt-B3-ButtonRelease>', on_alt_b3_release, add='+')

root.bind('<Alt_L>', lambda x: "break") # ignore key press


def toggle_toolbox(event):
    if toolbox.winfo_ismapped():
        toolbox.place_forget()
    else:
        toolbox.place(x=10, y=10)


initial_zoom = 0

def start_zooming(event):
    global initial_zoom
    initial_zoom = zoom_level
    #print(f'{initial_zoom=}')
    pass


def motion_zooming(event):
    delta_x = (event.x - brush_size_last_x) // 4
    #print(f'{delta_x=}')

    delta_steps = delta_x // 20
    #print(f'{delta_steps=}')

    target_level = initial_zoom + delta_steps
    #print(f'{target_level=} = {initial_zoom=} + {delta_steps=}')

    x = canvas.canvasx(brush_size_last_x)
    y = canvas.canvasy(brush_size_last_y)


    if target_level > zoom_level:
        zoom(x, y, +1)
    elif target_level == zoom_level:
        pass
    else:
        zoom(x, y, -1)
        pass

    return 'break'




def apply_change(action, change_type):
    match action:
        case 'clear_layer', layer_name, object_ids:
            new_state = 'normal' if change_type == 'undo' else 'hidden'
            #print(f'{change_type=} clear layer {layer_name=} {object_ids}')

        case 'toggle_layer_visible', layer_name:
            toggle_layer_visible(layer_name)
            object_ids = ()

        case _, object_ids:
            new_state = 'hidden' if change_type == 'undo' else 'normal'
            pass

    for object_id in object_ids:
        #print(f'apply {object_id=} {new_state=}')
        if new_state == 'hidden':
            canvas.addtag_withtag('deleted', object_id)
        else:
            canvas.dtag(object_id, 'deleted')
        canvas.itemconfig(object_id, state=new_state)


def start_undoing(event):
    if not undo_stack:
        print('nothing to undo')
        return

    action = undo_stack.pop()
    apply_change(action, 'undo')
    redo_stack.append(action)


def start_redoing(event):
    if not redo_stack:
        print('nothing to redo')
        return

    action = redo_stack.pop()
    apply_change(action, 'redo')
    undo_stack.append(action)



def zoom_to_level(target_level):
    def fn(event):
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        delta = target_level - zoom_level
        zoom(x, y, delta)
        return
    return fn

#select_brush_tool()

def on_key_press(event):
    global current_line
    global current_col
    global current_line_width
    #print(event)

    char = event.char
    keysym = event.keysym

    if char == '\b':
        line = current_lines[current_line]
        if line == '':
            print('delete line')
        else:
            current_col -= 1
            current_lines[current_line] = current_lines[current_line][:-1]
    elif char == '\r':
        current_lines.insert(current_line+1, '')
        current_line += 1
        current_col = 0
    else:
        current_col += 1
        current_lines[current_line] += char

    text = '\n'.join(current_lines)

    canvas.itemconfig(current_cell, text=text)

    update_text_cursor()


current_lines = ['']
current_line = 0
current_col  = 0
current_line_width = 0


cursor_colour = 'white'
cursor_width = 4
cursor_height = font_metrics["ascent"] + 2

cursor_id = None

def update_text_cursor():
    line = current_lines[current_line]

    line_subset = line[:current_col]

    padding = int(max(2, 2 * zoom_scales[zoom_level]))
    x_offset = cell_font_spec.measure(line_subset) + padding
    font_metrics = cell_font_spec.metrics()
    #print(font_metrics)
    linespace = font_metrics['linespace']
    y_offset = linespace * current_line
    cell_x, cell_y, *_= canvas.coords(current_cell)

    y = cell_y + y_offset
    x = cell_x + x_offset

    set_cursor(x, y)


def create_cursor(x, y):
    global cursor_id
    cursor_id = canvas.create_rectangle(
            x-(cursor_width//2),
            y,
            x+(cursor_width//2),
            y+cursor_height,
            fill=cursor_colour)


def set_cursor(x=0, y=0):
    old_x, old_y, *_ = canvas.coords(cursor_id)
    delta_x = x - old_x
    delta_y = y - old_y
    canvas.move(cursor_id, delta_x, delta_y)


def flash_cursor():
    global cursor_colour
    cursor_colour = "red" if cursor_colour == 'white' else "white"
    canvas.itemconfig(cursor_id, fill=cursor_colour)
    canvas.after(1000, flash_cursor)


def click_cell(event, cell_id):
    global current_cell
    global current_lines
    global current_line
    global current_col

    if cell_id == current_cell:
        return

    canvas.itemconfig(current_cell, fill=unselected_cell_colour)

    current_cell = cell_id
    canvas.itemconfig(current_cell, fill=selected_cell_colour)

    text = canvas.itemcget(current_cell, 'text')
    current_lines = text.split('\n')
    current_line = 0
    current_col  = 0

    update_text_cursor()

    return 'break'


def create_cell(x, y):
    global current_cell
    global current_lines
    global current_line
    global current_col
    global current_line_width

    y -= font_metrics['ascent'] // 2

    set_cursor(x, y)

    canvas.itemconfig(current_cell, fill=unselected_cell_colour)

    current_cell = canvas.create_text(
            x, y,
            text='',
            font=cell_font_spec,
            fill=colours['Cyan'],
            anchor='nw')

    current_lines = ['']
    current_line = 0
    current_col  = 0

    current_line_width = 0

    canvas.tag_bind(current_cell, '<Button-1>', partial(click_cell, cell_id=current_cell))


def create_cell_here(event):
    x = canvas.canvasx(event.x)
    y = canvas.canvasy(event.y)
    create_cell(x, y)


create_cursor(100, 50)
flash_cursor()
create_cell(100, 50)

root.bind('<KeyPress-Tab>', toggle_toolbox)

#root.bind('<KeyPress-u>', start_undoing)
#root.bind('<KeyPress-y>', start_redoing)

canvas.bind('<MouseWheel>', on_windows_zoom)

canvas.bind('<Double-Button-1>', create_cell_here)
#canvas.bind('<Button-1>', lambda e: print(e))
#canvas.bind('<Button-2>', lambda e: print(e))
#canvas.bind('<Button-3>', lambda e: print(e))

root.bind('<KeyPress>', on_key_press)

#root.wm_state('zoomed')
root.mainloop()

