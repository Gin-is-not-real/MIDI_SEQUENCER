import wx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
import time

import set_interval as intval

# TODO: real time: 
    # 
# TODO: controls:
    # volume
    # bmp / vitesse
    # set nb steps
    # update tone list
    # time signature ??
# TODO:
    # mettre en evidence la division temporelle
    # mettre en evidence les noires
    # mettre en evidence les gammes


DEFAULT_TONE_LIST = ['do3', 'do#3', 're3', 're#3', 'mi3', 'fa3', 'fa#3', 'sol3', 'sol#3', 'la3', 'la#3', 'si3', 'do4', 'do#4', 're4', 're#4', 'mi4', 'fa4', 'fa#4', 'sol4', 'sol#4', 'la4', 'la#4', 'si4', 'do5', 'do#5', 're5', 're#5', 'mi5', 'fa5', 'fa#5', 'sol5', 'sol#5', 'la5', 'la#5', 'si5', 'do6', 'do#6', 're6', 're#6', 'mi6', 'fa6', 'fa#6', 'sol6', 'sol#6', 'la6', 'la#6', 'si6', 'do7']

DEFAULT_TONE_LIST = ['do3', 'do#3', 're3', 're#3', 'mi3', 'fa3', 'fa#3', 'sol3', 'sol#3', 'la3', 'la#3', 'si3', 'do4']

DEFAULT_NB_STEPS = 16


class MDS_Player():
    """Manage midi outports: get and open outputs, play and stop reading, send messages.."""
    TONE_NAMES_FR = ('do', 'do#', 're', 're#', 'mi', 'fa', 'fa#', 'sol', 'sol#', 'la', 'la#', 'si')


    def play_messages(self, steps):
        """Loop on nb_steps and send out messages from array as a parameter"""
        playback_time = 0.2
        self.out = mido.open_output(MDS_Player.get_outport())

        # the current step played
        self.playing_index = 0

        # action for SetInterval loop callback
        def action():
            # send out on and off messages, step by step
            for msg in steps[self.playing_index]:
                self.out.send(msg)
    
            # sleep before the next step
            time.sleep(playback_time)
            self.playing_index += 1

            # restart loop
            if self.playing_index == len(steps) -1:
                self.playing_index = 0

        # run the intval loop
        self.intval = intval.SetInterval(playback_time, action)


    def stop(self):
        """Stop the interval and close the outport"""
        self.intval.cancel()
        self.out.close()


    @classmethod
    def get_outport(cls, index=0):
        """Return the output specified by the index parameter, or the first available"""
        try:
            return mido.get_output_names()[index]
        
        except IndexError: 
            return mido.get_output_names()[0]

    @classmethod
    def get_last_outport(cls):
        """Return the last available output"""
        return mido.get_output_names()[-1]

    @classmethod
    def get_midi_note(cls, tone_name, octave):
        """Return the midi note associate for a tone and octave"""
        id = cls.TONE_NAMES_FR.index(tone_name)
        return id + ((octave +1) *12)
    

class MDS_Step():
    """Object containing mixed data about a step, between this representation and this interpretation; positions on canvas, note data..."""

    def __init__(self, x, y, width, label, art):
        self.x = x 
        self.y = y
        self.width = width
        self.label = label
        self.art = art
        self.note = self.get_midi_note()

    def get_end(self):
        """Return the last x coord occupied by the step"""
        return (self.x + self.width) -1
    
    def get_midi_note(self):
        """Split and convert a label type nameoctave (ex: do4) and return the midi note associate to the tone name and octave"""
        octave = self.label[-1]
        name = self.label.replace(octave, '')
        return MDS_Player.get_midi_note(name, int(octave))


class MDS_Frame(wx.Frame):
    """Frame representing a midi step sequencer"""

    def __init__(self, nb_steps=DEFAULT_NB_STEPS, tone_list=DEFAULT_TONE_LIST, *args, **kw):
        super().__init__(*args, **kw)
        self.nb_steps = nb_steps
        self.tone_list = tone_list

        # contient les objets Step, représentant les objets (bar) sur le graphique
        self.steps = []

        self.create_GUI()

#######################################################
# GUI

    def create_GUI(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        # title 
        title = wx.StaticText(panel, label="Sequencer")
        font = title.GetFont()
        font.PointSize += 8
        font = font.Bold()
        title.SetFont(font)
        sizer.Add(title, wx.SizerFlags().Center())

        # inputs
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.inp_play = wx.ToggleButton(panel, -1, "play")
        self.inp_play.Bind(wx.EVT_TOGGLEBUTTON, self.handle_play)
        ctrl_sizer.Add(self.inp_play, wx.SizerFlags().Center())

        sizer.Add(ctrl_sizer, wx.SizerFlags().Center())

        # canvas
        self.create_canvas(panel)
        sizer.Add(self.canvas, -1, wx.CENTER)


    def create_canvas(self, parent):
        """Create figure, canvas, plots, and connect events callbacks for mouse events"""
        self.figure = Figure()
        self.canvas = FigureCanvas(parent, -1, self.figure)

        self.canvas.callbacks.connect('button_press_event', self.mouse_down)
        self.canvas.callbacks.connect('motion_notify_event', self.mouse_motion)
        self.canvas.callbacks.connect('button_release_event', self.mouse_up)

        self.state = ''

        self.create_plots()

    
    def create_plots(self):
        """Create sequencer plots from self nb_steps and tone_list properties"""

        plt.style.use('_mpl-gallery')

        self.subplot = self.figure.subplots()
        color = (1., 0., 0.)

        self.subplot.plot(1, 1, color=color)

        self.subplot.set_ylabel('Notes', fontsize=8)
        self.subplot.set_xlabel('Steps', fontsize=8)

        self.subplot.set(
            xlim=(0, self.nb_steps), 
            xticks=np.arange(0, self.nb_steps), 
            ylim=(0, len(self.tone_list))
            )
        
        self.subplot.set_yticks(np.arange(len(self.tone_list)))
        self.subplot.set_yticklabels(self.tone_list)
        self.subplot.invert_yaxis()

        plt.setp(self.subplot.get_ymajorticklabels(), va="top")
        plt.setp(self.subplot.get_xmajorticklabels(), ha="left")


#######################################################
# STEPS

    def get_step(self, x, y):
        """Get a step from self.steps list by x and y positions on canvas"""
        # step = [step for (i, step) in enumerate(self.steps) if step.y == y and (step.x <= x and x <= step.end)]

        for step in self.steps:
            if step.y == y:

                if step.x <= x and x <= step.get_end():
                    return step

        return False
    

    def add_step(self, x, y, width, label):
        """Create and add a midiplot bar on canvas, and add it's MDS representation on self.steps list"""
        bar_h = 1
        bar_y = bar_h/2 if y == 0 else ((y * bar_h) + (bar_h/2))
        bar = self.subplot.barh(bar_y, width, left=x, color='red', edgecolor='black')

        self.steps.append(MDS_Step(x, y, width, label, art=bar))
        self.canvas.draw()


    def update_step(self, step, x):
        """Update the step width and plot associate with new end x position"""
        width = int(x) - step.x +1
        
        if width == 0: 
            width = 1

        step.width = width 
        step.art.get_children()[0].set_width(width)
        # les attributs de step sont updatés dans le release de la souris pour gerer les cas où width serait négatif

        self.canvas.draw()


    def remove_step(self, x, y):
        """Remove a step from steps list and canvas"""
        step = self.get_step(x, y)

        step.art.remove()
        self.steps.remove(step)

        self.canvas.draw()


#######################################################
# MOUSE EVENTS

    def mouse_down(self, event):
        """Add or remove a step from canvas"""
        if event.inaxes:
            x, y = int(event.xdata), int(event.ydata)

            if not self.get_step(x, y):
                self.add_step(x, y, 1, self.subplot.get_yticklabels()[y].get_text())
                self.state = self.get_step(x, y)

            else:
                self.state = self.get_step(x, y)
                self.remove_step(x, y)

        else:
            self.state = ''
        
        # print('new state:', self.state)


    def mouse_motion(self, event):
        """Stretch a bar and update the step associate"""
        if self.state  == '' or self.state  == None or self.state == 'running':
            return
        if not event.inaxes:
            return
        
        step = self.state 
        x = event.xdata

        if x is None or x == step.get_end():
            return

        # width = int(x) - step.x +1
        self.update_step(step, x)


    def mouse_up(self, event):
        """Final update for steps attributes width and x after stretch"""
        if self.state != '':
            if self.state.width < 0:
                self.state.width = int(str(self.state.width).replace('-', ''))
                self.state.x = self.state.x - self.state.width
        self.state = '' 


#######################################################
# PLAYING EVENTS

    def handle_play(self, event):
        """play or stop the player"""

        if self.inp_play.GetLabel() == 'play':
            self.inp_play.SetLabel('stop')

            self.player.play_messages(self.format_messages())

        else:
            self.inp_play.SetLabel('play')
            self.player.stop()

    def format_messages(self):
        """Convert steps to mido Messages, and return messages list"""

        messages = []

        for i in range(0, self.nb_steps):
            line = []

            starts = [step for(index, step) in enumerate(self.steps) if step.x == i]
            stops = [step for(index, step) in enumerate(self.steps) if step.get_end()+1 == i]

            for step in starts:
                line.append(mido.Message('note_on', note=step.note, velocity=65))

            for step in stops:
                line.append(mido.Message('note_off', note=step.note))

            messages.append(line)

        return messages
    

#######################################################
# APP AND MAIN

class App(wx.App):
    def OnInit(self):
        self.frame = MDS_Frame(parent=None, title='Sequencer', size=(640, 640))
        self.frame.player = MDS_Player()
        self.frame.Show()
        return True 
    

if __name__ == "__main__":
    app = App()
    app.MainLoop()