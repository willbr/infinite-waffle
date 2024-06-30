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

SHIFT_MASK = 0x0001
CAPS_LOCK_MASK = 0x0002
CONTROL_MASK = 0x0004
ALT_MASK = 0x0008
NUM_LOCK_MASK = 0x0010
LEFT_ALT_MASK = 0x0020
LEFT_MOUSE_BUTTON_MASK = 0x0040
MIDDLE_MOUSE_BUTTON_MASK = 0x0080
RIGHT_MOUSE_BUTTON_MASK = 0x0100
COMMAND_MASK = 0x0200
ALT_GR_MASK = 0x0800
MOVEMENT_MASK = 0x40000


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

tool_label = Label(toolbox, text=f'tool', font=toolbox_font_spec, style='Custom.TLabel')
tool_label.pack(side=TOP, padx=10, pady=10)

layer_label = Label(toolbox, text=f'layer', font=toolbox_font_spec, style='Custom.TLabel')
layer_label.pack(side=TOP, padx=10, pady=10)

zoom_label = Label(toolbox, text=f' 100.00%', font=toolbox_font_spec, style='Custom.TLabel')
zoom_label.pack(side=TOP, padx=10, pady=10)


hscrollbar.config(command=canvas.xview)
vscrollbar.config(command=canvas.yview)

current_tool = None
current_cell = None

layer = {
        'outline': {'visible': True},
        'colour': {'visible': True},
        'sketch': {'visible': True},
        'background': {'visible': True},
        }

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


def on_canvas_resize(event=None):
    #print('resize')
    bbox = canvas.bbox('all')
    #print(f'{bbox=}')
    window_width, window_height = canvas.winfo_width(), canvas.winfo_height()

    if bbox is None:
        x1 = -window_width
        y1 = -window_height
        x2 = window_width * 1
        y2 = window_height * 1
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


#canvas.config(cursor='crosshair')
#canvas.config(cursor='none')
canvas.config(cursor="ibeam")

canvas.bind('<Configure>', on_canvas_resize)


def start_panning(event):
    x, y = event.x, event.y
    canvas.scan_mark(x, y)

def motion_panning(event):
    x, y = event.x, event.y
    canvas.scan_dragto(x, y, gain=1)

canvas.bind('<ButtonPress-3>', start_panning)
canvas.bind('<B3-Motion>', motion_panning)


last_x_cursor = 0
last_y_cursor = 0

def save_cursor_position(event):
    global last_x_cursor
    global last_y_cursor
    last_x_cursor = event.x
    last_y_cursor = event.y


def restore_cursor_position(event):
    #print('warping cursor')
    canvas.event_generate(
            '<Motion>',
            warp=True,
            x=last_x_cursor,
            y=last_y_cursor)


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
    delta_x = (event.x - last_x_cursor) // 4
    #print(f'{delta_x=}')

    delta_steps = delta_x // 20
    #print(f'{delta_steps=}')

    target_level = initial_zoom + delta_steps
    #print(f'{target_level=} = {initial_zoom=} + {delta_steps=}')

    x = canvas.canvasx(last_x_cursor)
    y = canvas.canvasy(last_y_cursor)


    if target_level > zoom_level:
        zoom(x, y, +1)
    elif target_level == zoom_level:
        pass
    else:
        zoom(x, y, -1)
        pass

    return 'break'


def zoom_to_level(target_level):
    def fn(event):
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        delta = target_level - zoom_level
        zoom(x, y, delta)
        return
    return fn


def select_range(from_line, from_col, to_line, to_col):
    global current_line
    global current_col
    global selection_line
    global selection_col

    current_line = from_line
    current_col  = max(0, from_col)
    selection_line = to_line
    selection_col  = max(0, to_col)


def delete_range(from_line, from_col, to_line, to_col):
    global current_lines

    #print((from_line, from_col, to_line, to_col))

    if to_line < from_line:
        from_line, from_col, to_line, to_col = to_line, to_col, from_line, from_col

    #print((from_line, from_col, to_line, to_col))

    top_text = current_lines[from_line]
    bottom_text = current_lines[to_line]

    if from_line == to_line:
        from_col, to_col = sorted((from_col, to_col))
        new_text = top_text[:from_col] + top_text[to_col:]
        #print(new_text)
        current_lines[current_line] = new_text
        #print(current_lines)
    else:
        new_text = top_text[:from_col] + bottom_text[to_col:]
        current_lines[current_line] = new_text

        current_lines = current_lines[:from_line+1] + current_lines[to_line+1:]

    select_range(from_line, from_col, from_line, from_col)


def insert_text(dst_line, dst_col, new_text):
    global current_line
    global current_col
    global selection_line
    global selection_col
    global current_lines

    #print('\n\n\n\ninsert_text')

    if new_text == '':
        print('new text is empty')
        return

    new_text_lines = new_text.split('\n')
    #print(f'insert text {new_lines=}')
    #print(f'{current_lines=}')

    line = current_lines[current_line]
    lhs = line[:current_col]
    rhs = line[current_col:]
    #print(f'{lhs=} {rhs=}')

    if len(new_text_lines) == 1:
        #old_line = current_lines[current_line]

        new_line = lhs + new_text + rhs
        #print(new_line)

        current_lines[current_line] = new_line
        current_col = len(lhs) + len(new_text)
        selection_line = current_line
        selection_col  = current_col
        return

    lines_before = current_lines[:current_line]
    lines_after = current_lines[current_line+1:]

    a, *b, c = new_text_lines

    #print(lines_before)
    #print(f'{lhs + a=}')
    #print(b)
    #print(f'{c + rhs=}')
    #print(lines_after)

    current_lines = lines_before + [lhs + a,] + b + [c + rhs,] + lines_after
    current_line = len(current_lines) - len(lines_after) - 1
    current_col  = len(c)
    selection_line = current_line
    selection_col  = current_col


def selection_text():
    from_line, from_col, to_line, to_col = current_line, current_col, selection_line, selection_col
    #from_line, from_col, to_line, to_col = 0,4, 1,5

    if to_line < from_line:
        from_line, from_col, to_line, to_col = to_line, to_col, from_line, from_col

    #print(current_lines)
    range_lines = current_lines[from_line:to_line+1]
    #print(range_lines)

    top_text    = range_lines[0]
    bottom_text = range_lines[-1]

    if from_line == to_line:
        #print(top_text)
        top_text = top_text[from_col:to_col]
        #print(top_text)
        range_lines[0] = top_text
    else:
        #print(top_text)
        top_text = top_text[from_col:]
        #print(top_text)
        range_lines[0] = top_text

        #print(bottom_text)
        bottom_text = bottom_text[:to_col]
        #print(bottom_text)
        range_lines[-1] = bottom_text

    text = '\n'.join(range_lines)

    return text


def on_key_press(event):
    global current_line
    global current_col
    #print(f'{event=} {current_line=} {current_col=}')

    if event.state == 0:
        pass
    elif event.state & SHIFT_MASK:
        pass
    elif event.state & MOVEMENT_MASK:
        pass
    else:
        #print(f'breaking on {event.state=:02x} unbound state {event=}')
        return 'break'


    char = event.char
    keysym = event.keysym


    if char == '':
        reset_cursor_flash()
        return

    if selection_ids:
        delete_range(
                current_line, current_col,
                selection_line, selection_col)

    insert_text(current_line, current_col, char)

    render_text()
    update_text_cursor()

    reset_cursor_flash()


def render_text():
    text = '\n'.join(current_lines)
    #print(repr(text))
    canvas.itemconfig(current_cell, text=text)


def on_return(event):
    global current_line
    global current_col

    current_lines.insert(current_line+1, '')
    current_line += 1
    current_col = 0

    text = '\n'.join(current_lines)
    canvas.itemconfig(current_cell, text=text)
    update_text_cursor()
    reset_cursor_flash()


def expand_left(n, unit):
    global current_line
    global current_col

    assert unit == 'char'

    current_col -= n
    while current_col < 0:
        if current_line == 0:
            break

        current_line -= 1
        current_col += 1

        line = current_lines[current_line]
        current_col += len(line)


def on_backspace(event):
    if has_selection():
        #print('has_selection')
        delete_selection()
    else:
        #print((current_line, current_col))
        expand_left(1, 'char')
        delete_selection()

    render_text()
    update_text_cursor()
    reset_cursor_flash()


def has_selection():
    #print(f'{current_line=}, {selection_line=}')
    #print(f'{current_col=}, {selection_col=}')
    r = current_line != selection_line or current_col != selection_col
    return r


def on_arrows(event):
    global current_line
    global current_col

    if has_selection():
        match event.keysym:
            case 'Left' | 'Up':
                pass
            case 'Right' | 'Down':
                current_line = selection_line
                current_col = selection_col
            case other:
                assert False

    else:
        match event.keysym:
            case 'Up':
                current_line = max(0, current_line - 1)
            case 'Down':
                current_line = min(len(current_lines)-1, current_line + 1)
            case 'Left':
                line = current_lines[current_line]
                if current_col > len(line):
                    current_col = len(line)
                current_col = max(0, current_col - 1)
            case 'Right':
                line = current_lines[current_line]
                current_col = min(len(line), current_col + 1)
            case other:
                assert False

    #text = '\n'.join(current_lines)
    #canvas.itemconfig(current_cell, text=text)
    update_text_cursor()
    reset_cursor_flash()


current_lines = ['']
current_line = 0
current_col  = 0

selection_ids = []
selection_line = 0
selection_col  = 0


cursor_colour = 'white'
cursor_width = 1
cursor_height = font_metrics["ascent"] + 2
linespace = font_metrics['linespace']

cursor_id = None

def update_text_cursor():
    line = current_lines[current_line]

    line_subset = line[:current_col]

    padding = int(max(2, 2 * zoom_scales[zoom_level]))
    padding = 0
    x_offset = cell_font_spec.measure(line_subset) + padding
    font_metrics = cell_font_spec.metrics()
    #print(font_metrics)
    linespace = font_metrics['linespace']
    y_offset = linespace * current_line
    cell_x, cell_y, *_= canvas.coords(current_cell)

    y = cell_y + y_offset
    x = cell_x + x_offset

    set_cursor_xy(x, y)

    #canvas.tag_raise(cursor_id)
    canvas.tag_lower(cursor_id)


def create_cursor(x, y):
    global cursor_id
    cursor_id = canvas.create_rectangle(
            x-(cursor_width//2),
            y,
            x+(cursor_width//2),
            y+linespace,
            fill=cursor_colour,
            outline='',
            tags='cursor')




def cancel_selection():
    global selection_ids
    for rect_id in selection_ids:
        canvas.delete(rect_id)
    selection_ids = []


def update_selection():
    #print('update selection')
    if current_line == selection_line and current_col == selection_col:
        cancel_selection()
        return

    if current_line < selection_line:
        from_line, from_col = current_line, current_col
        to_line, to_col = selection_line, selection_col
    else:
        from_line, from_col = selection_line, selection_col
        to_line, to_col = current_line, current_col

    x1, y1 = line_col_to_xy(from_line, from_col)
    x2, y2 = line_col_to_xy(to_line, to_col)
    font_metrics = cell_font_spec.metrics()
    linespace = font_metrics['linespace']

    selection_lines = list(range(from_line, to_line+1))
    #print(selection_lines)

    match len(selection_lines):
        case 0:
            head = None
        case 1:
            head = selection_lines[0]
            body = None
            tail = None
        case 2:
            head, tail = selection_lines
            body = None
        case other:
            head, *body, tail = selection_lines

    #print((head, body, tail))

    if head is None:
        return

    y2 += linespace
    x, y = canvas.coords(current_cell)

    new_rects = []
    if from_line == to_line:
        new_rects.append((
                      x+x1, y+y1,
                      x+x2, y+y1+linespace))
    else:
        _,_,line_width,_ = line_to_rect(head)
        new_rects.append((
                      x+x1, y+y1,
                      x+line_width, y+y1+linespace))

    if tail is not None:
        _,_,line_width,_ = line_to_rect(tail)
        new_rects.append((
                      x, y+y2-linespace,
                      x+x2, y+y2))

    if body is not None:
        for line_index in body:
            x3, y3, x4, y4 = line_to_rect(line_index)
            new_rects.append((
                x+x3, y+y3,
                x+x4, y+y4))

    update_selection_rects(new_rects)
    #print(repr(selection_text()))
    #print(selection_text())


def update_selection_rects(new_rects):
    global selection_ids
    num_rects = len(new_rects)
    num_old   = len(selection_ids)
    diff = num_rects - num_old
    if num_rects == num_old:
        pass
    elif diff > 0:
        for i in range(diff):
            new_id = canvas.create_rectangle(
                    0, 0,
                    0, 0,
                    #fill=cursor_colour,
                    fill=cursor_colour,
                    outline='',
                    tags='selection',
                    state='hidden')

            selection_ids.append(new_id)
        pass
    else:
        old_ids = selection_ids[diff:]
        selection_ids = selection_ids[:num_rects]
        for rect_id in old_ids:
            canvas.delete(rect_id)

    for ix, rect_id in enumerate(selection_ids):
        #print(ix, rect_id)
        canvas.coords(rect_id, *new_rects[ix])
        canvas.itemconfig(rect_id, state='normal')
        canvas.tag_lower(rect_id)


def set_cursor_xy(x=0, y=0):
    #print('set_cursor_xy')
    cancel_selection()

    old_x, old_y, *_ = canvas.coords(cursor_id)
    delta_x = x - old_x
    delta_y = y - old_y
    canvas.move(cursor_id, delta_x, delta_y)


flash_task_id = None
def flash_cursor():
    global flash_task_id
    state = canvas.itemcget(cursor_id, 'state')
    new_state = "normal" if state == 'hidden' else "hidden"
    canvas.itemconfig(cursor_id, state=new_state)
    flash_task_id = canvas.after(1000, flash_cursor)


def reset_cursor_flash():
    global flash_task_id
    canvas.after_cancel(flash_task_id)
    canvas.itemconfig(cursor_id, state='normal')
    flash_task_id = canvas.after(1000, flash_cursor)


def click_cell(event, cell_id):
    global current_cell
    global current_lines
    global current_line
    global current_col

    #print(f'click_cell {event=} {cell_id=}')

    #print(f'{cell_id=}')
    if cell_id == current_cell:
        pass
        #return

    canvas.itemconfig(current_cell, fill=unselected_cell_colour)

    current_cell = cell_id
    canvas.itemconfig(current_cell, fill=selected_cell_colour)

    text = canvas.itemcget(current_cell, 'text')
    current_lines = text.split('\n')

    current_line, current_col = xy_to_line_col(event.x, event.y)

    update_text_cursor()
    reset_cursor_flash()


def xy_to_line_col(event_x, event_y, align_cursor=True):
    line_number = 0
    col_number  = 0

    item_x, item_y = canvas.coords(current_cell)

    delta_x = canvas.canvasx(event_x) - item_x
    delta_y = canvas.canvasy(event_y) - item_y

    font_metrics = cell_font_spec.metrics()
    linespace = font_metrics['linespace']
    line_number = min(len(current_lines)-1, max(0, int(delta_y / linespace)))
    line = current_lines[line_number]

    prev_x = 0
    for i in range(1, len(line)+1):
        line_subset = line[:i]
        #print(f'{i} {line[:i]}')

        x_offset = cell_font_spec.measure(line_subset)
        width = x_offset - prev_x
        prev_x = x_offset

        if align_cursor:
            x_offset -= (width // 2)
        #print(f'{delta_x=:.0f} {x_offset=} {width=}')

        if x_offset > delta_x:
            col_number = i - 1
            break
    else:
        col_number = len(line)

    return line_number, col_number


def line_col_to_xy(line_number, col_number):
    font_metrics = cell_font_spec.metrics()
    linespace = font_metrics['linespace']
    y = line_number * linespace
    line = current_lines[line_number]
    line_subset = line[:col_number]
    x = cell_font_spec.measure(line_subset)
    return x, y


def line_to_rect(line_number):
    font_metrics = cell_font_spec.metrics()
    linespace = font_metrics['linespace']
    line = current_lines[line_number]
    width = cell_font_spec.measure(line)
    y1 = line_number * linespace
    y2 = y1 + linespace
    return 0, y1, width, y2


def click_near_cell(event):
    #print(f'near {event=}')
    ignore_list = set(canvas.find_withtag("cursor"))
    ignore_list |= set(canvas.find_withtag("selection"))
    #print(f'{ignore_list=}')
    current = set(canvas.find_withtag("current")) - ignore_list
    #print(f'{current=}')
    if current:
        #print('over item')
        return

    nearest_items = set(canvas.find_closest(event.x, event.y)) - ignore_list
    #print(f'{nearest_item=}')

    if not nearest_items:
        return

    nearest_item = next(iter(nearest_items))
    #print(( nearest_item, canvas.type(nearest_item), canvas.itemconfig(nearest_item, 'tags'),))
    click_cell(event, cell_id=nearest_item)


def select_word_at_mouse_cursor(event):
    global current_col
    global selection_line
    global selection_col

    #print('\n\n\n\n\n\n\nselect word')

    break_chars = ' (),.'
    _, current_col = xy_to_line_col(event.x, event.y, align_cursor=False)

    #print(f'{current_line=}, {current_col=}')


    line = current_lines[current_line]
    #print(f'{line=}')

    current_col = min(current_col, len(line)-1)
    c = line[current_col]
    #print(line)
    #print(current_col * ' ' + c)

    if c in break_chars:
        return


    lhs = line[:current_col]
    rhs = line[current_col:]
    #print(f'{lhs=}')
    #print(f'{rhs=}')

    lhs_offset = current_col
    rhs_offset = current_col
    #print(f'{lhs_offset=}')
    #print(f'{rhs_offset=}')

    #print('left')
    for i in range(lhs_offset-1, -1, -1):
        #print(i)
        #print((i, line[i]))
        if line[i] in break_chars:
            break
        lhs_offset = i

    #print('right')
    for i in range(rhs_offset, len(line)):
        #print((i, line[i]))
        if line[i] in break_chars:
            break
        rhs_offset = i


    #print(f'{current_col=}')
    #print(f'{lhs_offset=}')
    #print(f'{rhs_offset=}')

    selection_line = current_line
    selection_col = rhs_offset + 1
    current_col = lhs_offset

    #print(line[current_col:selection_col])
    #print(f'{current_line=}, {current_col=}')
    #print(f'{selection_line=}, {selection_col=}')

    update_text_cursor()
    reset_cursor_flash()

    update_selection()

    return


def create_cell(x, y):
    global current_cell
    global current_lines
    global current_line
    global current_col

    y -= font_metrics['ascent'] // 2

    set_cursor_xy(x, y)

    canvas.itemconfig(current_cell, fill=unselected_cell_colour)

    current_cell = canvas.create_text(
            x, y,
            text='',
            font=cell_font_spec,
            fill=colours['Cyan'],
            anchor='nw')

    current_lines = ['']
    select_range(0, 0, 0, 0)

    canvas.tag_bind(current_cell, '<Button-1>', partial(click_cell, cell_id=current_cell))


def create_cell_here(event):
    x = canvas.canvasx(event.x)
    y = canvas.canvasy(event.y)
    create_cell(x, y)


def on_button1_motion(event):
    global selection_line
    global selection_col
    selection_line, selection_col = xy_to_line_col(event.x, event.y)
    update_selection()
    reset_cursor_flash()


def select_all(event):
    global current_line, current_col
    global selection_line, selection_col
    current_line, current_col = 0, 0
    selection_line = len(current_lines) - 1
    last_line = current_lines[-1]
    selection_col = len(last_line)
    update_selection()


def delete_selection():
    #print('delete_selection')
    delete_range(
            current_line, current_col,
            selection_line, selection_col)


def cut_selection(event):
    #print('cut')
    copy_selection()
    delete_selection()

    render_text()
    update_text_cursor()

    reset_cursor_flash()


def copy_selection(event=None):
    #print('copy')
    new_text = selection_text()
    root.clipboard_clear()
    root.clipboard_append(new_text)


def paste_from_clipboard(event):
    #print('paste')
    new_text = root.clipboard_get()
    #print(f'{new_text=}')

    delete_selection()

    insert_text(current_line, current_col, new_text)

    render_text()
    update_text_cursor()

    reset_cursor_flash()


create_cursor(100, 50)
flash_cursor()
create_cell(100, 50)

root.bind('<KeyPress-F1>', toggle_toolbox)

canvas.bind('<MouseWheel>', on_windows_zoom)

canvas.bind('<Button-1>', click_near_cell)
canvas.bind('<Double-Button-1>', select_word_at_mouse_cursor)
#canvas.bind('<Double-Button-1>', create_cell_here)
canvas.bind('<B1-Motion>', on_button1_motion)

root.bind('<KeyPress>', on_key_press)

root.bind('<Return>', on_return)

root.bind('<BackSpace>', on_backspace)
root.bind('<Delete>', lambda e: print('delete'))

root.bind('<Up>',    on_arrows)
root.bind('<Down>',  on_arrows)
root.bind('<Left>',  on_arrows)
root.bind('<Right>', on_arrows)

root.bind('<Escape>', lambda e: print('centre'))

root.bind('<Control-a>', select_all)
root.bind('<Mod1-a>',    select_all)
root.bind('<Control-x>', cut_selection)
root.bind('<Control-c>', copy_selection)
root.bind('<Control-v>', paste_from_clipboard)

root.bind('<Control-z>', lambda e: print('undo'))
root.bind('<Control-y>', lambda e: print('redo'))


def type_example_text():
    text = """one two three four five
six seven eight nine
ten"""
    for char in text:
        #print(repr(char))
        match char:
            case ' ':
                cmd = '<KeyPress-space>'
            case '\n':
                cmd = '<KeyPress-Return>'
            case other:
                cmd = f'<KeyPress-{char}>'
        canvas.event_generate(cmd)

root.after(100, type_example_text)
#root.wm_state('zoomed')
root.mainloop()

