import mdl
from display import *
from matrix import *
from draw import *

"""======== first_pass( commands ) ==========

  Checks the commands array for any animation commands
  (frames, basename, vary)

  Should set num_frames and basename if the frames
  or basename commands are present

  If vary is found, but frames is not, the entire
  program should exit.

  If frames is found, but basename is not, set name
  to some default value, and print out a message
  with the name being used.
  ==================== """
def first_pass( commands ):

    name = ''
    num_frames = 1
    vary_used = False

    for command in commands:
        if command['op'] == 'basename':
            name = command['args'][0]

        elif command['op'] == 'frames':
            num_frames = int(command['args'][0])

        elif command['op'] == 'vary':
            vary_used = True

    if vary_used and num_frames == 1:
        print("No number of frames given.")
        quit()

    if name == '':
        name = 'anim'
        print("Basename not provided. Default value is anim")

    return (name, num_frames)

"""======== second_pass( commands ) ==========

  In order to set the knobs for animation, we need to keep
  a seaprate value for each knob for each frame. We can do
  this by using an array of dictionaries. Each array index
  will correspond to a frame (eg. knobs[0] would be the first
  frame, knobs[2] would be the 3rd frame and so on).

  Each index should contain a dictionary of knob values, each
  key will be a knob name, and each value will be the knob's
  value for that frame.

  Go through the command array, and when you find vary, go
  from knobs[0] to knobs[frames-1] and add (or modify) the
  dictionary corresponding to the given knob with the
  appropirate value.
  ===================="""
def second_pass( commands, num_frames ):
    frames = [ {} for i in range(num_frames) ]

    for command in commands:
        if command['op'] == 'vary':
            args = command['args']
            sframe = int(args[0])
            eframe = int(args[1])

            knob = command['knob']
            sknob = float(args[2])
            eknob = float(args[3])

            dknob = (eknob - sknob) / (eframe - sframe)

            for frame in range(sframe, eframe):
                frames[frame][knob] = sknob
                sknob += dknob


    return frames


def run(filename):
    """
    This function runs an mdl script
    """
    p = mdl.parseFile(filename)

    if p:
        (commands, symbols) = p
    else:
        print("Parsing failed.")
        return

    view = [0,
            0,
            1];
    ambient = [50,
               50,
               50]
    light = [[0.5,
              0.75,
              1],
             [255,
              255,
              255]]

    color = [0, 0, 0]
    symbols['.white'] = ['constants',
                         {'red': [0.2, 0.5, 0.5],
                          'green': [0.2, 0.5, 0.5],
                          'blue': [0.2, 0.5, 0.5]}]
    reflect = '.white'

    (name, num_frames) = first_pass(commands)
    frames = second_pass(commands, num_frames)


    tmp = new_matrix()
    ident( tmp )

    stack = [ [x[:] for x in tmp] ]
    screen = new_screen()
    zbuffer = new_zbuffer()
    tmp = []
    step_3d = 100
    consts = ''
    coords = []
    coords1 = []

    cur_frame = 0

    for frame in frames:
        print("Generating frame: ", cur_frame)
        for command in commands:
            # print(command)
            c = command['op']
            args = command['args']
            knob_value = 1

            for k in frame.keys():
                symbols[k] = frame[k]
            if c == 'box':
                if command['constants']:
                    reflect = command['constants']
                add_box(tmp,
                        args[0], args[1], args[2],
                        args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'sphere':
                if command['constants']:
                    reflect = command['constants']
                add_sphere(tmp,
                           args[0], args[1], args[2], args[3], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'torus':
                if command['constants']:
                    reflect = command['constants']
                add_torus(tmp,
                          args[0], args[1], args[2], args[3], args[4], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'line':
                add_edge(tmp,
                         args[0], args[1], args[2], args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_lines(tmp, screen, zbuffer, color)
                tmp = []
            elif c == 'move':
                knob = command['knob']

                if knob:
                    tmp = make_translate(args[0]*symbols[knob], args[1]*symbols[knob], args[2]*symbols[knob])
                else:
                    tmp = make_translate(args[0], args[1], args[2])

                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'scale':
                knob = command['knob']

                if knob:
                    tmp = make_scale(args[0]*symbols[knob], args[1]*symbols[knob], args[2]*symbols[knob])
                else:
                    tmp = make_scale(args[0], args[1], args[2])
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'rotate':
                knob = command['knob']

                if knob:
                    theta = args[1] * symbols[knob] * (math.pi/180)
                else:
                    theta = args[1]* (math.pi/180)

                if args[0] == 'x':
                    tmp = make_rotX(theta)
                elif args[0] == 'y':
                    tmp = make_rotY(theta)
                else:
                    tmp = make_rotZ(theta)
                matrix_mult( stack[-1], tmp )
                stack[-1] = [ x[:] for x in tmp]
                tmp = []

            elif c == 'push':
                stack.append([x[:] for x in stack[-1]] )
            elif c == 'pop':
                stack.pop()
            elif c == 'display':
                display(screen)
            elif c == 'save':
                save_extension(screen, args[0] + ".png")

        if (num_frames != 1 and name != 'default_gif'):
            places = len(str(num_frames)) - len(str(cur_frame))

            number = "0" * places + str(cur_frame)
            file_name = "./anim/" + name + number
            print(file_name)
            save_extension(screen, file_name)
            tmp = new_matrix()
            ident(tmp)
            stack = [ [x[:] for x in tmp] ]
            screen = new_screen()
            zbuffer = new_zbuffer()
            cur_frame += 1

    if (num_frames != 1 and name != 'default_gif'):
        make_animation(name)
